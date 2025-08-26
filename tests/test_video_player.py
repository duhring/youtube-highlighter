import pytest
from pathlib import Path
import tempfile
import shutil
from app.html_generator import HTMLGenerator


class TestVideoPlayerEnhancements:
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.generator = HTMLGenerator(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_html_contains_enhanced_player_features(self):
        """Test that HTML contains all enhanced video player features"""
        youtube_url = 'https://www.youtube.com/watch?v=test123'
        video_title = 'Test Video'
        description = 'Test Highlights'
        segments = [
            {'start': 10.0, 'end': 15.0, 'text': 'Test segment', 'summary': 'Test'},
        ]
        thumbnails = [None]
        
        html_path = self.generator.generate(youtube_url, video_title, description, segments, thumbnails)
        html_content = Path(html_path).read_text()
        
        # Check for enhanced player features
        assert 'youtube-player-container' in html_content
        assert 'debugLog' in html_content
        assert 'loadYouTubeAPI' in html_content
        assert 'onYouTubeIframeAPIReady' in html_content
        assert 'fallbackMode' in html_content
        assert 'playerReady' in html_content
        assert 'pendingSeek' in html_content
        assert 'retryCount' in html_content
    
    def test_html_contains_error_handling(self):
        """Test that HTML contains comprehensive error handling"""
        youtube_url = 'https://www.youtube.com/watch?v=test123'
        segments = [{'start': 10.0, 'end': 15.0, 'text': 'Test'}]
        
        html_path = self.generator.generate(youtube_url, 'Test', 'Test', segments, [None])
        html_content = Path(html_path).read_text()
        
        # Check for error handling features
        assert 'onPlayerError' in html_content
        assert 'setupFallbackMode' in html_content
        assert 'testPlayerFunctionality' in html_content
        assert 'API loading timeout' in html_content
        assert 'Max retries reached' in html_content
    
    def test_html_contains_multiple_seek_methods(self):
        """Test that HTML contains multiple seek fallback methods"""
        youtube_url = 'https://www.youtube.com/watch?v=test123'
        segments = [{'start': 30.0, 'end': 45.0, 'text': 'Test segment'}]
        
        html_path = self.generator.generate(youtube_url, 'Test', 'Test', segments, [None])
        html_content = Path(html_path).read_text()
        
        # Check for multiple seek methods
        assert 'seekToTime' in html_content
        assert 'player.seekTo' in html_content
        assert 'useIframeSrcSeek' in html_content
        assert 'iframe.src' in html_content
        assert 'window.open' in html_content
        assert 'Seek verification' in html_content
    
    def test_html_contains_visual_feedback(self):
        """Test that HTML contains visual feedback features"""
        youtube_url = 'https://www.youtube.com/watch?v=test123'
        segments = [{'start': 60.0, 'end': 75.0, 'text': 'Test segment'}]
        
        html_path = self.generator.generate(youtube_url, 'Test', 'Test', segments, [None])
        html_content = Path(html_path).read_text()
        
        # Check for visual feedback features
        assert 'showSeekingFeedback' in html_content
        assert 'highlightActiveSegment' in html_content
        assert 'segment-active' in html_content
        assert 'showLoadingState' in html_content
        assert 'hideLoadingState' in html_content
        assert 'player-loading' in html_content
    
    def test_segment_timestamps_properly_embedded(self):
        """Test that segment timestamps are properly embedded in HTML"""
        youtube_url = 'https://www.youtube.com/watch?v=test123'
        segments = [
            {'start': 10.5, 'end': 25.0, 'text': 'First segment'},
            {'start': 45.7, 'end': 60.0, 'text': 'Second segment'},
            {'start': 120.0, 'end': 135.0, 'text': 'Third segment'}
        ]
        
        html_path = self.generator.generate(youtube_url, 'Test', 'Test', segments, [None] * 3)
        html_content = Path(html_path).read_text()
        
        # Check that timestamps are properly converted to integers and embedded
        assert 'data-timestamp="10"' in html_content
        assert 'data-timestamp="45"' in html_content  
        assert 'data-timestamp="120"' in html_content
        
        # Check that formatted timestamps are displayed
        assert '00:10' in html_content  # 10 seconds
        assert '00:45' in html_content  # 45 seconds
        assert '02:00' in html_content  # 120 seconds
    
    def test_html_contains_debug_functionality(self):
        """Test that HTML contains debug functionality for troubleshooting"""
        youtube_url = 'https://www.youtube.com/watch?v=test123'
        segments = [{'start': 30.0, 'end': 45.0, 'text': 'Test'}]
        
        html_path = self.generator.generate(youtube_url, 'Test', 'Test', segments, [None])
        html_content = Path(html_path).read_text()
        
        # Check for debug features
        assert 'window.debugVideoPlayer' in html_content
        assert '[VideoPlayer]' in html_content
        assert 'debugLog' in html_content
    
    def test_html_contains_loading_states(self):
        """Test that HTML contains proper loading state management"""
        youtube_url = 'https://www.youtube.com/watch?v=test123'
        segments = [{'start': 30.0, 'end': 45.0, 'text': 'Test'}]
        
        html_path = self.generator.generate(youtube_url, 'Test', 'Test', segments, [None])
        html_content = Path(html_path).read_text()
        
        # Check for loading state elements
        assert 'player-loading' in html_content
        assert 'Loading video player' in html_content
        assert '@keyframes loading' in html_content
        assert 'showLoadingState' in html_content
        assert 'hideLoadingState' in html_content
    
    def test_video_id_extraction(self):
        """Test that video ID is properly extracted and used"""
        youtube_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        segments = [{'start': 30.0, 'end': 45.0, 'text': 'Test'}]
        
        html_path = self.generator.generate(youtube_url, 'Test', 'Test', segments, [None])
        html_content = Path(html_path).read_text()
        
        # Check that video ID is properly embedded
        assert 'dQw4w9WgXcQ' in html_content
        assert "let videoId = 'dQw4w9WgXcQ'" in html_content
    
    def test_fallback_message_content(self):
        """Test that fallback message is informative"""
        youtube_url = 'https://www.youtube.com/watch?v=test123'
        segments = [{'start': 30.0, 'end': 45.0, 'text': 'Test'}]
        
        html_path = self.generator.generate(youtube_url, 'Test', 'Test', segments, [None])
        html_content = Path(html_path).read_text()
        
        # Check fallback message content
        assert 'Video embedding is disabled' in html_content
        assert 'Click a segment below to open it directly on YouTube' in html_content
        assert 'Watch Full Video on YouTube' in html_content
    
    def test_click_handler_setup(self):
        """Test that click handlers are properly set up"""
        youtube_url = 'https://www.youtube.com/watch?v=test123'
        segments = [
            {'start': 10.0, 'end': 15.0, 'text': 'First'},
            {'start': 30.0, 'end': 35.0, 'text': 'Second'}
        ]
        
        html_path = self.generator.generate(youtube_url, 'Test', 'Test', segments, [None] * 2)
        html_content = Path(html_path).read_text()
        
        # Check that click handlers are set up
        assert 'setupCardClickHandlers' in html_content
        assert 'addEventListener(\'click\',' in html_content
        assert 'watch-btn' in html_content
        assert 'preventDefault()' in html_content
    
    def test_css_animations_included(self):
        """Test that CSS animations are included for visual feedback"""
        youtube_url = 'https://www.youtube.com/watch?v=test123'
        segments = [{'start': 30.0, 'end': 45.0, 'text': 'Test'}]
        
        html_path = self.generator.generate(youtube_url, 'Test', 'Test', segments, [None])
        html_content = Path(html_path).read_text()
        
        # Check for CSS animations
        assert '@keyframes loading' in html_content
        assert 'segment-active' in html_content
        assert 'transform: translateX' in html_content
        assert 'transition:' in html_content