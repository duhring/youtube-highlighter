import pytest
from unittest.mock import patch, mock_open
from pathlib import Path
from app.transcript_formatter import (
    TranscriptFormatter, 
    TranscriptFormat, 
    TranscriptSegment
)


class TestTranscriptFormatter:
    
    def setup_method(self):
        """Set up test fixtures"""
        self.formatter = TranscriptFormatter()
    
    def test_detect_vtt_format(self):
        """Test VTT format detection"""
        vtt_content = """WEBVTT

00:00:01.000 --> 00:00:03.000
Hello world

00:00:04.000 --> 00:00:06.000
Welcome to the video"""
        
        format_type, confidence = self.formatter.detect_format(vtt_content)
        assert format_type == TranscriptFormat.VTT
        assert confidence > 0.6
    
    def test_detect_srt_format(self):
        """Test SRT format detection"""
        srt_content = """1
00:00:01,000 --> 00:00:03,000
Hello world

2
00:00:04,000 --> 00:00:06,000
Welcome to the video"""
        
        format_type, confidence = self.formatter.detect_format(srt_content)
        assert format_type == TranscriptFormat.SRT
        assert confidence >= 0.7
    
    def test_detect_youtube_format(self):
        """Test YouTube copy-paste format detection"""
        youtube_content = """0:00 Hello world
0:15 Welcome to the video
1:30 This is important
2:45 Let's continue"""
        
        format_type, confidence = self.formatter.detect_format(youtube_content)
        assert format_type == TranscriptFormat.YOUTUBE_COPY_PASTE
        assert confidence > 0.6
    
    def test_detect_youtube_format_with_hours(self):
        """Test YouTube format with hours"""
        youtube_content = """0:00:00 Hello world
0:00:15 Welcome to the video
0:01:30 This is important
0:02:45 Let's continue"""
        
        format_type, confidence = self.formatter.detect_format(youtube_content)
        assert format_type == TranscriptFormat.YOUTUBE_COPY_PASTE
        assert confidence > 0.6
    
    def test_detect_plain_text_format(self):
        """Test plain text format detection"""
        plain_content = """Hello world. Welcome to the video. 
        This is important information that we need to cover.
        Let's continue with the tutorial."""
        
        format_type, confidence = self.formatter.detect_format(plain_content)
        assert format_type == TranscriptFormat.PLAIN_TEXT
        assert confidence == 0.5
    
    def test_detect_json_format(self):
        """Test JSON format detection"""
        json_content = """[
    {"start": 0, "end": 3, "text": "Hello world"},
    {"start": 4, "end": 7, "text": "Welcome to the video"}
]"""
        
        format_type, confidence = self.formatter.detect_format(json_content)
        assert format_type == TranscriptFormat.JSON_TIMESTAMPS
        assert confidence > 0.6
    
    def test_detect_empty_content(self):
        """Test empty content detection"""
        format_type, confidence = self.formatter.detect_format("")
        assert format_type == TranscriptFormat.UNKNOWN
        assert confidence == 0.0
    
    def test_parse_vtt_segments(self):
        """Test parsing VTT format to segments"""
        vtt_content = """WEBVTT

00:00:01.000 --> 00:00:03.000
Hello world

00:00:04.500 --> 00:00:06.200
Welcome to the video"""
        
        segments = self.formatter.parse_to_segments(vtt_content, TranscriptFormat.VTT)
        
        assert len(segments) == 2
        assert segments[0].start == 1.0
        assert segments[0].end == 3.0
        assert segments[0].text == "Hello world"
        assert segments[1].start == 4.5
        assert segments[1].end == 6.2
        assert segments[1].text == "Welcome to the video"
    
    def test_parse_srt_segments(self):
        """Test parsing SRT format to segments"""
        srt_content = """1
00:00:01,000 --> 00:00:03,000
Hello world

2
00:00:04,500 --> 00:00:06,200
Welcome to the video"""
        
        segments = self.formatter.parse_to_segments(srt_content, TranscriptFormat.SRT)
        
        assert len(segments) == 2
        assert segments[0].start == 1.0
        assert segments[0].end == 3.0
        assert segments[0].text == "Hello world"
        assert segments[1].start == 4.5
        assert segments[1].end == 6.2
        assert segments[1].text == "Welcome to the video"
    
    def test_parse_youtube_segments(self):
        """Test parsing YouTube format to segments"""
        youtube_content = """0:00 Hello world
0:15 Welcome to the video
1:30 This is important"""
        
        segments = self.formatter.parse_to_segments(youtube_content, TranscriptFormat.YOUTUBE_COPY_PASTE)
        
        assert len(segments) == 3
        assert segments[0].start == 0.0
        assert segments[0].end == 15.0
        assert segments[0].text == "Hello world"
        assert segments[1].start == 15.0
        assert segments[1].end == 90.0
        assert segments[1].text == "Welcome to the video"
        assert segments[2].start == 90.0
        assert segments[2].end == 93.0  # +3 seconds default
        assert segments[2].text == "This is important"
    
    def test_parse_plain_text_segments(self):
        """Test parsing plain text to segments"""
        plain_content = "Hello world. Welcome to the video. This is important."
        
        segments = self.formatter.parse_to_segments(plain_content, TranscriptFormat.PLAIN_TEXT)
        
        assert len(segments) == 3
        assert segments[0].text == "Hello world."
        assert segments[1].text == "Welcome to the video."
        assert segments[2].text == "This is important."
        # Check timing progression
        assert segments[0].start == 0.0
        assert segments[1].start == segments[0].end
        assert segments[2].start == segments[1].end
    
    def test_parse_json_segments(self):
        """Test parsing JSON format to segments"""
        json_content = """[
    {"start": 0, "end": 3, "text": "Hello world"},
    {"start": 4, "end": 7, "text": "Welcome to the video"}
]"""
        
        segments = self.formatter.parse_to_segments(json_content, TranscriptFormat.JSON_TIMESTAMPS)
        
        assert len(segments) == 2
        assert segments[0].start == 0.0
        assert segments[0].end == 3.0
        assert segments[0].text == "Hello world"
        assert segments[1].start == 4.0
        assert segments[1].end == 7.0
        assert segments[1].text == "Welcome to the video"
    
    def test_convert_to_vtt(self):
        """Test converting any format to VTT"""
        youtube_content = """0:00 Hello world
0:15 Welcome to the video"""
        
        vtt_output = self.formatter.convert_to_vtt(youtube_content)
        
        assert vtt_output.startswith("WEBVTT")
        assert "00:00:00.000 --> 00:00:15.000" in vtt_output
        assert "Hello world" in vtt_output
        assert "00:00:15.000 --> 00:00:18.000" in vtt_output
        assert "Welcome to the video" in vtt_output
    
    def test_time_parsing_edge_cases(self):
        """Test various time format parsing edge cases"""
        # Test different VTT time formats
        test_cases = [
            ("00:01:30.500", 90.5),
            ("1:30.500", 90.5),
            ("0:05", 5.0),
            ("1:23:45", 5025.0),
        ]
        
        for time_str, expected_seconds in test_cases:
            result = self.formatter._parse_time_string(time_str)
            assert result == expected_seconds
    
    def test_youtube_timestamp_parsing(self):
        """Test YouTube timestamp parsing"""
        test_cases = [
            ("0:00", 0.0),
            ("1:23", 83.0),
            ("1:23:45", 5025.0),
        ]
        
        for timestamp_str, expected_seconds in test_cases:
            result = self.formatter._parse_youtube_timestamp(timestamp_str)
            assert result == expected_seconds
    
    def test_segments_to_vtt(self):
        """Test converting segments to VTT format"""
        segments = [
            TranscriptSegment(0.0, 3.0, "Hello world"),
            TranscriptSegment(4.5, 7.2, "Welcome to the video")
        ]
        
        vtt_output = self.formatter.segments_to_vtt(segments)
        
        assert vtt_output.startswith("WEBVTT")
        assert "00:00:00.000 --> 00:00:03.000" in vtt_output
        assert "Hello world" in vtt_output
        assert "00:00:04.500 --> 00:00:07.200" in vtt_output
        assert "Welcome to the video" in vtt_output
    
    def test_format_info(self):
        """Test getting format information"""
        info = self.formatter.get_format_info(TranscriptFormat.VTT)
        
        assert info["name"] == "WebVTT"
        assert "format" in info["description"].lower()
        assert "WEBVTT" in info["example"]
    
    def test_malformed_vtt(self):
        """Test handling malformed VTT content"""
        malformed_vtt = """WEBVTT

Invalid timestamp line
Hello world

00:00:04.000 --> 00:00:06.000
Valid segment"""
        
        segments = self.formatter.parse_to_segments(malformed_vtt, TranscriptFormat.VTT)
        
        # Should still parse the valid segment
        assert len(segments) == 1
        assert segments[0].text == "Valid segment"
    
    def test_malformed_srt(self):
        """Test handling malformed SRT content"""
        malformed_srt = """1
Invalid timestamp
Hello world

2
00:00:04,000 --> 00:00:06,000
Valid segment"""
        
        segments = self.formatter.parse_to_segments(malformed_srt, TranscriptFormat.SRT)
        
        # Should still parse the valid segment
        assert len(segments) == 1
        assert segments[0].text == "Valid segment"
    
    def test_mixed_youtube_formats(self):
        """Test handling mixed YouTube timestamp formats"""
        mixed_content = """0:00 First segment
0:15 Second segment
1:23:45 Third segment with hours
2:30 Fourth segment"""
        
        segments = self.formatter.parse_to_segments(mixed_content, TranscriptFormat.YOUTUBE_COPY_PASTE)
        
        assert len(segments) == 4
        assert segments[0].start == 0.0
        assert segments[1].start == 15.0
        assert segments[2].start == 5025.0  # 1:23:45
        assert segments[3].start == 150.0   # 2:30
    
    def test_confidence_scoring(self):
        """Test confidence scoring for different formats"""
        # Good confidence VTT
        vtt_content = "WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nTest"
        _, confidence = self.formatter.detect_format(vtt_content)
        assert confidence == 0.5  # Exact confidence for this simple case
        
        # High confidence YouTube (100% match)
        youtube_content = "0:00 Test\n0:15 Another"
        _, confidence = self.formatter.detect_format(youtube_content)
        assert confidence == 1.0
        
        # Low confidence plain text
        plain_content = "Just some random text without any timing"
        _, confidence = self.formatter.detect_format(plain_content)
        assert confidence == 0.5