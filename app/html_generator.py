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
            background: #000; /* Add black background to see the container */
        }}
        
        #youtube-player-container {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100% !important;
            height: 100% !important;
        }}
        
        #youtube-player {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100% !important;
            height: 100% !important;
            border: none !important;
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
        
        
        @keyframes loading {{
            0% {{ transform: translateX(-100%); }}
            100% {{ transform: translateX(200px); }}
        }}
        
        .segment-active {{
            transform: translateY(-3px) !important;
            box-shadow: 0 8px 25px rgba(255, 255, 255, 0.2) !important;
            border: 2px solid rgba(255, 255, 255, 0.3) !important;
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
                <div id="youtube-player-container" style="width: 100%; height: 100%; position: relative;">
                    <!-- YouTube iframe will be embedded here -->
                    <iframe id="youtube-player" 
                            style="width: 100%; height: 100%; border: none;" 
                            src="https://www.youtube.com/embed/{video_id}?enablejsapi=1&rel=0&modestbranding=1&fs=1&cc_load_policy=0&iv_load_policy=3&autohide=0"
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                            allowfullscreen>
                    </iframe>
                </div>
                <div id="video-fallback" style="display: none;" class="fallback-message">
                    <p>🚫 Video embedding is disabled for this content.</p>
                    <p style="font-size: 0.9em; margin-bottom: 25px;">Click a segment below to open it directly on YouTube, or watch the full video:</p>
                    <a href="https://www.youtube.com/watch?v={video_id}" target="_blank" class="watch-on-youtube">
                        🎬 Watch Full Video on YouTube
                    </a>
                </div>
                <div id="player-loading" style="display: none;" class="fallback-message">
                    <p>🔄 Loading video player...</p>
                    <div style="width: 200px; height: 4px; background: rgba(255,255,255,0.2); border-radius: 2px; margin: 15px auto; overflow: hidden;">
                        <div style="width: 100%; height: 100%; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.6), transparent); animation: loading 1.5s infinite;"></div>
                    </div>
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
                <button class="watch-btn">Watch Segment</button>
            </div>
"""
        
        html_content += f"""
        </div>
        
        <div class="footer">
            <p>Generated with YouTube Highlight Generator</p>
        </div>
    </div>
    
    
    <script>
        // Hybrid YouTube Player: Direct iframe + API enhancement
        var player = null;
        var playerReady = false;
        var apiLoaded = false;
        var videoId = '{video_id}';
        var fallbackMode = false;
        var iframePlayer = null;
        
        
        
        // Initialize immediately when DOM loads
        document.addEventListener('DOMContentLoaded', function() {{
            iframePlayer = document.getElementById('youtube-player');
            
            // Set up click handlers first
            setupClickHandlers();
            
            // Try to enhance with YouTube API
            tryEnhanceWithAPI();
            
            // Set fallback timeout - if API doesn't work in 3 seconds, continue with basic iframe
            setTimeout(function() {{
                if (!playerReady && !fallbackMode) {{
                    setupBasicIframeMode();
                }}
            }}, 3000);
            
            // Monitor iframe load
            if (iframePlayer) {{
                iframePlayer.onload = function() {{
                    hideLoadingState();
                    ensurePlayerVisible();
                }};
                
                iframePlayer.onerror = function() {{
                    showFallbackMessage();
                }};
            }}
        }});
        
        function tryEnhanceWithAPI() {{
            
            // Check if API already exists
            if (window.YT && window.YT.Player) {{
                initializeAPIPlayer();
                return;
            }}
            
            // Try to load API
            var script = document.createElement('script');
            script.src = 'https://www.youtube.com/iframe_api';
            script.onerror = function() {{
                setupBasicIframeMode();
            }};
            
            var firstScript = document.getElementsByTagName('script')[0];
            firstScript.parentNode.insertBefore(script, firstScript);
        }}
        
        // Global callback required by YouTube API
        window.onYouTubeIframeAPIReady = function() {{
            apiLoaded = true;
            initializeAPIPlayer();
        }};
        
        function initializeAPIPlayer() {{
            try {{
                // Replace iframe with API player
                player = new YT.Player('youtube-player', {{
                    height: '100%',
                    width: '100%',
                    videoId: videoId,
                    playerVars: {{
                        'enablejsapi': 1,
                        'rel': 0,
                        'modestbranding': 1,
                        'fs': 1,
                        'cc_load_policy': 0,
                        'iv_load_policy': 3,
                        'autohide': 0
                    }},
                    events: {{
                        'onReady': function(event) {{
                            playerReady = true;
                            hideLoadingState();
                            
                            // Force player to be visible
                            setTimeout(function() {{
                                ensurePlayerVisible();
                            }}, 1000);
                        }},
                        'onError': function(event) {{
                            playerReady = false; // Reset player ready state
                            player = null; // Clear player reference
                            
                            if ([101, 150].includes(event.data)) {{
                                // Embedding disabled - show fallback message
                                showFallbackMessage();
                            }} else if (event.data === 2) {{
                                // Invalid video ID - try to reload iframe with current video ID
                                reloadBasicIframe();
                            }} else {{
                                setupBasicIframeMode();
                            }}
                        }}
                    }}
                }});
            }} catch (error) {{
                setupBasicIframeMode();
            }}
        }}
        
        function setupBasicIframeMode() {{
            fallbackMode = false; // Not true fallback, just basic mode
            playerReady = false; // Make sure API seeking is disabled
            player = null; // Clear API player reference
            hideLoadingState();
            
            // Ensure iframe is visible
            setTimeout(function() {{
                ensurePlayerVisible();
            }}, 500);
        }}
        
        function reloadBasicIframe() {{
            if (iframePlayer) {{
                var newSrc = 'https://www.youtube.com/embed/' + videoId + 
                            '?enablejsapi=1&rel=0&modestbranding=1&fs=1&cc_load_policy=0&iv_load_policy=3&autohide=0';
                iframePlayer.src = newSrc;
            }}
            setupBasicIframeMode();
        }}
        
        function showFallbackMessage() {{
            fallbackMode = true;
            hideLoadingState();
            
            var container = document.getElementById('youtube-player-container');
            var fallback = document.getElementById('video-fallback');
            
            if (container) container.style.display = 'none';
            if (fallback) fallback.style.display = 'block';
        }}
        
        function hideLoadingState() {{
            var loading = document.getElementById('player-loading');
            if (loading) loading.style.display = 'none';
        }}
        
        function ensurePlayerVisible() {{
            var container = document.getElementById('youtube-player-container');
            var playerEl = document.getElementById('youtube-player');
            
            if (container) {{
                container.style.display = 'block';
                container.style.position = 'absolute';
                container.style.top = '0';
                container.style.left = '0';
                container.style.width = '100%';
                container.style.height = '100%';
                container.style.zIndex = '1';
            }}
            
            if (playerEl) {{
                // Check if it's an iframe or div (API player)
                var tagName = playerEl.tagName.toLowerCase();
                
                playerEl.style.display = 'block';
                playerEl.style.position = 'absolute';
                playerEl.style.top = '0';
                playerEl.style.left = '0';
                playerEl.style.width = '100%';
                playerEl.style.height = '100%';
                playerEl.style.border = 'none';
                playerEl.style.zIndex = '2';
                
                if (tagName === 'iframe') {{
                    playerEl.style.backgroundColor = '#000';
                }}
            }}
        }}
        
        function seekToTime(seconds) {{
            showSeekingFeedback(seconds);
            
            if (fallbackMode) {{
                // Open in new tab
                var url = 'https://www.youtube.com/watch?v=' + videoId + '&t=' + Math.floor(seconds) + 's';
                window.open(url, '_blank');
                return;
            }}
            
            // Try iframe src manipulation FIRST (more reliable for restricted videos)
            if (iframePlayer && !fallbackMode) {{
                try {{
                    var newSrc = 'https://www.youtube.com/embed/' + videoId + 
                                '?enablejsapi=1&rel=0&modestbranding=1&fs=1&cc_load_policy=0&iv_load_policy=3&autohide=0' +
                                '&start=' + Math.floor(seconds) + '&autoplay=1';
                    iframePlayer.src = newSrc;
                    scrollToVideo();
                    return;
                }} catch (error) {{
                    // Try API method
                }}
            }}
            
            if (playerReady && player && typeof player.seekTo === 'function') {{
                // Use API seeking as fallback
                try {{
                    player.seekTo(seconds, true);
                    player.playVideo();
                    scrollToVideo();
                    return;
                }} catch (error) {{
                    // Use ultimate fallback
                }}
            }}
            
            // Ultimate fallback - open in new tab with timestamp
            var url = 'https://www.youtube.com/watch?v=' + videoId + '&t=' + Math.floor(seconds) + 's';
            window.open(url, '_blank');
        }}
        
        function showSeekingFeedback(seconds) {{
            var feedback = document.createElement('div');
            feedback.innerHTML = '🎬 Jumping to ' + formatTime(seconds) + '...';
            feedback.style.cssText = 'position: fixed; top: 20px; right: 20px; background: rgba(0,0,0,0.8); color: white; padding: 10px 20px; border-radius: 25px; font-size: 14px; z-index: 10000; transition: opacity 0.3s;';
            
            document.body.appendChild(feedback);
            
            setTimeout(function() {{
                feedback.style.opacity = '0';
                setTimeout(function() {{
                    if (feedback.parentNode) feedback.parentNode.removeChild(feedback);
                }}, 300);
            }}, 2000);
        }}
        
        function formatTime(seconds) {{
            var minutes = Math.floor(seconds / 60);
            var remainingSeconds = Math.floor(seconds % 60);
            return minutes + ':' + (remainingSeconds < 10 ? '0' : '') + remainingSeconds;
        }}
        
        function scrollToVideo() {{
            var container = document.querySelector('.video-container');
            if (container) {{
                container.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
            }}
        }}
        
        function highlightActiveSegment(card) {{
            // Remove active class from all cards
            var cards = document.querySelectorAll('.highlight-card');
            for (var i = 0; i < cards.length; i++) {{
                cards[i].classList.remove('segment-active');
            }}
            
            // Add active class to clicked card
            card.classList.add('segment-active');
            
            // Remove after 3 seconds
            setTimeout(function() {{
                card.classList.remove('segment-active');
            }}, 3000);
        }}
        
        function setupClickHandlers() {{
            var cards = document.querySelectorAll('.highlight-card');
            
            cards.forEach(function(card, index) {{
                var timestamp = parseInt(card.getAttribute('data-timestamp'));
                
                card.addEventListener('click', function(event) {{
                    if (event.target.tagName === 'BUTTON') return;
                    
                    highlightActiveSegment(card);
                    seekToTime(timestamp);
                }});
                
                var watchBtn = card.querySelector('.watch-btn');
                if (watchBtn) {{
                    watchBtn.addEventListener('click', function(event) {{
                        event.preventDefault();
                        event.stopPropagation();
                        highlightActiveSegment(card);
                        seekToTime(timestamp);
                    }});
                }}
            }});
        }}
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
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
            r'youtube\.com/v/([^&\n?#]+)',
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