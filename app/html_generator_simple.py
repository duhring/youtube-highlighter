from pathlib import Path
import re
from app.config import get_setting

class HTMLGenerator:
    """Generate the final HTML page"""

    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.title = get_setting("html.title", "Video Highlights")

    def generate(self, youtube_url, video_title, description, segments, thumbnails):
        """Generate the HTML highlight page"""
        video_id = self._extract_video_id(youtube_url)
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{description or self.title} - Video Highlights</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 40px;
            color: white;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header p {{
            font-size: 1.2rem;
            opacity: 0.9;
        }}
        
        .video-container {{
            margin-bottom: 40px;
            text-align: center;
        }}
        
        .video-wrapper {{
            position: relative;
            padding-bottom: 56.25%;
            height: 0;
            overflow: hidden;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}
        
        .fallback-message {{
            background: rgba(255, 255, 255, 0.1);
            padding: 40px;
            border-radius: 15px;
            text-align: center;
            color: white;
            backdrop-filter: blur(10px);
        }}
        
        .fallback-message p {{
            margin-bottom: 20px;
            font-size: 1.2rem;
            opacity: 0.9;
        }}
        
        .watch-on-youtube {{
            display: inline-block;
            background: linear-gradient(135deg, #ff0000, #cc0000);
            color: white;
            padding: 15px 30px;
            border-radius: 25px;
            text-decoration: none;
            font-weight: bold;
            font-size: 1.1rem;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .watch-on-youtube:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(255, 0, 0, 0.3);
        }}
        
        .highlights-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin-top: 40px;
        }}
        
        .highlight-card {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
            color: white;
            cursor: pointer;
            position: relative;
        }}
        
        .highlight-card:hover {{
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.15);
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);
        }}
        
        .highlight-card:active {{
            transform: translateY(-3px);
        }}
        
        .thumbnail {{
            width: 100%;
            height: 180px;
            object-fit: cover;
            border-radius: 8px;
            margin-bottom: 15px;
        }}
        
        .placeholder-thumbnail {{
            width: 100%;
            height: 180px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            border-radius: 8px;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 3rem;
            opacity: 0.7;
        }}
        
        .summary {{
            font-size: 1rem;
            line-height: 1.6;
            margin-bottom: 15px;
            min-height: 80px;
        }}
        
        .timestamp {{
            font-size: 0.9rem;
            opacity: 0.8;
            margin-bottom: 10px;
        }}
        
        .watch-btn {{
            display: inline-block;
            background: linear-gradient(135deg, #ff6b6b, #ee5a24);
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 25px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(238, 90, 36, 0.3);
            border: none;
            cursor: pointer;
            font-family: inherit;
        }}
        
        .watch-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(238, 90, 36, 0.4);
        }}
        
        .youtube-thumbnail {{
            width: 100%;
            height: 180px;
            object-fit: cover;
            border-radius: 8px;
            margin-bottom: 15px;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 60px;
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.9rem;
        }}
        
        .debug-info {{
            position: fixed;
            bottom: 10px;
            right: 10px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
            max-width: 300px;
            font-family: monospace;
            z-index: 10000;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 2rem;
            }}
            
            .highlights-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{description or self.title}</h1>
            <p>Key highlights from the video</p>
        </div>
        
        <div class="video-container">
            <div class="video-wrapper">
                <div class="fallback-message">
                    <p>🎬 Click any segment below to watch it on YouTube</p>
                    <a href="https://www.youtube.com/watch?v={video_id}" target="_blank" class="watch-on-youtube">
                        Watch Full Video on YouTube
                    </a>
                </div>
            </div>
        </div>
        
        <div class="highlights-grid">
"""
        
        thumbnails_padded = thumbnails + [None] * (len(segments) - len(thumbnails))
        
        for i, segment in enumerate(segments):
            start_time = int(segment['start'])
            timestamp_display = self._format_timestamp(segment['start'])
            thumbnail = thumbnails_padded[i] if i < len(thumbnails_padded) else None
            
            if thumbnail and Path(thumbnail).exists():
                thumbnail_html = f'<img src="{Path(thumbnail).name}" alt="Thumbnail {i+1}" class="thumbnail">'
            else:
                youtube_thumb_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                thumbnail_html = f'<img src="{youtube_thumb_url}" alt="Thumbnail {i+1}" class="youtube-thumbnail">'
            
            html_content += f"""
            <div class="highlight-card" data-timestamp="{start_time}">
                {thumbnail_html}
                <div class="summary">{segment.get('summary', segment['text'][:200] + '...')}</div>
                <div class="timestamp">Starts at {timestamp_display}</div>
                <button class="watch-btn" onclick="openYouTubeAtTime('{video_id}', {start_time})">Watch Segment</button>
            </div>
"""
        
        html_content += f"""
        </div>
        
        <div class="footer">
            <p>Generated with YouTube Highlight Generator</p>
        </div>
    </div>
    
    <div id="debug-info" class="debug-info" style="display: none;"></div>
    
    <script>
        // Simple, bulletproof video player
        console.log('Simple video player loaded');
        
        function debugMsg(msg) {{
            console.log('[VideoPlayer] ' + msg);
            var debugDiv = document.getElementById('debug-info');
            if (debugDiv) {{
                debugDiv.style.display = 'block';
                debugDiv.innerHTML += '<div>' + msg + '</div>';
            }}
        }}
        
        function openYouTubeAtTime(videoId, seconds) {{
            var url = 'https://www.youtube.com/watch?v=' + videoId + '&t=' + seconds + 's';
            debugMsg('Opening: ' + url);
            window.open(url, '_blank');
        }}
        
        // Set up click handlers when DOM is ready
        document.addEventListener('DOMContentLoaded', function() {{
            debugMsg('DOM ready, setting up click handlers');
            
            var cards = document.querySelectorAll('.highlight-card');
            debugMsg('Found ' + cards.length + ' cards');
            
            cards.forEach(function(card, index) {{
                var timestamp = card.getAttribute('data-timestamp');
                
                // Add click handler to the entire card
                card.addEventListener('click', function(event) {{
                    // Don't handle if clicking the button directly
                    if (event.target.tagName === 'BUTTON') {{
                        return;
                    }}
                    
                    debugMsg('Card ' + index + ' clicked, timestamp: ' + timestamp);
                    openYouTubeAtTime('{video_id}', parseInt(timestamp));
                }});
            }});
        }});
        
        debugMsg('Script loaded successfully');
    </script>
</body>
</html>
"""
        
        html_path = self.output_dir / "index.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML page generated: {html_path}")
        return str(html_path)
    
    def _extract_video_id(self, youtube_url):
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:youtube\\.com/watch\\?v=|youtu\\.be/|youtube\\.com/embed/)([^&\\n?#]+)',
            r'youtube\\.com/v/([^&\\n?#]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, youtube_url)
            if match:
                return match.group(1)
        return "unknown"
    
    def _format_timestamp(self, seconds):
        """Format seconds as MM:SS or HH:MM:SS"""
        if seconds < 3600:
            return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"