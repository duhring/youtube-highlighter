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
        
        .video-wrapper iframe {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            border: none;
        }}
        
        .fallback-message {{
            background: rgba(255, 255, 255, 0.1);
            padding: 40px;
            border-radius: 15px;
            text-align: center;
            color: white;
            backdrop-filter: blur(10px);
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 80%;
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
        
        .watch-btn {{
            background: none;
            border: none;
            font: inherit;
            cursor: pointer;
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
                    <!-- Player will be created here by JavaScript -->
                    <div id="youtube-player" style="width: 100%; height: 100%;"></div>
                </div>
                <div id="video-fallback" style="display: none;" class="fallback-message">
                    <p>🚫 Video embedding is disabled for this content.</p>
                    <p style="font-size: 0.9em; margin-bottom: 25px;">Click a segment below to open it directly on YouTube, or watch the full video:</p>
                    <a href="https://www.youtube.com/watch?v={video_id}" target="_blank" class="watch-on-youtube">
                        🎬 Watch Full Video on YouTube
                    </a>
                </div>
                <div id="player-loading" class="fallback-message" style="background: rgba(255, 255, 255, 0.05);">
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
        
        html_content += """
        </div>
        
        <div class="footer">
            <p>Generated with YouTube Highlight Generator</p>
        </div>
    </div>
    
    <script>
        // Enhanced video player with robust segment seeking
        let player = null;
        let playerReady = false;
        let apiLoaded = false;
        let videoId = '{video_id}';
        let pendingSeek = null;
        let fallbackMode = false;
        let retryCount = 0;
        const maxRetries = 3;
        
        // Debug logging
        function debugLog(message) {
            console.log(`[VideoPlayer] ${{message}}`);
            // Also show debug messages on page for troubleshooting
            const debugDiv = document.getElementById('debug-messages') || createDebugDiv();
            debugDiv.innerHTML += `<div>[VideoPlayer] ${{message}}</div>`;
        }
        
        function createDebugDiv() {
            const div = document.createElement('div');
            div.id = 'debug-messages';
            div.style.cssText = `
                position: fixed; bottom: 10px; right: 10px; 
                background: rgba(0,0,0,0.8); color: white; 
                padding: 10px; border-radius: 5px; 
                font-size: 12px; max-width: 300px; 
                max-height: 200px; overflow-y: auto; 
                z-index: 10000; font-family: monospace;
            `;
            document.body.appendChild(div);
            return div;
        }
        
        // Load YouTube iframe API with error handling
        function loadYouTubeAPI() {
            debugLog('Loading YouTube iframe API...');
            showLoadingState();
            
            // Check if API is already loaded
            if (window.YT && window.YT.Player) {
                debugLog('YouTube API already available');
                apiLoaded = true;
                initializePlayer();
                return;
            }
            
            // Immediate check if we're in an environment that blocks YouTube
            setTimeout(() => {
                if (!window.YT) {
                    debugLog('YouTube API not loading, possible blocking detected');
                }
            }, 2000);
            
            // Create script tag to load API
            const tag = document.createElement('script');
            tag.src = "https://www.youtube.com/iframe_api";
            tag.onerror = function() {
                debugLog('Failed to load YouTube iframe API, using fallback');
                fallbackMode = true;
                setupFallbackMode();
            };
            
            const firstScriptTag = document.getElementsByTagName('script')[0];
            firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
            
            // Set timeout for API loading
            setTimeout(() => {
                if (!apiLoaded && !fallbackMode) {
                    debugLog('YouTube API loading timeout, switching to fallback');
                    fallbackMode = true;
                    setupFallbackMode();
                }
            }, 5000);
        }
        
        function showLoadingState() {
            const loading = document.getElementById('player-loading');
            const fallback = document.getElementById('video-fallback');
            
            if (loading) {
                loading.style.display = 'block';
            }
            if (fallback) {
                fallback.style.display = 'none';
            }
        }
        
        function hideLoadingState() {
            const loading = document.getElementById('player-loading');
            if (loading) {
                loading.style.display = 'none';
            }
        }
        
        // Global function required by YouTube API
        window.onYouTubeIframeAPIReady = function() {
            debugLog('YouTube iframe API ready');
            apiLoaded = true;
            initializePlayer();
        };
        
        function initializePlayer() {
            if (fallbackMode) return;
            
            try {
                debugLog('Initializing YouTube player...');
                player = new YT.Player('youtube-player', {
                    height: '100%',
                    width: '100%',
                    videoId: videoId,
                    playerVars: {
                        'enablejsapi': 1,
                        'rel': 0,
                        'modestbranding': 1,
                        'fs': 1,
                        'cc_load_policy': 0,
                        'iv_load_policy': 3,
                        'autohide': 0,
                        'origin': window.location.origin
                    },
                    events: {
                        'onReady': onPlayerReady,
                        'onError': onPlayerError,
                        'onStateChange': onPlayerStateChange
                    }
                });
            } catch (error) {
                debugLog(`Player initialization failed: ${{error.message}}`);
                fallbackMode = true;
                setupFallbackMode();
            }
        }
        
        function onPlayerReady(event) {
            debugLog('Player ready');
            playerReady = true;
            hideLoadingState();
            setupCardClickHandlers();
            
            // If there was a pending seek request, execute it now
            if (pendingSeek !== null) {
                debugLog(`Executing pending seek to ${{pendingSeek}}s`);
                seekToTime(pendingSeek);
                pendingSeek = null;
            }
            
            // Test player functionality
            testPlayerFunctionality();
        }
        
        function onPlayerError(event) {
            debugLog(`Player error: ${{event.data}}`);
            playerReady = false;
            
            // Error codes: 2=invalid video ID, 5=HTML5 error, 100=video not found, 101/150=embedding disabled
            if ([2, 100, 101, 150].includes(event.data)) {
                debugLog('Video embedding disabled or not found, switching to fallback');
                fallbackMode = true;
                setupFallbackMode();
            } else if (retryCount < maxRetries) {
                retryCount++;
                debugLog(`Retrying player initialization (attempt ${{retryCount}}/${{maxRetries}})`);
                setTimeout(() => {
                    initializePlayer();
                }, 2000);
            } else {
                debugLog('Max retries reached, switching to fallback');
                fallbackMode = true;
                setupFallbackMode();
            }
        }
        
        function onPlayerStateChange(event) {
            debugLog(`Player state changed: ${{event.data}}`);
        }
        
        function testPlayerFunctionality() {
            if (!playerReady || !player) return;
            
            try {
                // Test if we can call player methods
                const duration = player.getDuration();
                const currentTime = player.getCurrentTime();
                debugLog(`Player test - Duration: ${{duration}}s, Current: ${{currentTime}}s`);
                
                if (duration === undefined || isNaN(duration)) {
                    throw new Error('Player methods not accessible');
                }
            } catch (error) {
                debugLog(`Player functionality test failed: ${{error.message}}`);
                fallbackMode = true;
                setupFallbackMode();
            }
        }
        
        function setupFallbackMode() {
            debugLog('Setting up fallback mode');
            fallbackMode = true;
            playerReady = false;
            
            try {
                // Hide loading and show fallback message
                hideLoadingState();
                showVideoFallback();
                debugLog('Fallback UI updated successfully');
                
                // Setup click handlers for direct YouTube links
                setTimeout(() => {
                    try {
                        setupCardClickHandlers();
                        debugLog('Click handlers set up in fallback mode');
                    } catch (e) {
                        debugLog(`Error setting up fallback click handlers: ${e.message}`);
                    }
                }, 100);
                
            } catch (e) {
                debugLog(`Error in setupFallbackMode: ${e.message}`);
                // Force show fallback even if there are errors
                try {
                    const loading = document.getElementById('player-loading');
                    const fallback = document.getElementById('video-fallback');
                    if (loading) loading.style.display = 'none';
                    if (fallback) fallback.style.display = 'block';
                } catch (e2) {
                    debugLog(`Critical error showing fallback: ${e2.message}`);
                }
            }
        }
        
        function showVideoFallback() {
            const playerContainer = document.getElementById('youtube-player-container');
            const fallback = document.getElementById('video-fallback');
            const loading = document.getElementById('player-loading');
            
            if (playerContainer) {
                playerContainer.style.display = 'none';
            }
            if (loading) {
                loading.style.display = 'none';
            }
            if (fallback) {
                fallback.style.display = 'block';
                debugLog('Fallback message displayed');
            }
        }
        
        function seekToTime(seconds) {
            debugLog(`Seeking to ${{seconds}}s (playerReady: ${{playerReady}}, fallbackMode: ${{fallbackMode}})`);
            
            // Add visual feedback
            showSeekingFeedback(seconds);
            
            if (fallbackMode || !playerReady) {
                // Direct YouTube link with timestamp
                const youtubeUrl = `https://www.youtube.com/watch?v=${{videoId}}&t=${{Math.floor(seconds)}}s`;
                debugLog(`Opening YouTube directly: ${{youtubeUrl}}`);
                window.open(youtubeUrl, '_blank');
                return;
            }
            
            if (playerReady && player && typeof player.seekTo === 'function') {
                try {
                    debugLog(`Using player.seekTo(${{seconds}})`);
                    player.seekTo(seconds, true);
                    player.playVideo();
                    
                    // Verify the seek worked
                    setTimeout(() => {
                        try {
                            const currentTime = player.getCurrentTime();
                            const timeDiff = Math.abs(currentTime - seconds);
                            
                            if (timeDiff > 5) { // If we're more than 5 seconds off
                                debugLog(`Seek verification failed. Expected: ${{seconds}}s, Actual: ${{currentTime}}s`);
                                // Fall back to iframe src method
                                useIframeSrcSeek(seconds);
                            } else {
                                debugLog(`Seek successful. Target: ${{seconds}}s, Actual: ${{currentTime}}s`);
                            }
                        } catch (error) {
                            debugLog(`Seek verification error: ${{error.message}}`);
                            useIframeSrcSeek(seconds);
                        }
                    }, 1000);
                    
                } catch (error) {
                    debugLog(`seekTo failed: ${{error.message}}, trying iframe src method`);
                    useIframeSrcSeek(seconds);
                }
            } else {
                debugLog('Player not ready, storing pending seek');
                pendingSeek = seconds;
                
                // Try iframe src method as backup
                setTimeout(() => {
                    if (pendingSeek === seconds) { // Still pending
                        debugLog('Using iframe src method for pending seek');
                        useIframeSrcSeek(seconds);
                        pendingSeek = null;
                    }
                }, 2000);
            }
            
            // Scroll to video
            scrollToVideo();
        }
        
        function useIframeSrcSeek(seconds) {
            debugLog(`Using iframe src seek method for ${{seconds}}s`);
            
            try {
                const iframe = document.getElementById('youtube-player');
                if (iframe) {
                    const baseUrl = `https://www.youtube.com/embed/${{videoId}}`;
                    const params = new URLSearchParams({
                        'enablejsapi': '1',
                        'rel': '0',
                        'modestbranding': '1',
                        'fs': '1',
                        'cc_load_policy': '0',
                        'iv_load_policy': '3',
                        'autohide': '0',
                        'start': Math.floor(seconds),
                        'autoplay': '1',
                        'origin': window.location.origin
                    });
                    
                    const newSrc = `${{baseUrl}}?${{params.toString()}}`;
                    debugLog(`Setting iframe src: ${{newSrc}}`);
                    iframe.src = newSrc;
                }
            } catch (error) {
                debugLog(`Iframe src seek failed: ${{error.message}}`);
                // Ultimate fallback
                const youtubeUrl = `https://www.youtube.com/watch?v=${{videoId}}&t=${{Math.floor(seconds)}}s`;
                window.open(youtubeUrl, '_blank');
            }
        }
        
        function showSeekingFeedback(seconds) {
            // Create temporary feedback element
            const feedback = document.createElement('div');
            feedback.innerHTML = `🎬 Jumping to ${{formatTime(seconds)}}...`;
            feedback.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 10px 20px;
                border-radius: 25px;
                font-size: 14px;
                z-index: 10000;
                transition: opacity 0.3s;
            `;
            
            document.body.appendChild(feedback);
            
            // Remove after 2 seconds
            setTimeout(() => {
                feedback.style.opacity = '0';
                setTimeout(() => {
                    if (feedback.parentNode) {
                        feedback.parentNode.removeChild(feedback);
                    }
                }, 300);
            }, 2000);
        }
        
        function formatTime(seconds) {
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = Math.floor(seconds % 60);
            return `${{minutes}}:${{remainingSeconds.toString().padStart(2, '0')}}`;
        }
        
        function scrollToVideo() {
            const videoContainer = document.querySelector('.video-container');
            if (videoContainer) {
                videoContainer.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
            }
        }
        
        function setupCardClickHandlers() {
            debugLog('Setting up card click handlers');
            
            document.querySelectorAll('.highlight-card').forEach((card, index) => {
                // Remove existing listeners to prevent duplicates
                card.replaceWith(card.cloneNode(true));
            });
            
            // Re-select after cloning to get fresh elements
            document.querySelectorAll('.highlight-card').forEach((card, index) => {
                const timestamp = parseInt(card.getAttribute('data-timestamp'));
                
                if (isNaN(timestamp)) {
                    debugLog(`Warning: Invalid timestamp for card ${{index}}: ${{card.getAttribute('data-timestamp')}}`);
                    return;
                }
                
                card.addEventListener('click', function(e) {
                    // Don't intercept clicks on buttons or links
                    if (e.target.tagName === 'A' || e.target.tagName === 'BUTTON') {
                        return;
                    }
                    
                    e.preventDefault();
                    debugLog(`Card ${{index}} clicked, seeking to ${{timestamp}}s`);
                    
                    // Visual feedback - highlight active segment
                    highlightActiveSegment(card);
                    
                    seekToTime(timestamp);
                });
                
                // Also handle the watch button specifically
                const watchBtn = card.querySelector('.watch-btn');
                if (watchBtn) {
                    watchBtn.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        debugLog(`Watch button clicked for card ${{index}}, seeking to ${{timestamp}}s`);
                        highlightActiveSegment(card);
                        seekToTime(timestamp);
                    });
                }
            });
            
            debugLog(`Set up click handlers for ${{document.querySelectorAll('.highlight-card').length}} cards`);
        }
        
        function highlightActiveSegment(activeCard) {
            // Remove active class from all cards
            document.querySelectorAll('.highlight-card').forEach(card => {
                card.classList.remove('segment-active');
            });
            
            // Add active class to clicked card
            activeCard.classList.add('segment-active');
            
            // Remove active class after 3 seconds
            setTimeout(() => {
                activeCard.classList.remove('segment-active');
            }, 3000);
        }
        
        // Initialize everything when DOM is ready
        document.addEventListener('DOMContentLoaded', function() {
            debugLog('DOM ready, initializing video player');
            debugLog(`Video ID: ${videoId}`);
            
            // Immediate test - if we can't access basic web APIs, go to fallback
            try {
                if (!window.fetch || !window.Promise) {
                    debugLog('Basic web APIs missing, using fallback immediately');
                    fallbackMode = true;
                    setupFallbackMode();
                    return;
                }
            } catch (e) {
                debugLog('Error checking web APIs, using fallback immediately');
                fallbackMode = true;
                setupFallbackMode();
                return;
            }
            
            // Try to load YouTube API, but set up fallback quickly if it fails
            try {
                loadYouTubeAPI();
            } catch (e) {
                debugLog(`Error loading YouTube API: ${e.message}, using fallback`);
                fallbackMode = true;
                setupFallbackMode();
                return;
            }
            
            // Setup initial click handlers (in case API is slow)
            setTimeout(() => {
                try {
                    setupCardClickHandlers();
                } catch (e) {
                    debugLog(`Error setting up click handlers: ${e.message}`);
                }
            }, 1000);
            
            // Very quick fallback - 1 second
            setTimeout(() => {
                if (!playerReady && !fallbackMode) {
                    debugLog('Player still not ready after 1 second, enabling fallback');
                    fallbackMode = true;
                    setupFallbackMode();
                }
            }, 1000);
            
            // Quick fallback if nothing works
            setTimeout(() => {
                if (!playerReady && !fallbackMode) {
                    debugLog('Player still not ready after 3 seconds, enabling fallback');
                    fallbackMode = true;
                    setupFallbackMode();
                }
            }, 3000);
            
            // Additional safety net
            setTimeout(() => {
                if (!playerReady && !fallbackMode) {
                    debugLog('Player still not ready after 8 seconds, enabling fallback');
                    fallbackMode = true;
                    setupFallbackMode();
                }
            }, 8000);
        });
        
        // Global debug function for testing
        window.debugVideoPlayer = function() {
            debugLog(`Debug info:
                - playerReady: ${{playerReady}}
                - fallbackMode: ${{fallbackMode}}
                - apiLoaded: ${{apiLoaded}}
                - retryCount: ${{retryCount}}
                - player exists: ${{!!player}}
                - pendingSeek: ${{pendingSeek}}
            `);
            
            if (player && playerReady) {
                try {
                    debugLog(`Player state: ${{player.getPlayerState()}}, Duration: ${{player.getDuration()}}s`);
                } catch (e) {
                    debugLog(`Error getting player info: ${{e.message}}`);
                }
            }
        };
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
