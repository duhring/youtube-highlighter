from pathlib import Path
from app.config import get_setting
from app.transcript import TranscriptParser
from app.segments import SegmentFinder
from app.summarize import AISummarizer
from app.video import VideoProcessor
from app.html_generator import HTMLGenerator

def create_highlights(youtube_url: str, transcript_file: str, description: str = None, keywords: list = None, num_cards: int = 4, output_dir: str = None, content_description: str = None):
    """
    Main function to create video highlights.
    """
    if output_dir is None:
        output_dir = get_setting("output_dir", "output")
    
    print("🎬 YouTube Highlight Generator v2")
    print("=" * 40)
    print(f"📁 Output directory: {output_dir}")

    # 1. Parse Transcript
    print(f"📄 Parsing transcript: {transcript_file}")
    try:
        transcript_segments = TranscriptParser.parse(transcript_file)
        validated_segments = TranscriptParser.validate_segments(transcript_segments)
        
        if not validated_segments:
            print("❌ No valid transcript segments found. Check your transcript file.")
            return
            
        print(f"✅ Parsed and validated {len(validated_segments)} transcript segments")
        transcript_segments = validated_segments
        
    except (ValueError, FileNotFoundError) as e:
        print(f"❌ Transcript parsing failed: {e}")
        return
    except Exception as e:
        print(f"❌ Unexpected error parsing transcript: {e}")
        return

    # 2. Find Interesting Segments
    print(f"🔍 Finding segments...")
    
    # Use intelligent segment finder if content description is provided
    if content_description:
        print(f"🧠 Using intelligent segment finding with description: {content_description[:100]}...")
        from app.intelligent_segments import IntelligentSegmentFinder
        segment_finder = IntelligentSegmentFinder(content_description)
        interesting_segments = segment_finder.find_segments(transcript_segments, num_cards)
    else:
        print(f"🔤 Using keyword-based segment finding...")
        segment_finder = SegmentFinder(keywords)
        interesting_segments = segment_finder.find_segments(transcript_segments, num_cards)
    
    # If no segments found with specific keywords, try fallback strategy
    if not interesting_segments:
        print("⚠️ No segments found with specified keywords. Trying fallback strategy...")
        print(f"💡 Searched for: {segment_finder.keywords}")
        
        # Try with most common English words as fallback
        fallback_keywords = ["the", "and", "you", "to", "a", "is", "it", "in", "for", "on"]
        fallback_finder = SegmentFinder(fallback_keywords)
        interesting_segments = fallback_finder.find_segments(transcript_segments, num_cards)
        
        if not interesting_segments:
            # If still no segments, just take the first few segments
            print("🔄 No keyword matches found. Using first segments as highlights...")
            interesting_segments = transcript_segments[:num_cards]
            
            # Add required fields for segment processing
            for i, segment in enumerate(interesting_segments):
                segment['keyword'] = 'auto-selected'
                segment['score'] = 1
                segment['index'] = i
        else:
            print(f"✅ Found {len(interesting_segments)} segments using fallback keywords")
    else:
        print(f"✅ Found {len(interesting_segments)} interesting segments")

    # 3. Summarize Segments
    print("📝 Summarizing segments...")
    summarizer = AISummarizer()
    for segment in interesting_segments:
        segment['summary'] = summarizer.summarize(segment['text'])

    # 4. Process Video
    video_processor = VideoProcessor(output_dir)
    video_path, video_title = video_processor.download_video(youtube_url)

    # 5. Extract Thumbnails
    thumbnails = video_processor.extract_thumbnails(video_path, interesting_segments)

    # 6. Generate HTML
    print("🌐 Generating HTML page...")
    html_generator = HTMLGenerator(output_dir)
    html_path = html_generator.generate(
        youtube_url,
        video_title or "Unknown Video",
        description,
        interesting_segments,
        thumbnails
    )

    print("\n🎉 Success!")
    print(f"📁 Output directory: {output_dir}")
    print(f"🌐 HTML file: {html_path}")
    print(f"📦 Ready to deploy to Netlify!")
