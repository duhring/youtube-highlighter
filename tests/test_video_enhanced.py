import pytest
from unittest.mock import patch, Mock, MagicMock
from pathlib import Path
import tempfile
import shutil
from PIL import Image
import numpy as np
from app.video import VideoProcessor


class TestVideoProcessorEnhanced:
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create temporary output directory
        self.temp_dir = tempfile.mkdtemp()
        self.processor = VideoProcessor(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_candidate_timestamps(self):
        """Test candidate timestamp generation"""
        segment = {'start': 10.0, 'end': 20.0}
        video_duration = 300.0
        
        candidates = self.processor._get_candidate_timestamps(segment, video_duration)
        
        assert len(candidates) <= 5
        assert all(0.1 <= t <= video_duration - 0.1 for t in candidates)
        assert 10.2 in candidates  # Start + 0.2 offset
        assert 15.0 in candidates  # Middle
        
        # Test with short segment
        short_segment = {'start': 5.0, 'end': 6.0}
        short_candidates = self.processor._get_candidate_timestamps(short_segment, video_duration)
        assert len(short_candidates) >= 2
        assert 5.2 in short_candidates
    
    def test_is_valid_frame(self):
        """Test frame quality validation"""
        # Test with valid frame
        valid_frame = np.random.randint(50, 200, (720, 1280, 3), dtype=np.uint8)
        assert self.processor._is_valid_frame(valid_frame) == True
        
        # Test with black frame
        black_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        assert self.processor._is_valid_frame(black_frame) == False
        
        # Test with white frame
        white_frame = np.full((720, 1280, 3), 255, dtype=np.uint8)
        assert self.processor._is_valid_frame(white_frame) == False
        
        # Test with solid color (low variation)
        solid_frame = np.full((720, 1280, 3), 128, dtype=np.uint8)
        assert self.processor._is_valid_frame(solid_frame) == False
        
        # Test with invalid shape
        invalid_frame = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        assert self.processor._is_valid_frame(invalid_frame) == False
        
        # Test with None
        assert self.processor._is_valid_frame(None) == False
    
    def test_resize_thumbnail(self):
        """Test thumbnail resizing with aspect ratio preservation"""
        # Create test image
        test_img = Image.new('RGB', (1920, 1080), (255, 0, 0))  # 16:9 aspect ratio
        
        resized = self.processor._resize_thumbnail(test_img)
        
        assert resized.size == (self.processor.thumbnail_width, self.processor.thumbnail_height)
        # Should have black bars on top/bottom for 16:9 to 16:9 conversion (if different sizes)
    
    def test_validate_cached_video_invalid_size(self):
        """Test cached video validation with invalid file size"""
        # Create tiny file
        test_file = Path(self.temp_dir) / "tiny_video.mp4"
        test_file.write_bytes(b"small")
        
        assert self.processor._validate_cached_video(test_file) == False
    
    def test_validate_cached_video_nonexistent(self):
        """Test cached video validation with non-existent file"""
        test_file = Path(self.temp_dir) / "nonexistent.mp4"
        
        assert self.processor._validate_cached_video(test_file) == False
    
    @patch('app.video.VideoFileClip')
    def test_validate_cached_video_invalid_duration(self, mock_clip):
        """Test cached video validation with invalid duration"""
        # Create file with valid size
        test_file = Path(self.temp_dir) / "invalid_duration.mp4"
        test_file.write_bytes(b"x" * 200000)  # 200KB
        
        # Mock VideoFileClip to return invalid duration
        mock_instance = MagicMock()
        mock_instance.__enter__.return_value = mock_instance
        mock_instance.duration = -1
        mock_clip.return_value = mock_instance
        
        assert self.processor._validate_cached_video(test_file) == False
    
    @patch('app.video.VideoFileClip')
    def test_validate_cached_video_frame_extraction_failure(self, mock_clip):
        """Test cached video validation with frame extraction failure"""
        # Create file with valid size
        test_file = Path(self.temp_dir) / "frame_fail.mp4"
        test_file.write_bytes(b"x" * 200000)  # 200KB
        
        # Mock VideoFileClip with valid duration but failing frame extraction
        mock_instance = MagicMock()
        mock_instance.__enter__.return_value = mock_instance
        mock_instance.duration = 100.0
        mock_instance.get_frame.side_effect = Exception("Frame extraction failed")
        mock_clip.return_value = mock_instance
        
        assert self.processor._validate_cached_video(test_file) == False
    
    @patch('app.video.VideoFileClip')
    def test_validate_cached_video_success(self, mock_clip):
        """Test successful cached video validation"""
        # Create file with valid size
        test_file = Path(self.temp_dir) / "valid_video.mp4"
        test_file.write_bytes(b"x" * 500000)  # 500KB
        
        # Mock VideoFileClip with successful validation
        mock_instance = MagicMock()
        mock_instance.__enter__.return_value = mock_instance
        mock_instance.duration = 100.0
        mock_instance.get_frame.return_value = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
        mock_clip.return_value = mock_instance
        
        assert self.processor._validate_cached_video(test_file) == True
    
    @patch('app.video.YouTube')
    def test_select_optimal_stream_exact_match(self, mock_youtube):
        """Test optimal stream selection with exact quality match"""
        # Mock YouTube object with streams
        mock_yt = Mock()
        mock_stream = Mock()
        mock_stream.resolution = "720p"
        mock_yt.streams.filter.return_value.first.return_value = mock_stream
        
        result = self.processor._select_optimal_stream(mock_yt)
        
        assert result == mock_stream
        mock_yt.streams.filter.assert_called_with(
            res="720p", progressive=True, file_extension='mp4'
        )
    
    @patch('app.video.YouTube')
    def test_select_optimal_stream_progressive_fallback(self, mock_youtube):
        """Test optimal stream selection with progressive fallback"""
        # Mock YouTube object with no exact match but progressive streams
        mock_yt = Mock()
        mock_yt.streams.filter.return_value.first.return_value = None  # No exact match
        
        mock_progressive_stream = Mock()
        mock_progressive_stream.resolution = "1080p"
        mock_yt.streams.filter.return_value.order_by.return_value.desc.return_value = [mock_progressive_stream]
        
        result = self.processor._select_optimal_stream(mock_yt)
        
        assert result == mock_progressive_stream
    
    def test_style_timestamp_thumbnail(self):
        """Test timestamp thumbnail styling"""
        # Create test image
        test_img = Image.new('RGB', (1280, 720), (100, 100, 100))
        segment = {'start': 65.5}  # 1:05.5
        
        styled = self.processor._style_timestamp_thumbnail(test_img, 1, segment, 65)
        
        assert styled.size == test_img.size
        assert styled.mode == 'RGB'
        # Should be different from original due to styling
        assert styled != test_img
    
    @patch('requests.get')
    def test_try_youtube_timestamp_thumbnails_success(self, mock_get):
        """Test YouTube timestamp thumbnail download success"""
        self.processor.video_id = "test123"
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        
        # Create test image data
        test_img = Image.new('RGB', (1280, 720), (255, 0, 0))
        import io
        img_bytes = io.BytesIO()
        test_img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        mock_response.content = img_bytes.getvalue()
        mock_get.return_value = mock_response
        
        segments = [
            {'start': 10.0, 'end': 15.0},
            {'start': 30.0, 'end': 35.0}
        ]
        
        result = self.processor._try_youtube_timestamp_thumbnails(segments)
        
        assert result is not None
        assert len(result) == 2
        # Check that files were created
        for i, thumbnail_path in enumerate(result):
            if thumbnail_path:
                assert Path(thumbnail_path).exists()
    
    @patch('requests.get')
    def test_try_youtube_timestamp_thumbnails_failure(self, mock_get):
        """Test YouTube timestamp thumbnail download failure"""
        self.processor.video_id = "test123"
        
        # Mock failed response
        mock_get.side_effect = Exception("Network error")
        
        segments = [{'start': 10.0, 'end': 15.0}]
        
        result = self.processor._try_youtube_timestamp_thumbnails(segments)
        
        assert result is None
    
    @patch('app.video.VideoFileClip')
    def test_extract_thumbnails_success(self, mock_clip):
        """Test successful thumbnail extraction from video"""
        # Create mock video file
        video_path = Path(self.temp_dir) / "test_video.mp4"
        video_path.write_bytes(b"x" * 1000000)  # 1MB file
        
        # Mock VideoFileClip
        mock_video = Mock()
        mock_video.duration = 100.0
        mock_video.fps = 30
        mock_video.get_frame.return_value = np.random.randint(50, 200, (720, 1280, 3), dtype=np.uint8)
        mock_clip.return_value = mock_video
        
        segments = [
            {'start': 10.0, 'end': 15.0},
            {'start': 30.0, 'end': 35.0}
        ]
        
        result = self.processor.extract_thumbnails(str(video_path), segments)
        
        assert len(result) == 2
        assert all(thumbnail is not None for thumbnail in result)
        # Check that thumbnail files exist
        for thumbnail_path in result:
            if thumbnail_path:
                assert Path(thumbnail_path).exists()
    
    @patch('app.video.VideoFileClip')
    def test_extract_thumbnails_partial_failure(self, mock_clip):
        """Test thumbnail extraction with some frames failing"""
        # Create mock video file
        video_path = Path(self.temp_dir) / "test_video.mp4"
        video_path.write_bytes(b"x" * 1000000)  # 1MB file
        
        # Mock VideoFileClip
        mock_video = Mock()
        mock_video.duration = 100.0
        mock_video.fps = 30
        
        # First call succeeds, second fails, third succeeds
        mock_video.get_frame.side_effect = [
            np.random.randint(50, 200, (720, 1280, 3), dtype=np.uint8),  # Success
            Exception("Frame extraction failed"),  # Failure
            np.random.randint(50, 200, (720, 1280, 3), dtype=np.uint8)   # Success
        ]
        mock_clip.return_value = mock_video
        
        segments = [
            {'start': 10.0, 'end': 15.0},
            {'start': 30.0, 'end': 35.0},
            {'start': 60.0, 'end': 65.0}
        ]
        
        result = self.processor.extract_thumbnails(str(video_path), segments)
        
        assert len(result) == 3
        # Should have at least some successful extractions
        successful_count = len([t for t in result if t is not None])
        assert successful_count > 0
    
    def test_extract_thumbnails_no_video(self):
        """Test thumbnail extraction with no video file"""
        segments = [{'start': 10.0, 'end': 15.0}]
        
        with patch.object(self.processor, '_fallback_thumbnail_generation') as mock_fallback:
            mock_fallback.return_value = [None]
            
            result = self.processor.extract_thumbnails(None, segments)
            
            mock_fallback.assert_called_once_with(segments)
            assert result == [None]
    
    def test_extract_thumbnails_invalid_video_file(self):
        """Test thumbnail extraction with invalid video file"""
        # Create tiny invalid file
        video_path = Path(self.temp_dir) / "invalid.mp4"
        video_path.write_bytes(b"tiny")
        
        segments = [{'start': 10.0, 'end': 15.0}]
        
        with patch.object(self.processor, '_fallback_thumbnail_generation') as mock_fallback:
            mock_fallback.return_value = [None]
            
            result = self.processor.extract_thumbnails(str(video_path), segments)
            
            mock_fallback.assert_called_once_with(segments)
            assert result == [None]
    
    def test_fallback_thumbnail_generation_order(self):
        """Test that fallback thumbnail generation tries methods in correct order"""
        self.processor.video_id = "test123"
        segments = [{'start': 10.0}]
        
        with patch.object(self.processor, '_try_youtube_timestamp_thumbnails') as mock_youtube:
            with patch.object(self.processor, '_generate_custom_thumbnails') as mock_custom:
                # First try YouTube thumbnails (success)
                mock_youtube.return_value = ['thumb1.png']
                
                result = self.processor._fallback_thumbnail_generation(segments)
                
                mock_youtube.assert_called_once_with(segments)
                mock_custom.assert_not_called()  # Should not be called if YouTube succeeds
                assert result == ['thumb1.png']
    
    def test_fallback_to_custom_thumbnails(self):
        """Test fallback to custom thumbnail generation"""
        self.processor.video_id = "test123"
        segments = [{'start': 10.0}]
        
        with patch.object(self.processor, '_try_youtube_timestamp_thumbnails') as mock_youtube:
            with patch.object(self.processor, '_generate_custom_thumbnails') as mock_custom:
                # YouTube thumbnails fail, custom succeeds
                mock_youtube.return_value = None
                mock_custom.return_value = ['custom1.png']
                
                result = self.processor._fallback_thumbnail_generation(segments)
                
                mock_youtube.assert_called_once_with(segments)
                mock_custom.assert_called_once_with(segments)
                assert result == ['custom1.png']