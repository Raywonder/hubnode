# Modern Media Player

A feature-rich desktop media player built with Electron and React, designed for Windows 11 with modern dark/light theming.

## Features

### 🎵 Core Playback
- **Multi-format support**: MP3, FLAC, WAV, OGG, M4A
- **Folder-based browsing**: Open any music directory
- **Queue management**: View and reorder your music queue
- **Repeat modes**: None, All tracks, Single track
- **Shuffle playback**: Random track selection

### 🎨 Modern Interface
- **Dark/Light themes**: Toggle between beautiful themes
- **Album art display**: Shows embedded cover art
- **Metadata extraction**: Artist, album, track info
- **Responsive design**: Works on different screen sizes
- **Clean, modern UI**: Inspired by popular music apps

### ⌨️ Keyboard Shortcuts
- `Space`: Play/Pause toggle
- `Ctrl+Left/Right` (or `Cmd+Left/Right` on Mac): Previous/Next track
- `Ctrl+O` (or `Cmd+O` on Mac): Open music folder
- `Ctrl+T` (or `Cmd+T` on Mac): Toggle theme

### 💾 Smart Features
- **Playback position memory**: Remembers where you left off
- **Settings persistence**: Theme, volume, and preferences saved
- **Auto-scan**: Recursively finds all music files in selected folder
- **Metadata caching**: Fast loading of track information

## Installation & Setup

### Prerequisites
- Node.js (v16 or later)
- npm or yarn

### Quick Start

1. **Navigate to project directory**:
   ```bash
   cd git/media-player
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Development mode** (with React dev server):
   ```bash
   npm run dev
   ```

4. **Production mode** (build and run):
   ```bash
   npm run build
   npm start
   ```

### Building for Distribution

Create distributable packages:
```bash
npm run dist
```

## Usage

1. **Launch the app** and click "📁 Open Music Folder"
2. **Select your music directory** (e.g., `C:/Users/YourName/Music`)
3. **Wait for scanning** - the app will find all supported audio files
4. **View your queue** by clicking "📜 Queue" to see all tracks
5. **Start playing** by clicking any track or using the play button
6. **Use controls** for play/pause, next/previous, shuffle, and repeat
7. **Adjust volume** with the volume slider
8. **Toggle theme** using the sun/moon button

## Project Structure

```
media-player/
├── main.js           # Electron main process
├── preload.js        # Electron preload script (security bridge)
├── package.json      # Dependencies and scripts
├── public/
│   └── index.html    # HTML template
└── src/
    ├── index.js      # React entry point
    ├── index.css     # Global styles
    ├── App.js        # Main React component
    └── App.css       # Component styles
```

## Key Components

### Electron Main Process (`main.js`)
- Window management and menu creation
- File system operations (folder scanning)
- Metadata extraction using `music-metadata`
- IPC (Inter-Process Communication) handlers

### React Frontend (`App.js`)
- Audio playback using HTML5 Audio API
- Queue management and track navigation
- Theme switching and settings persistence
- Keyboard shortcut handling

### Security Bridge (`preload.js`)
- Secure communication between Electron and React
- Exposes limited APIs to the renderer process

## Customization

### Adding New Audio Formats
Edit the `supportedExtensions` array in `main.js`:
```javascript
const supportedExtensions = ['.mp3', '.flac', '.wav', '.ogg', '.m4a', '.aac'];
```

### Changing Default Settings
Modify the default values in `App.js`:
```javascript
const savedTheme = localStorage.getItem('theme') || 'dark';
const savedVolume = localStorage.getItem('volume') || '0.7';
```

### Custom Keyboard Shortcuts
Add new shortcuts in the `handleKeyPress` function in `App.js`.

## Troubleshooting

### Common Issues

**App won't start**:
- Ensure Node.js and npm are installed
- Run `npm install` to install dependencies
- Check console for error messages

**No audio playback**:
- Verify your audio files are in supported formats
- Check system audio settings
- Ensure file paths are accessible

**Metadata not showing**:
- Some files may not have embedded metadata
- The app will show fallback information (filename, "Unknown Artist")

**Performance issues**:
- Large music libraries may take time to scan initially
- Consider organizing music into smaller subdirectories

## License

MIT License - feel free to modify and distribute.

## Contributing

This is a learning project, but contributions are welcome! Areas for improvement:
- Waveform visualization
- Playlist import/export
- Last.fm scrobbling
- More audio format support
- Performance optimizations