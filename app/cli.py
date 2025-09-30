import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import typer
from typing_extensions import Annotated
from app.main import create_highlights
from app.config import get_setting
from app.transcript_downloader import TranscriptDownloader
from app.transcript import TranscriptParser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = typer.Typer()

@app.command()
def generate(
    youtube_url: str = typer.Argument(..., help="The URL of the YouTube video."),
    transcript_file: str = typer.Argument(..., help="Path to the transcript file (.vtt or .srt)."),
    description: str = typer.Option(None, "--description", "-d", help="A description for the highlight page."),
    keywords: str = typer.Option(None, "--keywords", "-k", help="Comma-separated keywords to find interesting segments (e.g., 'love,rules,never')."),
    num_cards: int = typer.Option(4, "--cards", "-c", help="The number of highlight cards to generate."),
    output_dir: str = typer.Option(None, "--output-dir", "-o", help="Output directory for generated files."),
):
    """
    Generate a video highlights page.
    """
    # Parse comma-separated keywords
    if keywords:
        keywords_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]
    else:
        keywords_list = None
    
    create_highlights(youtube_url, transcript_file, description, keywords_list, num_cards, output_dir)

@app.command()
def download_transcript(
    youtube_url: str = typer.Argument(..., help="The URL of the YouTube video."),
    output_dir: str = typer.Option(get_setting("output_dir", "output"), "--output-dir", "-o", help="The directory to save the transcript to."),
    force: bool = typer.Option(False, "--force", "-f", help="Force re-download even if transcript exists in cache"),
    validate: bool = typer.Option(True, "--validate/--no-validate", help="Validate downloaded transcript"),
):
    """
    Download the transcript for a YouTube video using improved downloader.
    """
    from pathlib import Path
    import shutil
    
    try:
        # Initialize downloader
        downloader = TranscriptDownloader()
        
        # Extract video ID
        video_id = downloader._extract_video_id(youtube_url)
        if not video_id:
            print(f"❌ Invalid YouTube URL: {youtube_url}")
            raise typer.Exit(1)
        
        print(f"🎬 Processing video: {video_id}")
        
        # Clear cache if force flag is used
        if force:
            print(f"🔄 Clearing cache for video: {video_id}")
            downloader.clear_cache(video_id)
        
        # Download transcript
        transcript_path = downloader.download_transcript(youtube_url, video_id)
        
        if not transcript_path:
            print(f"❌ Could not download transcript for video: {video_id}")
            print("   This could be because:")
            print("   • The video has no subtitles available")
            print("   • The video is private or restricted")
            print("   • Network connectivity issues")
            raise typer.Exit(1)
        
        print(f"✅ Transcript downloaded: {transcript_path}")
        
        # Validate transcript if requested
        if validate:
            try:
                segments = TranscriptParser.parse(transcript_path)
                validated_segments = TranscriptParser.validate_segments(segments)
                print(f"✅ Validation successful: {len(validated_segments)} valid segments")
            except Exception as e:
                print(f"⚠️ Transcript validation failed: {e}")
        
        # Copy to output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        output_transcript_path = Path(output_dir) / f"{video_id}.{Path(transcript_path).suffix[1:]}"  # Preserve extension
        
        shutil.copy2(transcript_path, output_transcript_path)
        print(f"💾 Transcript copied to: {output_transcript_path}")
        
    except Exception as e:
        logger.error(f"Transcript download failed: {e}")
        print(f"❌ Error: {e}")
        raise typer.Exit(1)

@app.command()
def validate_transcript(
    transcript_file: str = typer.Argument(..., help="Path to the transcript file to validate."),
    show_segments: bool = typer.Option(False, "--show-segments", "-s", help="Show first few segments"),
):
    """
    Validate a transcript file and show basic information.
    """
    from pathlib import Path
    
    try:
        transcript_path = Path(transcript_file)
        
        if not transcript_path.exists():
            print(f"❌ File not found: {transcript_file}")
            raise typer.Exit(1)
        
        print(f"📝 Validating transcript: {transcript_path}")
        print(f"   File size: {transcript_path.stat().st_size} bytes")
        print(f"   Format: {transcript_path.suffix}")
        
        # Parse and validate
        segments = TranscriptParser.parse(transcript_path)
        validated_segments = TranscriptParser.validate_segments(segments)
        
        print(f"✅ Validation successful!")
        print(f"   Total segments parsed: {len(segments)}")
        print(f"   Valid segments: {len(validated_segments)}")
        
        if validated_segments:
            total_duration = validated_segments[-1]['end'] - validated_segments[0]['start']
            print(f"   Duration: {total_duration:.1f} seconds ({total_duration/60:.1f} minutes)")
            
            if show_segments and len(validated_segments) >= 3:
                print(f"\n🔍 First 3 segments:")
                for i, segment in enumerate(validated_segments[:3]):
                    start_min = int(segment['start'] // 60)
                    start_sec = segment['start'] % 60
                    end_min = int(segment['end'] // 60)
                    end_sec = segment['end'] % 60
                    print(f"   {i+1}. [{start_min}:{start_sec:04.1f} - {end_min}:{end_sec:04.1f}] {segment['text'][:100]}{'...' if len(segment['text']) > 100 else ''}")
        
    except Exception as e:
        logger.error(f"Transcript validation failed: {e}")
        print(f"❌ Validation failed: {e}")
        raise typer.Exit(1)

@app.command()
def clear_cache(
    video_id: str = typer.Option(None, "--video-id", "-v", help="Clear cache for specific video ID"),
    all_cache: bool = typer.Option(False, "--all", "-a", help="Clear entire transcript cache"),
):
    """
    Clear transcript cache.
    """
    try:
        downloader = TranscriptDownloader()
        
        if all_cache:
            print("🗑️ Clearing entire transcript cache...")
            downloader.clear_cache()
            print("✅ Cache cleared successfully")
        elif video_id:
            print(f"🗑️ Clearing cache for video: {video_id}")
            downloader.clear_cache(video_id)
            print("✅ Cache cleared successfully")
        else:
            print("❌ Please specify either --video-id or --all")
            raise typer.Exit(1)
            
    except Exception as e:
        logger.error(f"Cache clear failed: {e}")
        print(f"❌ Error: {e}")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
