import pytest
from unittest.mock import patch, Mock, MagicMock
from pathlib import Path
import json
import tempfile
import shutil
from app.transcript_downloader import TranscriptDownloader


class TestTranscriptDownloaderEnhanced:
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create temporary cache directory
        self.temp_dir = tempfile.mkdtemp()
        self.downloader = TranscriptDownloader(cache_dir=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_extract_video_id(self):
        """Test video ID extraction from various URL formats"""
        test_cases = [
            ("https://www.youtube.com/watch?v=abc123", "abc123"),
            ("https://youtu.be/def456", "def456"),
            ("https://www.youtube.com/embed/ghi789", "ghi789"),
            ("https://www.youtube.com/watch?v=jkl012&feature=share", "jkl012"),
            ("https://youtube.com/v/mno345", "mno345"),
            ("invalid_url", None),
        ]
        
        for url, expected_id in test_cases:
            result = self.downloader._extract_video_id(url)
            assert result == expected_id
    
    def test_find_cached_transcript(self):
        """Test finding cached transcript files"""
        video_id = "test123"
        
        # Create a test cache file
        cache_file = Path(self.temp_dir) / f"{video_id}.vtt"
        cache_file.write_text("WEBVTT\n\ntest content")
        
        result = self.downloader._find_cached_transcript(video_id)
        assert result == cache_file
        
        # Test with non-existent file
        result = self.downloader._find_cached_transcript("nonexistent")
        assert result is None
    
    def test_find_cached_transcript_empty_file(self):
        """Test that empty cache files are ignored"""
        video_id = "test123"
        
        # Create an empty cache file
        cache_file = Path(self.temp_dir) / f"{video_id}.vtt"
        cache_file.write_text("")
        
        result = self.downloader._find_cached_transcript(video_id)
        assert result is None
    
    @patch('requests.Session.get')
    def test_web_scraping_success(self, mock_get):
        """Test successful web scraping"""
        video_id = "test123"
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Mock response with transcript data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
        <script>
        var ytInitialPlayerResponse = {
            "captions": {
                "playerCaptionsTracklistRenderer": {
                    "captionTracks": [
                        {
                            "baseUrl": "https://www.youtube.com/api/timedtext?v=test123&lang=en&fmt=json3"
                        }
                    ]
                }
            }
        };
        </script>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with patch.object(self.downloader, '_extract_transcript_from_page') as mock_extract:
            mock_extract.return_value = [
                {'start': 0.0, 'end': 3.0, 'text': 'Hello world'}
            ]
            
            result = self.downloader._download_with_web_scraping(youtube_url, video_id)
            assert result is not None
            assert Path(result).exists()
    
    @patch('requests.Session.get')
    def test_web_scraping_failure(self, mock_get):
        """Test web scraping failure"""
        video_id = "test123"
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        
        mock_get.side_effect = Exception("Network error")
        
        result = self.downloader._download_with_web_scraping(youtube_url, video_id)
        assert result is None
    
    def test_parse_json3_format(self):
        """Test parsing JSON3 format transcript"""
        json3_content = json.dumps({
            "events": [
                {
                    "tStartMs": 0,
                    "dDurationMs": 3000,
                    "segs": [{"utf8": "Hello world"}]
                },
                {
                    "tStartMs": 3500,
                    "dDurationMs": 2500,
                    "segs": [{"utf8": "Welcome to the video"}]
                }
            ]
        })
        
        result = self.downloader._parse_json3_format(json3_content)
        
        assert len(result) == 2
        assert result[0]['start'] == 0.0
        assert result[0]['end'] == 3.0
        assert result[0]['text'] == "Hello world"
        assert result[1]['start'] == 3.5
        assert result[1]['end'] == 6.0
        assert result[1]['text'] == "Welcome to the video"
    
    def test_parse_srv3_format(self):
        """Test parsing SRV3 format transcript"""
        srv3_content = '''<?xml version="1.0"?>
        <transcript>
            <p t="0" d="3000">Hello world</p>
            <p t="3500" d="2500">Welcome to the video</p>
        </transcript>'''
        
        result = self.downloader._parse_srv3_format(srv3_content)
        
        assert len(result) == 2
        assert result[0]['start'] == 0.0
        assert result[0]['end'] == 3.0
        assert result[0]['text'] == "Hello world"
        assert result[1]['start'] == 3.5
        assert result[1]['end'] == 6.0
        assert result[1]['text'] == "Welcome to the video"
    
    def test_parse_xml_format(self):
        """Test parsing XML format transcript"""
        xml_content = '''<?xml version="1.0"?>
        <transcript>
            <text start="0" dur="3">Hello world</text>
            <text start="3.5" dur="2.5">Welcome to the video</text>
        </transcript>'''
        
        result = self.downloader._parse_xml_format(xml_content)
        
        assert len(result) == 2
        assert result[0]['start'] == 0.0
        assert result[0]['end'] == 3.0
        assert result[0]['text'] == "Hello world"
        assert result[1]['start'] == 3.5
        assert result[1]['end'] == 6.0
        assert result[1]['text'] == "Welcome to the video"
    
    def test_convert_transcript_data_to_vtt(self):
        """Test converting transcript data to VTT format"""
        transcript_data = [
            {'start': 0.0, 'end': 3.0, 'text': 'Hello world'},
            {'start': 4.5, 'end': 7.2, 'text': 'Welcome to the video'}
        ]
        
        vtt_content = self.downloader._convert_transcript_data_to_vtt(transcript_data)
        
        assert vtt_content.startswith("WEBVTT")
        assert "00:00:00.000 --> 00:00:03.000" in vtt_content
        assert "Hello world" in vtt_content
        assert "00:00:04.500 --> 00:00:07.200" in vtt_content
        assert "Welcome to the video" in vtt_content
    
    def test_seconds_to_vtt_time(self):
        """Test converting seconds to VTT time format"""
        test_cases = [
            (0.0, "00:00:00.000"),
            (65.5, "00:01:05.500"),
            (3661.123, "01:01:01.123"),
        ]
        
        for seconds, expected_time in test_cases:
            result = self.downloader._seconds_to_vtt_time(seconds)
            assert result == expected_time
    
    @patch('requests.get')
    def test_fetch_timedtext_url_json3(self, mock_get):
        """Test fetching transcript from timedtext URL with JSON3 format"""
        url = "https://www.youtube.com/api/timedtext?v=test123&lang=en&fmt=json3"
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({
            "events": [
                {
                    "tStartMs": 0,
                    "dDurationMs": 3000,
                    "segs": [{"utf8": "Hello world"}]
                }
            ]
        })
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.downloader._fetch_timedtext_url(url)
        
        assert len(result) == 1
        assert result[0]['text'] == "Hello world"
    
    def test_extract_transcript_from_page_no_match(self):
        """Test transcript extraction when no patterns match"""
        html_content = "<html><body>No transcript data here</body></html>"
        
        result = self.downloader._extract_transcript_from_page(html_content, "test123")
        assert result is None
    
    @patch('requests.Session.get')
    def test_try_transcript_api(self, mock_get):
        """Test trying transcript API"""
        session = Mock()
        video_id = "test123"
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "WEBVTT\n\n00:00:00.000 --> 00:00:03.000\nHello world"
        session.get.return_value = mock_response
        
        result = self.downloader._try_transcript_api(session, video_id)
        assert result is not None
        assert "WEBVTT" in result
    
    @patch('requests.Session.get')
    def test_try_transcript_api_failure(self, mock_get):
        """Test transcript API failure"""
        session = Mock()
        video_id = "test123"
        
        session.get.side_effect = Exception("API error")
        
        result = self.downloader._try_transcript_api(session, video_id)
        assert result is None
    
    def test_parse_transcript_match_url(self):
        """Test parsing transcript match with URL"""
        url = "https://www.youtube.com/api/timedtext?v=test123&lang=en&fmt=json3"
        
        with patch.object(self.downloader, '_fetch_timedtext_url') as mock_fetch:
            mock_fetch.return_value = [{'start': 0, 'end': 3, 'text': 'Test'}]
            
            result = self.downloader._parse_transcript_match(url, "test123")
            assert len(result) == 1
            assert result[0]['text'] == 'Test'
    
    def test_parse_transcript_match_json(self):
        """Test parsing transcript match with JSON"""
        json_data = '{"test": "data"}'
        
        with patch.object(self.downloader, '_extract_from_json_data') as mock_extract:
            mock_extract.return_value = [{'start': 0, 'end': 3, 'text': 'Test'}]
            
            result = self.downloader._parse_transcript_match(json_data, "test123")
            assert len(result) == 1
            assert result[0]['text'] == 'Test'
    
    def test_parse_transcript_match_invalid(self):
        """Test parsing invalid transcript match"""
        invalid_data = "not a url or json"
        
        result = self.downloader._parse_transcript_match(invalid_data, "test123")
        assert result is None
    
    def test_clear_cache_specific_video(self):
        """Test clearing cache for specific video"""
        video_id = "test123"
        
        # Create test cache files
        cache_file1 = Path(self.temp_dir) / f"{video_id}.vtt"
        cache_file2 = Path(self.temp_dir) / f"{video_id}_auto.vtt"
        cache_file3 = Path(self.temp_dir) / "other_video.vtt"
        
        cache_file1.write_text("test1")
        cache_file2.write_text("test2")
        cache_file3.write_text("test3")
        
        self.downloader.clear_cache(video_id)
        
        # Should remove files for specific video but not others
        assert not cache_file1.exists()
        assert not cache_file2.exists()
        assert cache_file3.exists()
    
    def test_clear_cache_all(self):
        """Test clearing entire cache"""
        # Create test cache files
        cache_file1 = Path(self.temp_dir) / "video1.vtt"
        cache_file2 = Path(self.temp_dir) / "video2.srt"
        cache_file3 = Path(self.temp_dir) / "video3.txt"  # Non-transcript file
        
        cache_file1.write_text("test1")
        cache_file2.write_text("test2")
        cache_file3.write_text("test3")
        
        self.downloader.clear_cache()
        
        # Should remove transcript files but not others
        assert not cache_file1.exists()
        assert not cache_file2.exists()
        assert cache_file3.exists()  # Non-transcript files preserved
    
    @patch('subprocess.run')
    def test_execute_ytdlp_command_success(self, mock_run):
        """Test successful yt-dlp command execution"""
        mock_result = Mock()
        mock_result.stdout = "Downloaded successfully"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Create a mock downloaded file
        video_id = "test123"
        mock_file = Path(self.temp_dir) / f"{video_id}.vtt"
        mock_file.write_text("WEBVTT\n\ntest content")
        
        with patch.object(self.downloader, '_find_downloaded_file') as mock_find:
            mock_find.return_value = mock_file
            with patch.object(self.downloader, '_validate_transcript_file') as mock_validate:
                mock_validate.return_value = True
                
                cmd = ["yt-dlp", "--help"]
                result = self.downloader._execute_ytdlp_command(cmd, video_id)
                
                assert result == str(mock_file)
    
    @patch('subprocess.run')
    def test_execute_ytdlp_command_no_subtitles(self, mock_run):
        """Test yt-dlp command when no subtitles available"""
        mock_result = Mock()
        mock_result.stdout = "no subtitles available"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        cmd = ["yt-dlp", "--help"]
        result = self.downloader._execute_ytdlp_command(cmd, "test123")
        
        assert result is None
    
    @patch('subprocess.run')
    def test_execute_ytdlp_command_timeout(self, mock_run):
        """Test yt-dlp command timeout"""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("yt-dlp", 120)
        
        cmd = ["yt-dlp", "--help"]
        result = self.downloader._execute_ytdlp_command(cmd, "test123")
        
        assert result is None