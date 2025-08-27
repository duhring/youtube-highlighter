# YouTube Highlighter

Create stunning video highlight pages from YouTube videos with AI-powered segment detection and summarization.

## Overview

YouTube Highlighter leverages artificial intelligence to analyze YouTube videos and extract the most engaging moments, creating condensed highlight compilations with beautiful HTML output pages. This tool streamlines the process of identifying and extracting key moments from long-form content, making it ideal for content creators, researchers, and viewers who want to quickly access the most important parts of videos.

## Features

- **Smart Transcript Extraction**: Downloads subtitles from YouTube videos with multiple fallback methods
- **Intelligent Segment Detection**: Uses AI or keyword matching to find the most interesting parts
- **AI Summarization**: Generates concise summaries for each highlight segment using facebook/bart-large-cnn
- **Automatic Thumbnails**: Extracts video thumbnails at key moments
- **Beautiful HTML Output**: Creates shareable highlight pages ready for deployment
- **Web Interface**: Browser-based interface for easy use
- **CLI Support**: Command-line tools for automation and batch processing
- **Dual Interface**: Choose between CLI for automation/scripting or web interface for user-friendly interaction

## Use Cases

- Content creators looking to repurpose long-form content into engaging shorts and highlight pages
- Researchers needing to quickly identify key moments in educational or documentary content  
- Viewers wanting to catch the best moments from lengthy videos without watching the full content
- Creating shareable highlight pages for social media and websites

## Quick Start

### Prerequisites

- Python 3.11 (recommended) or Python 3.8+
- macOS, Linux, or Windows

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/duhring/youtube-highlighter
   cd youtube-highlighter
   ```

2. **Run the setup script (recommended):**
   ```bash
   ./setup.sh
   ```
   
   This will:
   - Install Python 3.11 if needed (via Homebrew on macOS)
   - Create a virtual environment
   - Install all dependencies

3. **Activate the virtual environment:**
   ```bash
   source venv311/bin/activate
   ```

### Usage

#### Web Interface (Easiest)

1. **Start the web server:**
   ```bash
   PYTHONPATH=. python3 app/web/server.py
   ```

2. **Open your browser to:** http://localhost:5000

3. **Enter a YouTube URL** and let the app do the rest!

#### Command Line Interface

1. **Generate highlights for a video:**
   ```bash
   # Download transcript and generate highlights in one step
   PYTHONPATH=. python3 app/cli.py download-transcript "https://youtube.com/watch?v=VIDEO_ID"
   PYTHONPATH=. python3 app/cli.py generate "https://youtube.com/watch?v=VIDEO_ID" "VIDEO_ID.vtt"
   ```

2. **With custom keywords:**
   ```bash
   PYTHONPATH=. python3 app/cli.py generate "https://youtube.com/watch?v=VIDEO_ID" "transcript.vtt" --keywords "demo,tutorial,important"
   ```

3. **Just download a transcript:**
   ```bash
   PYTHONPATH=. python3 app/cli.py download-transcript "https://youtube.com/watch?v=VIDEO_ID"
   ```

## Examples

### Basic Usage
```bash
# Download transcript
PYTHONPATH=. python3 app/cli.py download-transcript "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Generate 6 highlight cards with custom description
PYTHONPATH=. python3 app/cli.py generate \
  "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  "dQw4w9WgXcQ.vtt" \
  --description "Rick Astley's Classic Hit" \
  --cards 6
```

### Advanced Usage
```bash
# Use specific keywords and custom output directory
PYTHONPATH=. python3 app/cli.py generate \
  "https://www.youtube.com/watch?v=VIDEO_ID" \
  "transcript.vtt" \
  --keywords "introduction,demo,conclusion" \
  --cards 4 \
  --output-dir "my-highlights"
```

## Configuration

The app uses `config.yaml` for settings:

- **Video quality**: 720p (default), 1080p, highest, lowest
- **AI model**: facebook/bart-large-cnn (for summarization)
- **Thumbnail size**: 1280x720 pixels
- **Default keywords**: introduction, conclusion, demo, important

## Output

The app generates:
- **HTML highlight page** with embedded video player
- **Thumbnail images** for each highlight
- **Timestamped folders** in the output directory
- **Ready-to-deploy** static files

## Troubleshooting

### Common Issues

**"No transcript available"**
- Some videos don't have subtitles
- Try videos with manual captions first
- Use the web interface to upload your own transcript

**"PYTHONPATH error"**
- Always prefix commands with `PYTHONPATH=.`
- This is required due to the package structure

**"Permission denied" on setup.sh**
- Run: `chmod +x setup.sh`
- Then: `./setup.sh`

### Getting Help

```bash
# CLI help
PYTHONPATH=. python3 app/cli.py --help

# Command-specific help
PYTHONPATH=. python3 app/cli.py generate --help
```

## Development

### Running Tests
```bash
# Run all tests
python3 -m pytest

# Run specific test with verbose output
python3 -m pytest tests/test_transcript.py -v
```

### Project Structure
```
app/
├── cli.py              # Command-line interface
├── main.py             # Core highlight generation
├── transcript_downloader.py  # YouTube transcript extraction
├── segments.py         # Keyword-based segment finding
├── intelligent_segments.py   # AI-based segment finding
├── summarize.py        # AI summarization
├── video.py            # Video processing and thumbnails
├── html_generator.py   # HTML page generation
└── web/
    └── server.py       # Flask web interface

tests/                  # Test suite
config.yaml            # Configuration file
```

---

*Note: This tool is designed to enhance video consumption and content creation workflows while respecting content creators' rights and YouTube's terms of service.*