import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil
from app.transcript_downloader import TranscriptDownloader

@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def downloader(temp_cache_dir):
    """Create a TranscriptDownloader instance with temp cache"""
    return TranscriptDownloader(cache_dir=str(temp_cache_dir))

class TestTranscriptDownloader:
    
    def test_extract_video_id_standard_url(self, downloader):
        """Test video ID extraction from standard YouTube URL"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = downloader._extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"
    
    def test_extract_video_id_short_url(self, downloader):
        """Test video ID extraction from short YouTube URL"""
        url = "https://youtu.be/dQw4w9WgXcQ"
        video_id = downloader._extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"
    
    def test_extract_video_id_embed_url(self, downloader):
        """Test video ID extraction from embed URL"""
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        video_id = downloader._extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"
    
    def test_extract_video_id_invalid_url(self, downloader):
        """Test video ID extraction from invalid URL"""
        url = "https://www.example.com/not-a-youtube-url"
        video_id = downloader._extract_video_id(url)
        assert video_id is None
    
    def test_find_cached_transcript_exact_match(self, downloader, temp_cache_dir):
        """Test finding cached transcript with exact filename match"""
        # Create a cached file
        video_id = "test_video_123"
        cached_file = temp_cache_dir / f"{video_id}.vtt"
        cached_file.write_text("WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nTest content")
        
        result = downloader._find_cached_transcript(video_id)
        assert result == cached_file
    
    def test_find_cached_transcript_with_language(self, downloader, temp_cache_dir):
        """Test finding cached transcript with language suffix"""
        video_id = "test_video_123"
        cached_file = temp_cache_dir / f"{video_id}.en.vtt"
        cached_file.write_text("WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nTest content")
        
        result = downloader._find_cached_transcript(video_id)
        assert result == cached_file
    
    def test_find_cached_transcript_empty_file(self, downloader, temp_cache_dir):
        """Test that empty cached files are still found (validation happens later)"""
        video_id = "test_video_123"
        empty_file = temp_cache_dir / f"{video_id}.vtt"
        empty_file.touch()  # Create empty file
        
        result = downloader._find_cached_transcript(video_id)
        assert result == empty_file  # Empty files are found, but validation will catch them
    
    def test_find_cached_transcript_no_match(self, downloader):
        """Test finding cached transcript when none exists"""
        video_id = "nonexistent_video"
        result = downloader._find_cached_transcript(video_id)
        assert result is None
    
    def test_validate_transcript_file_valid_vtt(self, downloader, temp_cache_dir):
        """Test validation of valid VTT file"""
        vtt_file = temp_cache_dir / "test.vtt"
        vtt_file.write_text("WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nValid content")
        
        result = downloader._validate_transcript_file(vtt_file)
        assert result is True
    
    def test_validate_transcript_file_valid_srt(self, downloader, temp_cache_dir):
        """Test validation of valid SRT file"""
        srt_file = temp_cache_dir / "test.srt"
        srt_file.write_text("1\n00:00:01,000 --> 00:00:03,000\nValid content")
        
        result = downloader._validate_transcript_file(srt_file)
        assert result is True
    
    def test_validate_transcript_file_empty(self, downloader, temp_cache_dir):
        """Test validation of empty file (should be removed)"""
        empty_file = temp_cache_dir / "test.vtt"
        empty_file.touch()
        
        result = downloader._validate_transcript_file(empty_file)
        assert result is False
        assert not empty_file.exists()  # Should be removed
    
    def test_validate_transcript_file_invalid_vtt(self, downloader, temp_cache_dir):
        """Test validation of invalid VTT file"""
        invalid_file = temp_cache_dir / "test.vtt"
        invalid_file.write_text("This is not a valid VTT file")
        
        result = downloader._validate_transcript_file(invalid_file)
        assert result is False
    
    @patch('subprocess.run')
    def test_execute_ytdlp_command_success(self, mock_run, downloader, temp_cache_dir):
        """Test successful yt-dlp command execution"""
        # Mock successful subprocess run
        mock_result = Mock()
        mock_result.stdout = "Download completed"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Create a file that would be "downloaded"
        video_id = "test_video"
        downloaded_file = temp_cache_dir / f"{video_id}.en.vtt"
        downloaded_file.write_text("WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nTest")
        
        cmd = ["yt-dlp", "--skip-download", "test_url"]
        result = downloader._execute_ytdlp_command(cmd, video_id)
        
        assert result == str(downloaded_file)
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_execute_ytdlp_command_no_subtitles(self, mock_run, downloader):
        """Test yt-dlp command when no subtitles are available"""
        # Mock subprocess run that indicates no subtitles
        mock_result = Mock()
        mock_result.stdout = "There are no subtitles for the requested languages"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        cmd = ["yt-dlp", "--skip-download", "test_url"]
        result = downloader._execute_ytdlp_command(cmd, "test_video")
        
        assert result is None
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_execute_ytdlp_command_timeout(self, mock_run, downloader):
        """Test yt-dlp command timeout handling"""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("yt-dlp", 120)
        
        cmd = ["yt-dlp", "--skip-download", "test_url"]
        result = downloader._execute_ytdlp_command(cmd, "test_video")
        
        assert result is None
    
    def test_clear_cache_specific_video(self, downloader, temp_cache_dir):
        """Test clearing cache for specific video"""
        video_id = "test_video_123"
        
        # Create some test files
        file1 = temp_cache_dir / f"{video_id}.vtt"
        file2 = temp_cache_dir / f"{video_id}.en.vtt"
        file3 = temp_cache_dir / "other_video.vtt"
        
        for f in [file1, file2, file3]:
            f.write_text("test content")
        
        # Clear cache for specific video
        downloader.clear_cache(video_id)
        
        # Check that only the specific video files were removed
        assert not file1.exists()
        assert not file2.exists()
        assert file3.exists()
    
    def test_clear_cache_all(self, downloader, temp_cache_dir):
        """Test clearing entire cache"""
        # Create test files
        files = [
            temp_cache_dir / "video1.vtt",
            temp_cache_dir / "video2.srt",
            temp_cache_dir / "video3.en.vtt",
            temp_cache_dir / "not_transcript.txt"  # Should not be removed
        ]
        
        for f in files:
            f.write_text("test content")
        
        # Clear entire cache
        downloader.clear_cache()
        
        # Check that transcript files were removed but other files remain
        assert not files[0].exists()
        assert not files[1].exists() 
        assert not files[2].exists()
        assert files[3].exists()  # Non-transcript file should remain

    @patch.object(TranscriptDownloader, '_download_with_ytdlp_manual')
    @patch.object(TranscriptDownloader, '_download_with_ytdlp_auto')
    @patch.object(TranscriptDownloader, '_download_with_pytube')
    def test_download_transcript_fallback_strategies(self, mock_pytube, mock_ytdlp_auto, mock_ytdlp_manual, downloader):
        """Test that download_transcript tries multiple strategies"""
        # Mock all strategies to fail except the last one
        mock_ytdlp_manual.return_value = None
        mock_ytdlp_auto.return_value = None
        mock_pytube.return_value = "/path/to/transcript.srt"
        
        result = downloader.download_transcript("https://youtube.com/watch?v=test")
        
        # Should have tried all strategies
        mock_ytdlp_manual.assert_called_once()
        mock_ytdlp_auto.assert_called_once()
        mock_pytube.assert_called_once()
        
        assert result == "/path/to/transcript.srt"