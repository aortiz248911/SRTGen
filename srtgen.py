import sys
import os
import re
import librosa
from pydub import AudioSegment
import soundfile as sf
import warnings
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QTableWidget,
    QTableWidgetItem, QMessageBox, QHeaderView, QSlider,
    QFontComboBox, QSpinBox, QColorDialog, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QColor, QFont, QIcon
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
import qtawesome as qta

# Suprimir advertencias específicas de librosa
warnings.filterwarnings("ignore", message="Could not update timestamps for skipped samples")

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
        self.temp_wav_file = None  # Para almacenar el archivo WAV temporal
        self.duration = 0
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        self.is_dark_theme = False
        self.subtitle_font = QFont("Arial", 12)
        self.subtitle_color = QColor("white")
        
        self.init_theme()
        
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self.update_position)
        self.position_timer.setInterval(50)
        
        self.initUI()

    def init_theme(self):
        self.light_style = """
            QWidget { background-color: #ffffff; color: #000000; }
            QPushButton { background-color: #f0f0f0; border: 1px solid #cccccc; padding: 5px; }
            QPushButton:hover { background-color: #e0e0e0; }
            QTableWidget { border: 1px solid #cccccc; }
            QTableWidget::item:selected {
                background-color: #4a90e2;  /* Fondo azul claro para selección en tema claro */
                color: #ffffff;  /* Texto blanco para contraste */
                border: 1px solid #4a90e2;
            }
            QHeaderView::section { background-color: #f0f0f0; }
            QSlider::handle:horizontal {
                background-color: #4a90e2;
                border: 1px solid #cccccc;
                width: 20px;
                height: 20px;
                border-radius: 10px;  /* Hacer el handle circular/esférico */
                margin: -2px 0;  /* Centrar verticalmente */
            }
            QSlider::groove:horizontal {
                background-color: #e0e0e0;
                height: 8px;
                border-radius: 4px;
            }
        """
        self.dark_style = """
            QWidget { background-color: #2b2b2b; color: #ffffff; }
            QPushButton { background-color: #3b3b3b; border: 1px solid #505050; padding: 5px; }
            QPushButton:hover { background-color: #454545; }
            QTableWidget { border: 1px solid #505050; }
            QTableWidget::item:selected {
                background-color: #4a90e2;  /* Fondo azul claro para selección en tema oscuro */
                color: #ffffff;  /* Texto blanco para contraste */
                border: 1px solid #4a90e2;
            }
            QHeaderView::section { background-color: #3b3b3b; }
            QSlider::handle:horizontal {
                background-color: #4a90e2;
                border: 1px solid #505050;
                width: 20px;
                height: 20px;
                border-radius: 10px;  /* Hacer el handle circular/esférico */
                margin: -2px 0;  /* Centrar verticalmente */
            }
            QSlider::groove:horizontal {
                background-color: #505050;
                height: 8px;
                border-radius: 4px;
            }
        """
        self.setStyleSheet(self.light_style)

    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        self.setStyleSheet(self.dark_style if self.is_dark_theme else self.light_style)
        icon_color = 'white' if self.is_dark_theme else 'black'
        self.theme_button.setIcon(qta.icon('fa5s.adjust', color=icon_color))
        self.load_media_button.setIcon(qta.icon('fa5s.folder-open', color=icon_color))
        self.play_button.setIcon(qta.icon('fa5s.play' if not self.playing else 'fa5s.pause', color=icon_color))
        self.load_lyrics_button.setIcon(qta.icon('fa5s.file-alt', color=icon_color))
        self.mark_time_button.setIcon(qta.icon('fa5s.clock', color=icon_color))
        self.generate_button.setIcon(qta.icon('fa5s.save', color=icon_color))
        self.update_preview_style()

    def initUI(self):
        layout = QVBoxLayout()
        media_layout = QHBoxLayout()

        # Botón del tema al lado izquierdo
        self.theme_button = QPushButton("T")
        self.theme_button.setIcon(qta.icon('fa5s.adjust', color='black'))
        self.theme_button.clicked.connect(self.toggle_theme)
        self.theme_button.setShortcut("Ctrl+T")
        media_layout.addWidget(self.theme_button)

        self.load_media_button = QPushButton("Ctrl+O")
        self.load_media_button.setIcon(qta.icon('fa5s.folder-open', color='black'))
        self.load_media_button.clicked.connect(self.load_media)
        self.load_media_button.setShortcut("Ctrl+O")
        media_layout.addWidget(self.load_media_button)

        self.play_button = QPushButton("Espacio")
        self.play_button.setIcon(qta.icon('fa5s.play', color='black'))
        self.play_button.clicked.connect(self.toggle_playback)
        self.play_button.setShortcut(Qt.Key_Space)
        media_layout.addWidget(self.play_button)

        self.load_lyrics_button = QPushButton("Ctrl+L")
        self.load_lyrics_button.setIcon(qta.icon('fa5s.file-alt', color='black'))
        self.load_lyrics_button.clicked.connect(self.load_lyrics)
        self.load_lyrics_button.setShortcut("Ctrl+L")
        media_layout.addWidget(self.load_lyrics_button)

        self.mark_time_button = QPushButton("M")
        self.mark_time_button.setIcon(qta.icon('fa5s.clock', color='black'))
        self.mark_time_button.clicked.connect(self.mark_current_time)
        self.mark_time_button.setShortcut(Qt.Key_M)
        media_layout.addWidget(self.mark_time_button)

        # Añadir control de volumen
        self.volume_label = QLabel("Volumen:")
        media_layout.addWidget(self.volume_label)
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)  # Volumen inicial al 50%
        self.volume_slider.valueChanged.connect(self.set_volume)
        media_layout.addWidget(self.volume_slider)

        layout.addLayout(media_layout)

        # Restaurar control deslizante de tiempo (más amplio y con handle esférico)
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setMinimumWidth(400)  # Establecer un ancho mínimo más amplio
        self.time_slider.sliderMoved.connect(self.seek_position)
        self.time_slider.setTracking(True)
        self.time_slider.valueChanged.connect(self.update_position)
        layout.addWidget(self.time_slider)

        # Añadir etiqueta de tiempo debajo del slider
        self.time_label = QLabel("00:00:00,000 / 00:00:00,000")
        layout.addWidget(self.time_label)

        # Controles de estilo de subtítulos
        style_layout = QHBoxLayout()
        style_frame = QFrame()
        style_frame.setFrameStyle(QFrame.Box | QFrame.Raised)
        style_frame.setLayout(style_layout)

        style_layout.addWidget(QLabel("Fuente:"))
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(self.subtitle_font)
        self.font_combo.currentFontChanged.connect(self.update_font)
        style_layout.addWidget(self.font_combo)

        style_layout.addWidget(QLabel("Tamaño:"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 72)
        self.size_spin.setValue(self.subtitle_font.pointSize())
        self.size_spin.valueChanged.connect(self.update_font_size)
        style_layout.addWidget(self.size_spin)

        self.color_button = QPushButton("Color")
        self.color_button.setStyleSheet(f"background-color: {self.subtitle_color.name()};")
        self.color_button.clicked.connect(self.choose_color)
        style_layout.addWidget(self.color_button)

        layout.addWidget(style_frame)

        self.preview_label = QLabel("Vista previa de la letra")
        self.update_preview_style()
        self.preview_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.preview_label)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Letra", "Tiempo"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.DoubleClicked)
        # Asegurar que las celdas seleccionadas sean visibles
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)

        self.generate_button = QPushButton("Ctrl+S")
        self.generate_button.setIcon(qta.icon('fa5s.save', color='black'))
        self.generate_button.clicked.connect(self.generate_srt)
        self.generate_button.setShortcut("Ctrl+S")
        layout.addWidget(self.generate_button)

        self.setLayout(layout)
        self.setWindowTitle("SRTGen")
        # Establecer el ícono en la barra superior
        icon_path = os.path.join("D:", "Proyectos", "SRTGen", "Srtgenerator.ico")
        self.setWindowIcon(QIcon(icon_path))

    def set_volume(self, value):
        """Ajusta el volumen del audio (0-100 a 0.0-1.0 para QAudioOutput)."""
        volume = value / 100.0  # Convertir de 0-100 a 0.0-1.0
        self.audio_output.setVolume(volume)

    def update_font(self, font):
        self.subtitle_font = font
        self.size_spin.setValue(font.pointSize())
        self.update_preview_style()

    def update_font_size(self, size):
        self.subtitle_font.setPointSize(size)
        self.update_preview_style()

    def choose_color(self):
        color = QColorDialog.getColor(self.subtitle_color, self, "Seleccionar color de subtítulo")
        if color.isValid():
            self.subtitle_color = color
            self.color_button.setStyleSheet(f"background-color: {color.name()};")
            self.update_preview_style()

    def update_preview_style(self):
        self.preview_label.setFont(self.subtitle_font)
        self.preview_label.setStyleSheet(
            f"QLabel {{ background-color: #000000; color: {self.subtitle_color.name()}; padding: 10px; }}"
        )

    def convert_to_wav(self, file_path):
        """Convierte un archivo MP3 a WAV temporalmente usando pydub."""
        if file_path.lower().endswith('.mp3'):
            temp_wav = os.path.splitext(file_path)[0] + "_temp.wav"
            try:
                audio = AudioSegment.from_mp3(file_path)
                audio.export(temp_wav, format="wav")
                return temp_wav
            except Exception as e:
                QMessageBox.warning(self, "Advertencia", f"No se pudo convertir a WAV: {str(e)}. Usando archivo original.")
                return file_path
        return file_path

    def cleanup_temp_file(self):
        """Elimina el archivo WAV temporal si existe."""
        if self.temp_wav_file and os.path.exists(self.temp_wav_file):
            try:
                os.remove(self.temp_wav_file)
            except Exception:
                pass
            self.temp_wav_file = None

    def load_media(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo de audio", "",
            "Audio Files (*.mp3 *.wav);;All Files (*)")
        if file_path:
            try:
                # Limpiar archivo temporal anterior
                self.cleanup_temp_file()
                
                # Convertir a WAV si es necesario
                processed_file = self.convert_to_wav(file_path)
                self.temp_wav_file = processed_file if processed_file != file_path else None
                
                self.media_player.setSource(QUrl.fromLocalFile(file_path))  # Reproducir el original
                self.media_file = processed_file  # Usar WAV para análisis
                
                # Cargar y procesar la duración sin backend específico
                y, sr = librosa.load(self.media_file, offset=0.0, duration=None, mono=True)
                self.duration = librosa.get_duration(y=y, sr=sr)
                self.time_slider.setRange(0, int(self.duration * 1000))
                
                self.media_player.mediaStatusChanged.connect(self._handle_media_status)
                self.position_timer.start()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al cargar el audio:\n{str(e)}")
                self.cleanup_temp_file()

    def seek_position(self):
        """Busca a una posición específica en el audio usando el slider de tiempo."""
        if self.media_file:
            pos = self.time_slider.value()
            self.media_player.setPosition(pos)
            self.update_position()

    def _handle_media_status(self, status):
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            self.update_time_display(0)

    def load_lyrics(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo de letras", "",
            "Text Files (*.txt);;All Files (*)")
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    lyrics = [line.strip() for line in file if line.strip()]
                self.populate_table_with_lyrics(lyrics)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al cargar las letras:\n{str(e)}")

    def populate_table_with_lyrics(self, lyrics):
        self.table.setRowCount(len(lyrics))
        total_duration = self.duration if self.duration > 0 else 210
        
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
                QMessageBox.warning(self, "Advertencia", f"No se pudo analizar silencios: {str(e)}")

        interval = total_duration / (len(lyrics) + 1)
        for i, line in enumerate(lyrics):
            self.table.setItem(i, 0, QTableWidgetItem(line))
            self.table.setItem(i, 1, QTableWidgetItem(f"{interval * (i + 1):.3f}"))

    def analyze_silences(self, file_path):
        y, sr = librosa.load(file_path, offset=0.0, duration=None, mono=True)
        silences = librosa.effects.split(y, top_db=20)
        return [(start / sr, end / sr) for start, end in silences]

    def toggle_playback(self):
        if not self.media_file:
            QMessageBox.warning(self, "Error", "Carga un archivo de audio primero")
            return
        if not self.playing:
            self.media_player.play()
            self.playing = True
            icon_color = 'white' if self.is_dark_theme else 'black'
            self.play_button.setIcon(qta.icon('fa5s.pause', color=icon_color))
            self.position_timer.start()
        else:
            self.media_player.pause()
            self.playing = False
            icon_color = 'white' if self.is_dark_theme else 'black'
            self.play_button.setIcon(qta.icon('fa5s.play', color=icon_color))
            self.position_timer.stop()

    def update_position(self):
        if self.media_file:
            position = self.media_player.position()
            # Solo actualizar el slider si no se está manipulando manualmente
            if not self.time_slider.isSliderDown():  # Verificar si el usuario no está deslizando
                self.time_slider.setValue(position)
            current_time = position / 1000.0
            self.update_time_display(current_time)
            self.update_preview(current_time)

    def update_time_display(self, current):
        cur_h, cur_m, cur_s, cur_ms = self._format_time(current)
        dur_h, dur_m, dur_s, dur_ms = self._format_time(self.duration)
        self.time_label.setText(
            f"{cur_h:02d}:{cur_m:02d}:{cur_s:02d},{cur_ms:03d} / "
            f"{dur_h:02d}:{dur_m:02d}:{dur_s:02d},{dur_ms:03d}"
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
                if time_item:
                    t = float(time_item.text())
                    if t > max_time and t <= current_time:
                        max_time = t
                        current_line = self.table.item(row, 0).text()
            except (ValueError, AttributeError):
                continue
        self.preview_label.setText(current_line or "Vista previa de la letra")

    def mark_current_time(self):
        if not self.media_file:
            QMessageBox.warning(self, "Error", "Carga un archivo de audio primero")
            return
        
        current_time = self.media_player.position() / 1000.0
        selected_row = self.table.currentRow()
        
        if selected_row >= 0:
            self.table.setItem(selected_row, 1, QTableWidgetItem(f"{current_time:.3f}"))
            next_row = selected_row + 1
            if next_row < self.table.rowCount():
                self.table.setCurrentCell(next_row, 0)
            else:
                QMessageBox.information(self, "Información", "Has llegado al final de la lista.")

    # def adjust_time(self, adjustment):
    #     selected_row = self.table.currentRow()
    #     if selected_row >= 0 and self.table.item(selected_row, 1):
    #         try:
    #             current_time = float(self.table.item(selected_row, 1).text())
    #             new_time = max(0, min(self.duration, current_time + adjustment))
    #             self.table.setItem(selected_row, 1, QTableWidgetItem(f"{new_time:.3f}"))
    #         except (ValueError, AttributeError):
    #             QMessageBox.warning(self, "Error", "Tiempo inválido en la línea seleccionada")

    def generate_srt(self):
        if not self.table.rowCount():
            QMessageBox.warning(self, "Error", "No hay letras para generar SRT")
            return
            
        timestamps = []
        for row in range(self.table.rowCount()):
            line_item = self.table.item(row, 0)
            time_item = self.table.item(row, 1)
            if not line_item or not time_item:
                continue
            line = line_item.text().strip()
            if not line:
                continue
            try:
                time_in_seconds = float(time_item.text())
                if time_in_seconds < 0 or time_in_seconds > self.duration:
                    QMessageBox.warning(self, "Error", f"Tiempo inválido en la línea {row + 1}")
                    return
                timestamps.append((time_in_seconds, line))
            except ValueError:
                QMessageBox.warning(self, "Error", f"Tiempo inválido en la línea {row + 1}")
                return
        
        if not timestamps:
            QMessageBox.warning(self, "Error", "No hay datos válidos para generar SRT")
            return
            
        timestamps.sort()
        base_name = os.path.splitext(os.path.basename(self.media_file or "output"))[0]
        output_file, _ = QFileDialog.getSaveFileName(
            self, "Guardar archivo SRT", f"{base_name}.srt",
            "SubRip Subtitle (*.srt)")
        if output_file:
            try:
                with open(output_file, "w", encoding="utf-8") as file:
                    # Agregar metadatos de estilo al inicio del SRT
                    file.write(f"## Subtitle Style\n")
                    file.write(f"# Font: {self.subtitle_font.family()}\n")
                    file.write(f"# Size: {self.subtitle_font.pointSize()}\n")
                    file.write(f"# Color: {self.subtitle_color.name()}\n\n")
                    
                    # Generar entradas SRT
                    for i, (start_time, line) in enumerate(timestamps, 1):
                        end_time = (timestamps[i][0] - 0.001 if i < len(timestamps) 
                                  else min(self.duration, start_time + 5.0))
                        file.write(f"{i}\n"
                                 f"{segundos_a_timestamp(start_time)} --> "
                                 f"{segundos_a_timestamp(end_time)}\n"
                                 f"{line}\n\n")
                QMessageBox.information(self, "Éxito", f"Archivo SRT guardado como:\n{output_file}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al guardar SRT:\n{str(e)}")
            finally:
                self.cleanup_temp_file()  # Limpiar archivo temporal al guardar

    def closeEvent(self, event):
        """Sobrescribe el cierre para limpiar archivos temporales."""
        self.cleanup_temp_file()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AudioSync()
    window.show()
    sys.exit(app.exec())