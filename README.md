# SRTGen - Audio Subtitle Synchronization Tool

A powerful GUI application for creating and synchronizing SRT subtitle files with audio tracks.

## Features

- 🎵 Audio file synchronization (supports MP3 and WAV formats)
- 📝 Text-to-subtitle conversion
- ⚡ Real-time preview of subtitles
- ⌚ Precise timing controls with millisecond accuracy
- 🎮 Keyboard shortcuts for efficient workflow
- 🔍 Automatic silence detection for initial timing suggestions
- 📊 Interactive table interface for managing subtitles
- 💾 Export to standard SRT format

## Keyboard Shortcuts

- `Ctrl+O` - Load audio file
- `Ctrl+L` - Load lyrics file
- `Ctrl+S` - Generate and save SRT file
- `Space` - Play/Pause audio
- `M` - Mark current time
- `←` - Adjust time -0.1 seconds
- `→` - Adjust time +0.1 seconds

## Requirements

- Python 3.8 or higher
- PyQt5
- librosa
- qtawesome

## Installation

1. Clone the repository:
```bash
git clone https://github.com/aortiz248911/SRTGen.git
```

2. Install dependencies:
```bash
pip install PyQt5 librosa qtawesome
 ```

3. Run the application:
```bash
python srtgen.py
 ```

## How to Use
1. Load Audio File
   
   - Click the folder icon or press Ctrl+O
   - Select your MP3 or WAV audio file
2. Load Lyrics
   
   - Click the text file icon or press Ctrl+L
   - Select your lyrics text file (one line per subtitle)
3. Synchronize Subtitles
   
   - Use the play/pause button (Space) to control audio playback
   - Press M to mark the start time for each subtitle line
   - Use left/right arrows to fine-tune timings by 0.1 seconds
   - Preview subtitles in real-time in the black preview box
4. Generate SRT File
   
   - Click the save icon or press Ctrl+S
   - Choose where to save your SRT file
## Input File Format
Create a simple text file with your subtitles, one line per subtitle:

```plaintext
First line of the subtitle
Second line of the subtitle
Third line of the subtitle
 ```

## Output Format
The generated SRT file follows the standard format:

```plaintext
1
00:00:01,000 --> 00:00:04,000
First line of the subtitle

2
00:00:04,001 --> 00:00:08,000
Second line of the subtitle
 ```

## Tips for Best Results
1. Prepare a clean lyrics text file before starting
2. Use automatic silence detection for initial timing suggestions
3. Fine-tune timings using the arrow keys
4. Preview in real-time to ensure proper synchronization
## Troubleshooting
- Audio won't load : Ensure file format is MP3 or WAV
- Missing dependencies : Run pip install -r requirements.txt
- Timing issues : Use arrow keys for fine adjustments
## Contributing
Contributions are welcome! Please feel free to:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request
## License
This project is licensed under the MIT License.

## Author
Andrés Ortiz

## Support
For issues and feature requests, please use the GitHub issues tracker.

## Acknowledgments
- PyQt5 for the GUI framework
- librosa for audio processing
- qtawesome for the icons
