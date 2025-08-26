import pytest
from app.video import VideoProcessor
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np

@pytest.fixture
def video_processor(tmp_path):
    return VideoProcessor(output_dir=str(tmp_path))

def test_thumbnail_generation(video_processor, tmp_path):
    # Create a dummy video file
    dummy_video_path = tmp_path / "video.mp4"
    dummy_video_path.touch()

    # Mock the download_video method
    video_processor.download_video = MagicMock(return_value=(str(dummy_video_path), "Test Video"))

    segments = [{'start': 0, 'end': 2, 'text': 'test'}]
    
    # Mock the moviepy VideoFileClip
    with patch('app.video.VideoFileClip') as mock_clip:
        # Create a dummy frame (a 100x100 white image)
        dummy_frame = np.full((100, 100, 3), 255, dtype=np.uint8)
        mock_clip.return_value.get_frame.return_value = dummy_frame
        mock_clip.return_value.duration = 5

        thumbnails = video_processor.extract_thumbnails(str(dummy_video_path), segments)
    
        assert len(thumbnails) == 1
        assert Path(thumbnails[0]).exists()
