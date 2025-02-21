import sys
import os
import re
import librosa
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QTableWidget,
    QTableWidgetItem, QMessageBox, QHeaderView, QSlider
)
from PyQt5.QtCore import Qt, QTimer, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
import qtawesome as qta  # Importar QtAwesome

def segundos_a_timestamp(segundos):
    total_ms = int(segundos * 1000)
    horas, rem = divmod(total_ms, 3600000)
    minutos, rem = divmod(rem, 60000)
    segundos, milisegundos = divmod(rem, 1000)
    return f"{horas:02d}:{minutos:02d}:{segundos:02d},{milisegundos:03d}"

class AudioSync(QWidget):
    def __init__(self):
        super().__init__()
        self.playing = False
        self.media_file = None
        self.duration = 0
        self.media_player = QMediaPlayer()
        
        # Timer para actualización precisa
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self.update_position)
        self.position_timer.setInterval(50)  # 50ms para alta precisión
        
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Media controls
        media_layout = QHBoxLayout()

        # Botón "Cargar Audio" con ícono y atajo
        self.load_media_button = QPushButton("Ctrl+O")
        self.load_media_button.setIcon(qta.icon('fa5s.folder-open', color='black'))
        self.load_media_button.clicked.connect(self.load_media)
        self.load_media_button.setShortcut("Ctrl+O")
        media_layout.addWidget(self.load_media_button)

        # Botón "Reproducir/Pausar" con ícono dinámico y atajo
        self.play_button = QPushButton("Espacio")
        self.play_button.setIcon(qta.icon('fa5s.play', color='black'))
        self.play_button.clicked.connect(self.toggle_playback)
        self.play_button.setShortcut(Qt.Key_Space)
        media_layout.addWidget(self.play_button)

        # Botón "Cargar Letras" con ícono y atajo
        self.load_lyrics_button = QPushButton("Ctrl+L")
        self.load_lyrics_button.setIcon(qta.icon('fa5s.file-alt', color='black'))
        self.load_lyrics_button.clicked.connect(self.load_lyrics)
        self.load_lyrics_button.setShortcut("Ctrl+L")
        media_layout.addWidget(self.load_lyrics_button)

        # Botón "Marcar Tiempo" con ícono y atajo
        self.mark_time_button = QPushButton("M")
        self.mark_time_button.setIcon(qta.icon('fa5s.clock', color='black'))
        self.mark_time_button.clicked.connect(self.mark_current_time)
        self.mark_time_button.setShortcut(Qt.Key_M)
        media_layout.addWidget(self.mark_time_button)

        # Botón "-0.1s" con ícono y atajo
        self.adjust_minus = QPushButton("←")
        self.adjust_minus.setIcon(qta.icon('fa5s.backward', color='black'))
        self.adjust_minus.clicked.connect(lambda: self.adjust_time(-0.1))
        self.adjust_minus.setShortcut(Qt.Key_Left)
        media_layout.addWidget(self.adjust_minus)

        # Botón "+0.1s" con ícono y atajo
        self.adjust_plus = QPushButton("→")
        self.adjust_plus.setIcon(qta.icon('fa5s.forward', color='black'))
        self.adjust_plus.clicked.connect(lambda: self.adjust_time(0.1))
        self.adjust_plus.setShortcut(Qt.Key_Right)
        media_layout.addWidget(self.adjust_plus)

        layout.addLayout(media_layout)

        # Slider y tiempo
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.sliderMoved.connect(self.seek_position)
        self.time_slider.setTracking(True)
        self.time_label = QLabel("00:00:00.000 / 00:00:00.000")
        layout.addWidget(self.time_slider)
        layout.addWidget(self.time_label)

        # Vista previa
        self.preview_label = QLabel("Vista previa de la letra")
        self.preview_label.setStyleSheet("QLabel { background-color: black; color: white; padding: 10px; }")
        self.preview_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.preview_label)

        # Tabla para letras y tiempos
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Letra", "Tiempo (seg)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.DoubleClicked)
        layout.addWidget(self.table)

        # Botón "Generar SRT" con ícono y atajo
        self.generate_button = QPushButton("Ctrl+S")
        self.generate_button.setIcon(qta.icon('fa5s.save', color='black'))
        self.generate_button.clicked.connect(self.generate_srt)
        self.generate_button.setShortcut("Ctrl+S")
        layout.addWidget(self.generate_button)

        self.setLayout(layout)
        self.setWindowTitle("Sincronizador de Audio y Letras")
        self.setMinimumSize(600, 400)

    def load_media(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo de audio", "",
            "Audio Files (*.mp3 *.wav);;All Files (*)")
        if file_path:
            try:
                media_content = QMediaContent(QUrl.fromLocalFile(file_path))
                self.media_player.setMedia(media_content)
                self.media_file = file_path
                
                y, sr = librosa.load(file_path, sr=None)
                self.duration = librosa.get_duration(y=y, sr=sr)
                self.time_slider.setRange(0, int(self.duration * 1000))
                
                self.media_player.play()
                self.media_player.pause()
                self.position_timer.start()
                self.update_time_display(0)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al cargar el audio:\n{str(e)}")

    def load_lyrics(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo de letras", "",
            "Text Files (*.txt);;All Files (*)")
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    lyrics = file.read().strip().split("\n")
                self.populate_table_with_lyrics(lyrics)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al cargar las letras:\n{str(e)}")

    def populate_table_with_lyrics(self, lyrics):
        self.table.setRowCount(len(lyrics))
        total_duration = self.duration or 210
        interval = total_duration / (len(lyrics) + 1)
        
        if self.media_file:
            try:
                segments = self.analyze_silences(self.media_file)
                for i, (start, _) in enumerate(segments[:len(lyrics)]):
                    self.table.setItem(i, 0, QTableWidgetItem(lyrics[i]))
                    self.table.setItem(i, 1, QTableWidgetItem(f"{start:.3f}"))
                if len(lyrics) > len(segments):
                    last_time = segments[-1][1] if segments else 0
                    remaining = len(lyrics) - len(segments)
                    interval = (total_duration - last_time) / (remaining + 1)
                    for i in range(len(segments), len(lyrics)):
                        time = last_time + interval * (i - len(segments) + 1)
                        self.table.setItem(i, 0, QTableWidgetItem(lyrics[i]))
                        self.table.setItem(i, 1, QTableWidgetItem(f"{time:.3f}"))
                return
            except Exception as e:
                QMessageBox.warning(self, "Advertencia", f"No se pudo analizar silencios: {str(e)}. Usando intervalo uniforme.")

        for i, line in enumerate(lyrics):
            self.table.setItem(i, 0, QTableWidgetItem(line))
            self.table.setItem(i, 1, QTableWidgetItem(f"{interval * (i + 1):.3f}"))

    def analyze_silences(self, file_path):
        y, sr = librosa.load(file_path)
        silences = librosa.effects.split(y, top_db=20)
        return [(start / sr, end / sr) for start, end in silences]

    def toggle_playback(self):
        if not self.media_file:
            QMessageBox.warning(self, "Error", "Carga un archivo de audio primero")
            return
        if not self.playing:
            self.media_player.play()
            self.playing = True
            self.play_button.setText("Espacio")
            self.play_button.setIcon(qta.icon('fa5s.pause', color='black'))  # Cambiar ícono a pausa
            self.position_timer.start()
        else:
            self.media_player.pause()
            self.playing = False
            self.play_button.setText("Espacio")
            self.play_button.setIcon(qta.icon('fa5s.play', color='black'))  # Cambiar ícono a play
            self.position_timer.stop()

    def seek_position(self):
        if self.media_file:
            pos = self.time_slider.value()
            self.media_player.setPosition(pos)

    def update_position(self):
        if self.media_file and self.playing:
            position = self.media_player.position()
            self.time_slider.setValue(position)
            current_time = position / 1000.0
            self.update_time_display(current_time)
            self.update_preview(current_time)

    def update_time_display(self, current):
        cur_h, cur_m, cur_s, cur_ms = self._format_time(current)
        dur_h, dur_m, dur_s, dur_ms = self._format_time(self.duration)
        self.time_label.setText(
            f"{cur_h:02d}:{cur_m:02d}:{cur_s:02d}.{cur_ms:03d} / "
            f"{dur_h:02d}:{dur_m:02d}:{dur_s:02d}.{dur_ms:03d}"
        )

    def _format_time(self, seconds):
        total_ms = int(seconds * 1000)
        hours, rem = divmod(total_ms, 3600000)
        minutes, rem = divmod(rem, 60000)
        secs, ms = divmod(rem, 1000)
        return hours, minutes, secs, ms

    def update_preview(self, current_time):
        current_line = ""
        max_time = -1
        for row in range(self.table.rowCount()):
            try:
                time_item = self.table.item(row, 1)
                if time_item and (t := float(time_item.text())) > max_time and t <= current_time:
                    max_time = t
                    current_line = self.table.item(row, 0).text()
            except ValueError:
                pass
        self.preview_label.setText(current_line)

    def mark_current_time(self):
        if not self.media_file:
            QMessageBox.warning(self, "Error", "Carga un archivo de audio primero")
            return
        
        current_time = self.media_player.position() / 1000.0
        selected_row = self.table.currentRow()
        
        if selected_row >= 0:
            # Marcar el tiempo en la fila actual
            self.table.setItem(selected_row, 1, QTableWidgetItem(f"{current_time:.3f}"))
            
            # Moverse a la siguiente fila
            next_row = selected_row + 1
            if next_row < self.table.rowCount():
                self.table.setCurrentCell(next_row, 0)  # Seleccionar la siguiente fila
            else:
                QMessageBox.information(self, "Información", "Has llegado al final de la lista.")

    def adjust_time(self, adjustment):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            try:
                time_item = self.table.item(selected_row, 1)
                current_time = float(time_item.text())
                new_time = max(0, current_time + adjustment)
                self.table.setItem(selected_row, 1, QTableWidgetItem(f"{new_time:.3f}"))
            except ValueError:
                QMessageBox.warning(self, "Error", "Tiempo inválido en la línea seleccionada")

    def generate_srt(self):
        if not self.media_file:
            QMessageBox.warning(self, "Error", "Carga un archivo de audio primero")
            return
        timestamps = []
        for row in range(self.table.rowCount()):
            line_item = self.table.item(row, 0)
            time_item = self.table.item(row, 1)
            if not line_item or not time_item:
                continue
            line = line_item.text()
            try:
                time_in_seconds = float(time_item.text())
                if time_in_seconds < 0 or time_in_seconds > self.duration:
                    QMessageBox.warning(self, "Error", f"Tiempo inválido en la línea {row + 1}")
                    return
                timestamps.append((time_in_seconds, line))
            except ValueError:
                QMessageBox.warning(self, "Error", f"Tiempo inválido en la línea {row + 1}")
                return
        
        timestamps.sort()
        base_name = os.path.splitext(os.path.basename(self.media_file))[0]
        output_file, _ = QFileDialog.getSaveFileName(
            self, "Guardar archivo SRT", f"{base_name}.srt",
            "SubRip Subtitle (*.srt)")
        if output_file:
            with open(output_file, "w", encoding="utf-8") as file:
                for i, (start_time, line) in enumerate(timestamps, 1):
                    end_time = timestamps[i][0] - 0.001 if i < len(timestamps) else min(self.duration, start_time + 5.0)
                    file.write(f"{i}\n"
                             f"{segundos_a_timestamp(start_time)} --> {segundos_a_timestamp(end_time)}\n"
                             f"{line}\n\n")
            QMessageBox.information(self, "Éxito", f"Archivo SRT guardado como:\n{output_file}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AudioSync()
    window.show()
    sys.exit(app.exec_())