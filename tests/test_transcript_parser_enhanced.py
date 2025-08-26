import pytest
from unittest.mock import patch, mock_open, Mock
from pathlib import Path
import tempfile
import shutil
from app.transcript import TranscriptParser
from app.transcript_formatter import TranscriptFormat


class TestTranscriptParserEnhanced:
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_parse_with_formatter_vtt(self):
        """Test parsing VTT file with enhanced formatter"""
        vtt_content = """WEBVTT

00:00:01.000 --> 00:00:03.000
Hello world

00:00:04.000 --> 00:00:06.000
Welcome to the video"""
        
        test_file = self.temp_path / "test.vtt"
        test_file.write_text(vtt_content, encoding='utf-8')
        
        segments = TranscriptParser.parse(test_file)
        
        assert len(segments) == 2
        assert segments[0]['start'] == 1.0
        assert segments[0]['end'] == 3.0
        assert segments[0]['text'] == "Hello world"
        assert segments[1]['start'] == 4.0
        assert segments[1]['end'] == 6.0
        assert segments[1]['text'] == "Welcome to the video"
    
    def test_parse_with_formatter_youtube_format(self):
        """Test parsing YouTube copy-paste format"""
        youtube_content = """0:00 Hello world
0:15 Welcome to the video
1:30 This is important"""
        
        test_file = self.temp_path / "test.txt"
        test_file.write_text(youtube_content, encoding='utf-8')
        
        segments = TranscriptParser.parse(test_file)
        
        assert len(segments) == 3
        assert segments[0]['start'] == 0.0
        assert segments[0]['text'] == "Hello world"
        assert segments[1]['start'] == 15.0
        assert segments[1]['text'] == "Welcome to the video"
        assert segments[2]['start'] == 90.0
        assert segments[2]['text'] == "This is important"
    
    def test_parse_fallback_to_legacy(self):
        """Test fallback to legacy parsing when formatter fails"""
        # Create a file that might confuse the formatter but work with legacy
        vtt_content = """WEBVTT

00:00:01.000 --> 00:00:03.000
Hello world"""
        
        test_file = self.temp_path / "test.vtt"
        test_file.write_text(vtt_content, encoding='utf-8')
        
        # Mock the formatter to fail
        with patch('app.transcript.TranscriptParser._parse_with_formatter') as mock_formatter:
            mock_formatter.return_value = []
            
            segments = TranscriptParser.parse(test_file)
            
            # Should fallback to legacy parsing
            assert len(segments) == 1
            assert segments[0]['text'] == "Hello world"
    
    def test_parse_file_not_found(self):
        """Test parsing non-existent file"""
        non_existent_file = self.temp_path / "doesnt_exist.vtt"
        
        with pytest.raises(FileNotFoundError):
            TranscriptParser.parse(non_existent_file)
    
    def test_parse_empty_file(self):
        """Test parsing empty file"""
        empty_file = self.temp_path / "empty.vtt"
        empty_file.write_text("", encoding='utf-8')
        
        with pytest.raises(ValueError, match="empty"):
            TranscriptParser.parse(empty_file)
    
    def test_read_file_with_encoding_detection_utf8(self):
        """Test reading UTF-8 file"""
        content = "Hello 世界"
        test_file = self.temp_path / "utf8.txt"
        test_file.write_text(content, encoding='utf-8')
        
        result = TranscriptParser._read_file_with_encoding_detection(test_file)
        assert result == content
    
    def test_read_file_with_encoding_detection_latin1(self):
        """Test reading Latin-1 file"""
        content = "Café"
        test_file = self.temp_path / "latin1.txt"
        test_file.write_bytes(content.encode('latin-1'))
        
        result = TranscriptParser._read_file_with_encoding_detection(test_file)
        assert result == content
    
    def test_read_file_with_encoding_detection_fallback(self):
        """Test reading file with encoding issues using fallback"""
        # Create file with mixed encoding issues
        test_file = self.temp_path / "mixed.txt"
        with open(test_file, 'wb') as f:
            f.write(b'Hello \xff\xfe world')  # Invalid UTF-8 bytes
        
        # Should fallback to replacement characters
        result = TranscriptParser._read_file_with_encoding_detection(test_file)
        assert "Hello" in result
        assert "world" in result
    
    def test_read_file_completely_unreadable(self):
        """Test reading completely unreadable file"""
        test_file = self.temp_path / "unreadable.txt"
        
        # Mock all file operations to fail
        with patch('builtins.open', side_effect=Exception("Cannot read file")):
            with pytest.raises(ValueError, match="Could not read file"):
                TranscriptParser._read_file_with_encoding_detection(test_file)
    
    def test_parse_with_formatter_confidence_too_low(self):
        """Test when formatter confidence is too low"""
        # Content that would have very low confidence
        low_confidence_content = "random text without any structure"
        
        test_file = self.temp_path / "low_conf.txt"
        test_file.write_text(low_confidence_content, encoding='utf-8')
        
        with patch('app.transcript_formatter.TranscriptFormatter.detect_format') as mock_detect:
            mock_detect.return_value = (TranscriptFormat.UNKNOWN, 0.1)
            
            # Should fall back to legacy parsing
            segments = TranscriptParser._parse_with_formatter(test_file)
            assert segments == []
    
    def test_parse_with_formatter_exception_handling(self):
        """Test exception handling in formatter parsing"""
        test_file = self.temp_path / "test.vtt"
        test_file.write_text("WEBVTT\n\ntest", encoding='utf-8')
        
        with patch('app.transcript_formatter.TranscriptFormatter.parse_to_segments') as mock_parse:
            mock_parse.side_effect = Exception("Parsing error")
            
            segments = TranscriptParser._parse_with_formatter(test_file)
            assert segments == []
    
    def test_validate_segments_basic(self):
        """Test basic segment validation"""
        segments = [
            {'start': 0.0, 'end': 3.0, 'text': 'Hello world'},
            {'start': 4.0, 'end': 7.0, 'text': 'Welcome'},
            {'start': 8.0, 'end': 8.0, 'text': 'Invalid duration'},  # Invalid
            {'start': -1.0, 'end': 2.0, 'text': 'Negative start'},    # Invalid
            {'start': 10.0, 'end': 9.0, 'text': 'End before start'}, # Invalid
        ]
        
        valid_segments = TranscriptParser.validate_segments(segments)
        
        assert len(valid_segments) == 2
        assert valid_segments[0]['text'] == 'Hello world'
        assert valid_segments[1]['text'] == 'Welcome'
    
    def test_validate_segments_empty_text(self):
        """Test validation with empty text segments"""
        segments = [
            {'start': 0.0, 'end': 3.0, 'text': 'Valid segment'},
            {'start': 4.0, 'end': 7.0, 'text': ''},     # Empty text
            {'start': 8.0, 'end': 11.0, 'text': '   '}, # Whitespace only
        ]
        
        valid_segments = TranscriptParser.validate_segments(segments)
        
        assert len(valid_segments) == 1
        assert valid_segments[0]['text'] == 'Valid segment'
    
    def test_validate_segments_overlap_removal(self):
        """Test removing overlapping segments"""
        segments = [
            {'start': 0.0, 'end': 5.0, 'text': 'First segment'},
            {'start': 3.0, 'end': 8.0, 'text': 'Overlapping segment'},
            {'start': 10.0, 'end': 15.0, 'text': 'Non-overlapping segment'},
        ]
        
        valid_segments = TranscriptParser.validate_segments(segments)
        
        # Should keep non-overlapping segments and handle overlaps
        assert len(valid_segments) >= 1
        assert any(seg['text'] == 'Non-overlapping segment' for seg in valid_segments)
    
    def test_parse_integration_with_various_formats(self):
        """Integration test with various formats"""
        formats_and_content = [
            ("test.vtt", "WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nVTT format"),
            ("test.srt", "1\n00:00:01,000 --> 00:00:03,000\nSRT format"),
            ("test.txt", "0:00 YouTube format"),
        ]
        
        for filename, content in formats_and_content:
            test_file = self.temp_path / filename
            test_file.write_text(content, encoding='utf-8')
            
            segments = TranscriptParser.parse(test_file)
            assert len(segments) >= 1
            assert 'start' in segments[0]
            assert 'end' in segments[0]
            assert 'text' in segments[0]
            assert segments[0]['text'].strip()  # Non-empty text
    
    def test_parse_malformed_but_recoverable(self):
        """Test parsing malformed but partially recoverable content"""
        malformed_vtt = """WEBVTT

This line has no timestamp
But this is valid

00:00:01.000 --> 00:00:03.000
Valid segment

Another invalid line

00:00:04.000 --> 00:00:06.000
Another valid segment"""
        
        test_file = self.temp_path / "malformed.vtt"
        test_file.write_text(malformed_vtt, encoding='utf-8')
        
        segments = TranscriptParser.parse(test_file)
        
        # Should recover the valid segments
        assert len(segments) >= 2
        valid_texts = [seg['text'] for seg in segments]
        assert 'Valid segment' in valid_texts
        assert 'Another valid segment' in valid_texts
    
    def test_parse_with_special_characters(self):
        """Test parsing content with special characters"""
        special_content = """WEBVTT

00:00:01.000 --> 00:00:03.000
Hello 世界! Café ñoño

00:00:04.000 --> 00:00:06.000
Émoji test: 🎬📝✨"""
        
        test_file = self.temp_path / "special.vtt"
        test_file.write_text(special_content, encoding='utf-8')
        
        segments = TranscriptParser.parse(test_file)
        
        assert len(segments) == 2
        assert '世界' in segments[0]['text']
        assert '🎬' in segments[1]['text']
    
    def test_parse_very_large_file_handling(self):
        """Test handling of large files (basic check)"""
        # Create content with many segments
        vtt_lines = ["WEBVTT", ""]
        for i in range(100):
            start_time = f"00:00:{i:02d}.000"
            end_time = f"00:00:{i+1:02d}.000"
            vtt_lines.extend([
                f"{start_time} --> {end_time}",
                f"Segment number {i}",
                ""
            ])
        
        large_content = "\n".join(vtt_lines)
        test_file = self.temp_path / "large.vtt"
        test_file.write_text(large_content, encoding='utf-8')
        
        segments = TranscriptParser.parse(test_file)
        
        assert len(segments) == 100
        assert segments[0]['text'] == "Segment number 0"
        assert segments[99]['text'] == "Segment number 99"