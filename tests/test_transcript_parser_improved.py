import pytest
from pathlib import Path
from app.transcript import TranscriptParser
import tempfile

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    import tempfile
    import shutil
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)

class TestImprovedTranscriptParser:
    
    def test_parse_valid_vtt_file(self, temp_dir):
        """Test parsing a valid VTT file"""
        vtt_content = """WEBVTT
Kind: captions
Language: en

00:00:01.000 --> 00:00:03.000
This is the first caption.

00:00:04.000 --> 00:00:06.000
This is the second caption.

00:00:07.500 --> 00:00:10.200
Third caption with longer text.
"""
        vtt_file = temp_dir / "test.vtt"
        vtt_file.write_text(vtt_content)
        
        segments = TranscriptParser.parse(vtt_file)
        
        assert len(segments) == 3
        assert segments[0]['start'] == 1.0
        assert segments[0]['end'] == 3.0
        assert segments[0]['text'] == "This is the first caption."
        assert segments[2]['start'] == 7.5
        assert segments[2]['text'] == "Third caption with longer text."
    
    def test_parse_valid_srt_file(self, temp_dir):
        """Test parsing a valid SRT file"""
        srt_content = """1
00:00:01,000 --> 00:00:03,000
This is the first subtitle.

2
00:00:04,500 --> 00:00:07,200
This is the second subtitle.

3
00:00:08,000 --> 00:00:11,000
Third subtitle here.
"""
        srt_file = temp_dir / "test.srt"
        srt_file.write_text(srt_content)
        
        segments = TranscriptParser.parse(srt_file)
        
        assert len(segments) == 3
        assert segments[0]['start'] == 1.0
        assert segments[0]['end'] == 3.0
        assert segments[0]['text'] == "This is the first subtitle."
        assert segments[1]['start'] == 4.5
        assert segments[1]['end'] == 7.2
    
    def test_parse_vtt_with_html_tags(self, temp_dir):
        """Test parsing VTT file with HTML tags (should be removed)"""
        vtt_content = """WEBVTT

00:00:01.000 --> 00:00:03.000
This has <b>bold</b> and <i>italic</i> text.

00:00:04.000 --> 00:00:06.000
<font color="red">Colored text</font> here.
"""
        vtt_file = temp_dir / "test_html.vtt"
        vtt_file.write_text(vtt_content)
        
        segments = TranscriptParser.parse(vtt_file)
        
        assert len(segments) == 2
        assert segments[0]['text'] == "This has bold and italic text."
        assert segments[1]['text'] == "Colored text here."
    
    def test_parse_srt_with_html_tags(self, temp_dir):
        """Test parsing SRT file with HTML tags (should be removed)"""
        srt_content = """1
00:00:01,000 --> 00:00:03,000
This has <b>bold</b> text.

2
00:00:04,000 --> 00:00:06,000
<i>Italic</i> and <u>underlined</u> text.
"""
        srt_file = temp_dir / "test_html.srt"
        srt_file.write_text(srt_content)
        
        segments = TranscriptParser.parse(srt_file)
        
        assert len(segments) == 2
        assert segments[0]['text'] == "This has bold text."
        assert segments[1]['text'] == "Italic and underlined text."
    
    def test_parse_malformed_vtt(self, temp_dir):
        """Test parsing malformed VTT file (should handle gracefully)"""
        malformed_content = """WEBVTT

This line has no timestamp
00:00:01.000 --> 00:00:03.000
Valid caption.

Invalid timestamp line
Some random text.

00:00:04.000 --> 00:00:06.000
Another valid caption.
"""
        vtt_file = temp_dir / "malformed.vtt"
        vtt_file.write_text(malformed_content)
        
        segments = TranscriptParser.parse(vtt_file)
        
        # Should only parse the valid segments
        assert len(segments) == 2
        assert segments[0]['text'] == "Valid caption."
        assert segments[1]['text'] == "Another valid caption."
    
    def test_parse_different_encodings(self, temp_dir):
        """Test parsing files with different encodings"""
        # Test with UTF-8 content including special characters
        vtt_content = """WEBVTT

00:00:01.000 --> 00:00:03.000
Café and naïve résumé.

00:00:04.000 --> 00:00:06.000
Emoji test: 🎬 📺 ✨
"""
        vtt_file = temp_dir / "utf8_test.vtt"
        vtt_file.write_text(vtt_content, encoding='utf-8')
        
        segments = TranscriptParser.parse(vtt_file)
        
        assert len(segments) == 2
        assert "Café and naïve résumé" in segments[0]['text']
        assert "🎬 📺 ✨" in segments[1]['text']
    
    def test_parse_empty_file(self, temp_dir):
        """Test parsing empty file (should raise ValueError)"""
        empty_file = temp_dir / "empty.vtt"
        empty_file.touch()
        
        with pytest.raises(ValueError, match="empty"):
            TranscriptParser.parse(empty_file)
    
    def test_parse_nonexistent_file(self, temp_dir):
        """Test parsing nonexistent file (should raise FileNotFoundError)"""
        nonexistent = temp_dir / "nonexistent.vtt"
        
        with pytest.raises(FileNotFoundError):
            TranscriptParser.parse(nonexistent)
    
    def test_parse_unsupported_format_auto_detect_vtt(self, temp_dir):
        """Test auto-detection of VTT format for unsupported extension"""
        vtt_content = """WEBVTT

00:00:01.000 --> 00:00:03.000
Auto-detected VTT content.
"""
        unknown_file = temp_dir / "test.txt"  # Wrong extension
        unknown_file.write_text(vtt_content)
        
        segments = TranscriptParser.parse(unknown_file)
        
        assert len(segments) == 1
        assert segments[0]['text'] == "Auto-detected VTT content."
    
    def test_parse_unsupported_format_auto_detect_srt(self, temp_dir):
        """Test auto-detection of SRT format for unsupported extension"""
        srt_content = """1
00:00:01,000 --> 00:00:03,000
Auto-detected SRT content.
"""
        unknown_file = temp_dir / "test.txt"  # Wrong extension
        unknown_file.write_text(srt_content)
        
        segments = TranscriptParser.parse(unknown_file)
        
        assert len(segments) == 1
        assert segments[0]['text'] == "Auto-detected SRT content."
    
    def test_validate_segments_valid_data(self):
        """Test segment validation with valid data"""
        segments = [
            {'start': 1.0, 'end': 3.0, 'text': 'First segment'},
            {'start': 4.0, 'end': 6.0, 'text': 'Second segment'},
            {'start': 2.5, 'end': 5.0, 'text': 'Overlapping segment'}
        ]
        
        validated = TranscriptParser.validate_segments(segments)
        
        assert len(validated) == 3
        # Should be sorted by start time
        assert validated[0]['start'] == 1.0
        assert validated[1]['start'] == 2.5
        assert validated[2]['start'] == 4.0
    
    def test_validate_segments_invalid_data(self):
        """Test segment validation with invalid data (should be filtered out)"""
        segments = [
            {'start': 1.0, 'end': 3.0, 'text': 'Valid segment'},
            {'start': -1.0, 'end': 2.0, 'text': 'Negative start time'},  # Invalid
            {'start': 5.0, 'end': 4.0, 'text': 'End before start'},     # Invalid
            {'start': 3.0, 'end': 5.0, 'text': ''},                     # Invalid (empty text)
            {'start': 6.0, 'end': 8.0},                                 # Invalid (missing text)
            {'start': 7.0, 'end': 9.0, 'text': 'Another valid segment'}
        ]
        
        validated = TranscriptParser.validate_segments(segments)
        
        assert len(validated) == 2
        assert validated[0]['text'] == 'Valid segment'
        assert validated[1]['text'] == 'Another valid segment'
    
    def test_time_to_seconds_various_formats(self):
        """Test time string conversion with various formats"""
        # Test HH:MM:SS.mmm format
        assert TranscriptParser._time_to_seconds("01:23:45.678") == 5025.678
        
        # Test MM:SS.mmm format
        assert TranscriptParser._time_to_seconds("12:34.567") == 754.567
        
        # Test SS.mmm format
        assert TranscriptParser._time_to_seconds("45.123") == 45.123
        
        # Test integer seconds
        assert TranscriptParser._time_to_seconds("30") == 30.0
    
    def test_time_to_seconds_invalid_format(self):
        """Test time string conversion with invalid format"""
        with pytest.raises(ValueError):
            TranscriptParser._time_to_seconds("invalid:time:format")
        
        with pytest.raises(ValueError):
            TranscriptParser._time_to_seconds("")
    
    def test_parse_vtt_with_positioning_info(self, temp_dir):
        """Test parsing VTT with positioning information (should be ignored)"""
        vtt_content = """WEBVTT

00:00:01.000 --> 00:00:03.000 position:50% line:90%
Caption with positioning info.

00:00:04.000 --> 00:00:06.000 align:center
Centered caption.
"""
        vtt_file = temp_dir / "positioned.vtt"
        vtt_file.write_text(vtt_content)
        
        segments = TranscriptParser.parse(vtt_file)
        
        assert len(segments) == 2
        assert segments[0]['start'] == 1.0
        assert segments[0]['end'] == 3.0
        assert segments[1]['start'] == 4.0
        assert segments[1]['end'] == 6.0
    
    def test_parse_multiline_captions(self, temp_dir):
        """Test parsing captions that span multiple lines"""
        vtt_content = """WEBVTT

00:00:01.000 --> 00:00:05.000
This is a very long caption
that spans multiple lines
and should be joined together.

00:00:06.000 --> 00:00:08.000
Short caption.
"""
        vtt_file = temp_dir / "multiline.vtt"
        vtt_file.write_text(vtt_content)
        
        segments = TranscriptParser.parse(vtt_file)
        
        assert len(segments) == 2
        assert segments[0]['text'] == "This is a very long caption that spans multiple lines and should be joined together."
        assert segments[1]['text'] == "Short caption."