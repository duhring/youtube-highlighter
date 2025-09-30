# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YouTube Highlighter is a Python CLI application that downloads YouTube video transcripts, identifies interesting segments based on keywords, and generates a highlight webpage with thumbnails and summaries. The project includes both a command-line interface and a Flask web server.

## Development Commands

### Running Tests
```bash
# Run all tests
python3 -m pytest

# Run specific test file
python3 -m pytest tests/test_transcript.py

# Run with verbose output
python3 -m pytest tests/test_transcript.py -v

# Run specific test class/method
python3 -m pytest tests/test_transcript_downloader.py::TestTranscriptDownloader::test_find_cached_transcript_empty_file -v
```

### Running the Application
```bash
# CLI - Generate highlights (requires existing transcript file)
PYTHONPATH=. python3 app/cli.py generate "https://youtube.com/watch?v=VIDEO_ID" transcript.vtt

# CLI - Download transcript only
PYTHONPATH=. python3 app/cli.py download-transcript "https://youtube.com/watch?v=VIDEO_ID"

# CLI - Validate transcript file
PYTHONPATH=. python3 app/cli.py validate-transcript tests/sample.vtt --show-segments

# CLI - Clear transcript cache
PYTHONPATH=. python3 app/cli.py clear-cache --all

# Web server (runs on http://localhost:5000 by default)
PYTHONPATH=. python3 app/web/server.py

# Get CLI help
PYTHONPATH=. python3 app/cli.py --help
```

### Installing Dependencies
```bash
# Use the setup script for Python 3.11 (recommended)
./setup.sh

# Or manually with pip
pip3 install -r requirements.txt
```

### Environment Setup
```bash
# Activate virtual environment (after setup.sh)
source venv311/bin/activate

# Or if using standard Python 3
python3 -m venv venv
source venv/bin/activate
```

### Cleaning Up Dependencies
```bash
# Note: requirements.txt has duplicate entries that need to be cleaned up:
# - pytube>=15.0.0 appears twice (lines 1-2)  
# - Lines 17-27 duplicate lines 4-14 (transformers, torch, pillow, etc.)
# Remove duplicates to clean up the file
```

## Architecture Overview

### Core Processing Pipeline
1. **Transcript Download** (`app/transcript_downloader.py`) - Downloads subtitles using multiple fallback strategies (web scraping, yt-dlp)
2. **Transcript Parsing** (`app/transcript.py`) - Parses VTT/SRT files into structured segments
3. **Segment Finding** (`app/segments.py` & `app/intelligent_segments.py`) - Identifies interesting segments using either keyword matching or AI-based content analysis
4. **AI Summarization** (`app/summarize.py`) - Generates summaries for each segment using transformers
5. **Video Processing** (`app/video.py`) - Downloads video and extracts thumbnails at specific timestamps
6. **HTML Generation** (`app/html_generator.py`) - Creates final highlight webpage

### Key Components

**Entry Points:**
- `app/cli.py` - Typer-based CLI with commands: generate, download-transcript, validate-transcript, clear-cache
- `app/main.py` - Core orchestration function `create_highlights()` that coordinates the entire pipeline
- `app/web/server.py` - Flask web interface for browser-based usage

**Supporting Modules:**
- `app/transcript_formatter.py` - Formats and cleans transcript text
- `app/html_generator_backup.py` & `app/html_generator_simple.py` - Alternative HTML generators
- `run.sh` - Convenience script (contains hardcoded path that needs updating for different environments)

**Configuration:**
- `config.yaml` - All application settings (AI model: facebook/bart-large-cnn, video quality: 720p, thumbnail size: 1280x720, default keywords: introduction/conclusion/demo/important, etc.)
- `app/config.py` - Configuration loader with dot-notation access via `get_setting()`

**Data Flow:**
- Input: YouTube URL + optional transcript file
- Cache: `.cache/` directory for downloaded transcripts and videos
- Output: `output/` directory containing HTML page, thumbnails, and video files

### Testing Strategy
- Uses pytest framework with fixtures for sample VTT files
- Test files cover all major components with both unit and enhanced integration tests
- Sample transcript data in `tests/sample.vtt` for validation testing
- Mock external dependencies (YouTube downloads, AI models) in tests

### External Dependencies
- **Video/Audio Processing**: pytube, moviepy, yt-dlp, pillow
- **AI/ML**: transformers, torch, openai-whisper for transcript processing and summarization
- **Web Framework**: Flask for web interface
- **CLI Framework**: typer for command-line interface
- **Parsing**: beautifulsoup4 for web scraping transcripts

### Important Implementation Details
- Multiple transcript download fallbacks handle various YouTube restrictions
- Caching system prevents re-downloading transcripts and videos (`.cache/` directory)
- Flexible keyword matching with fallback to common English words if no matches found
- Support for both manual and auto-generated captions
- Robust error handling with user-friendly CLI output (emoji indicators)
- Web interface supports manual transcript upload if auto-download fails
- Dual segment finding approaches: keyword-based (`SegmentFinder`) and AI-based (`IntelligentSegmentFinder`)
- Output directory structure: timestamped folders containing HTML page and numbered thumbnail files
- Configuration via `config.yaml` with settings for video quality, AI model, thumbnails, etc.
- PYTHONPATH=. prefix required for all CLI commands due to package structure

## Known Issues & Maintenance
- `requirements.txt` contains duplicate entries that should be cleaned up
- `run.sh` contains hardcoded path that needs updating for different environments
- README.md is empty and could be populated with basic usage instructions