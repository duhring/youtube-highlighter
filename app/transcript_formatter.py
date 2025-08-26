import re
import json
from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TranscriptFormat(Enum):
    """Supported transcript formats"""
    VTT = "vtt"
    SRT = "srt"
    YOUTUBE_COPY_PASTE = "youtube_copy_paste"
    PLAIN_TEXT = "plain_text"
    JSON_TIMESTAMPS = "json_timestamps"
    UNKNOWN = "unknown"


@dataclass
class TranscriptSegment:
    """A single transcript segment with timing and text"""
    start: float
    end: float
    text: str


class TranscriptFormatter:
    """Universal transcript format detector and converter"""
    
    def __init__(self):
        self.youtube_patterns = [
            # YouTube format: "0:00 Some text" or "1:23 Some text"
            r'^(\d{1,2}:\d{2})\s+(.+)$',
            # YouTube format with seconds: "0:00:00 Some text" or "1:23:45 Some text"  
            r'^(\d{1,2}:\d{2}:\d{2})\s+(.+)$',
            # YouTube format with milliseconds: "0:00.000 Some text"
            r'^(\d{1,2}:\d{2}\.\d{3})\s+(.+)$',
            # YouTube format with hours: "1:23:45 Some text"
            r'^(\d{1,2}:\d{2}:\d{2})\s+(.+)$'
        ]
    
    def detect_format(self, content: str) -> Tuple[TranscriptFormat, float]:
        """
        Detect transcript format with confidence score.
        Returns (format, confidence_score) where confidence is 0-1
        """
        content = content.strip()
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        if not lines:
            return TranscriptFormat.UNKNOWN, 0.0
        
        # Check VTT format
        vtt_confidence = self._check_vtt_format(content, lines)
        if vtt_confidence > 0.6:  # Lower threshold for VTT
            return TranscriptFormat.VTT, vtt_confidence
        
        # Check SRT format  
        srt_confidence = self._check_srt_format(lines)
        if srt_confidence >= 0.7:  # Allow equal to threshold for SRT
            return TranscriptFormat.SRT, srt_confidence
            
        # Check YouTube copy-paste format
        youtube_confidence = self._check_youtube_format(lines)
        if youtube_confidence > 0.6:  # Lower threshold for YouTube
            return TranscriptFormat.YOUTUBE_COPY_PASTE, youtube_confidence
        
        # Check JSON timestamps format
        json_confidence = self._check_json_format(content)
        if json_confidence > 0.6:  # Lower threshold for JSON
            return TranscriptFormat.JSON_TIMESTAMPS, json_confidence
        
        # Default to plain text if we have content
        if content.strip():
            return TranscriptFormat.PLAIN_TEXT, 0.5
            
        return TranscriptFormat.UNKNOWN, 0.0
    
    def _check_vtt_format(self, content: str, lines: List[str]) -> float:
        """Check if content matches VTT format"""
        confidence = 0.0
        
        # Must start with WEBVTT
        if content.startswith('WEBVTT'):
            confidence += 0.4
        
        # Count timestamp lines
        timestamp_lines = 0
        total_lines = len(lines)
        
        for line in lines:
            if ' --> ' in line and self._is_valid_timestamp_line(line):
                timestamp_lines += 1
        
        if total_lines > 0:
            confidence += (timestamp_lines / total_lines) * 0.6
        
        return min(confidence, 1.0)
    
    def _check_srt_format(self, lines: List[str]) -> float:
        """Check if content matches SRT format"""
        confidence = 0.0
        total_lines = len(lines)
        
        if total_lines < 3:
            return 0.0
        
        # SRT pattern: number, timestamp line, text, empty line
        srt_blocks = 0
        i = 0
        
        while i < len(lines):
            # Check for number
            if lines[i].isdigit():
                confidence += 0.2  # Increase confidence for digit
                i += 1
                
                # Check for timestamp line (SRT uses commas, convert to periods for validation)
                if i < len(lines) and ' --> ' in lines[i]:
                    timestamp_line = lines[i].replace(',', '.')  # Convert SRT comma format
                    if self._is_valid_timestamp_line(timestamp_line):
                        confidence += 0.3  # Increase confidence for timestamp
                        srt_blocks += 1
                        i += 1
                        
                        # Skip text lines until empty line or end
                        while i < len(lines) and lines[i]:
                            i += 1
                        i += 1  # Skip empty line
                    else:
                        break
                else:
                    break
            else:
                break
        
        if srt_blocks > 0:
            confidence += 0.4 * min(srt_blocks / 2, 1.0)  # More generous for SRT blocks
        
        return min(confidence, 1.0)
    
    def _check_youtube_format(self, lines: List[str]) -> float:
        """Check if content matches YouTube copy-paste format"""
        if len(lines) < 2:
            return 0.0
        
        matching_lines = 0
        
        for line in lines:
            for pattern in self.youtube_patterns:
                if re.match(pattern, line):
                    matching_lines += 1
                    break
        
        return matching_lines / len(lines)
    
    def _check_json_format(self, content: str) -> float:
        """Check if content is JSON with timestamp data"""
        try:
            data = json.loads(content)
            if isinstance(data, list) and data:
                # Check first few items for timestamp structure
                sample_size = min(3, len(data))
                valid_items = 0
                
                for item in data[:sample_size]:
                    if isinstance(item, dict):
                        has_time = any(key in item for key in ['start', 'time', 'timestamp', 'begin'])
                        has_text = any(key in item for key in ['text', 'content', 'subtitle'])
                        
                        if has_time and has_text:
                            valid_items += 1
                
                return valid_items / sample_size
            
        except (json.JSONDecodeError, TypeError):
            pass
        
        return 0.0
    
    def _is_valid_timestamp_line(self, line: str) -> bool:
        """Check if line is a valid timestamp line"""
        timestamp_patterns = [
            r'\d{2}:\d{2}:\d{2}[\.,]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[\.,]\d{3}',  # HH:MM:SS.mmm
            r'\d{1,2}:\d{2}[\.,]\d{3}\s*-->\s*\d{1,2}:\d{2}[\.,]\d{3}',          # MM:SS.mmm
            r'\d{1,2}:\d{2}\s*-->\s*\d{1,2}:\d{2}',                             # MM:SS
            r'\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}',       # Exact VTT format
        ]
        
        return any(re.search(pattern, line) for pattern in timestamp_patterns)
    
    def convert_to_vtt(self, content: str, detected_format: Optional[TranscriptFormat] = None) -> str:
        """Convert any supported format to VTT"""
        if detected_format is None:
            detected_format, _ = self.detect_format(content)
        
        segments = self.parse_to_segments(content, detected_format)
        return self.segments_to_vtt(segments)
    
    def parse_to_segments(self, content: str, format_type: TranscriptFormat) -> List[TranscriptSegment]:
        """Parse content to standardized segments"""
        if format_type == TranscriptFormat.VTT:
            return self._parse_vtt_segments(content)
        elif format_type == TranscriptFormat.SRT:
            return self._parse_srt_segments(content)
        elif format_type == TranscriptFormat.YOUTUBE_COPY_PASTE:
            return self._parse_youtube_segments(content)
        elif format_type == TranscriptFormat.JSON_TIMESTAMPS:
            return self._parse_json_segments(content)
        elif format_type == TranscriptFormat.PLAIN_TEXT:
            return self._parse_plain_text_segments(content)
        else:
            return []
    
    def _parse_vtt_segments(self, content: str) -> List[TranscriptSegment]:
        """Parse VTT format content"""
        segments = []
        blocks = re.split(r'\n\s*\n', content)
        
        for block in blocks[1:]:  # Skip WEBVTT header
            lines = [line.strip() for line in block.split('\n') if line.strip()]
            if len(lines) < 2:
                continue
            
            # Find timestamp line
            timestamp_line = None
            text_lines = []
            
            for i, line in enumerate(lines):
                if ' --> ' in line:
                    timestamp_line = line
                    text_lines = lines[i+1:]
                    break
            
            if timestamp_line and text_lines:
                try:
                    start_time, end_time = self._parse_timestamp_line(timestamp_line)
                    text = ' '.join(text_lines)
                    segments.append(TranscriptSegment(start_time, end_time, text))
                except ValueError:
                    continue
        
        return segments
    
    def _parse_srt_segments(self, content: str) -> List[TranscriptSegment]:
        """Parse SRT format content"""
        segments = []
        blocks = re.split(r'\n\s*\n', content)
        
        for block in blocks:
            lines = [line.strip() for line in block.split('\n') if line.strip()]
            if len(lines) < 3:
                continue
            
            # SRT format: number, timestamp, text lines
            try:
                # Skip number line
                timestamp_line = lines[1]
                text_lines = lines[2:]
                
                if ' --> ' in timestamp_line:
                    start_time, end_time = self._parse_timestamp_line(timestamp_line.replace(',', '.'))
                    text = ' '.join(text_lines)
                    segments.append(TranscriptSegment(start_time, end_time, text))
            except (ValueError, IndexError):
                continue
        
        return segments
    
    def _parse_youtube_segments(self, content: str) -> List[TranscriptSegment]:
        """Parse YouTube copy-paste format"""
        segments = []
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        for i, line in enumerate(lines):
            for pattern in self.youtube_patterns:
                match = re.match(pattern, line)
                if match:
                    timestamp_str = match.group(1)
                    text = match.group(2)
                    
                    try:
                        start_time = self._parse_youtube_timestamp(timestamp_str)
                        # Estimate end time (next timestamp or +3 seconds)
                        end_time = start_time + 3.0
                        
                        if i + 1 < len(lines):
                            next_match = None
                            for next_pattern in self.youtube_patterns:
                                next_match = re.match(next_pattern, lines[i + 1])
                                if next_match:
                                    break
                            
                            if next_match:
                                next_time = self._parse_youtube_timestamp(next_match.group(1))
                                end_time = next_time
                        
                        segments.append(TranscriptSegment(start_time, end_time, text))
                        break
                    except ValueError:
                        continue
        
        return segments
    
    def _parse_json_segments(self, content: str) -> List[TranscriptSegment]:
        """Parse JSON timestamp format"""
        try:
            data = json.loads(content)
            segments = []
            
            for item in data:
                if isinstance(item, dict):
                    # Try different field names
                    start_time = None
                    end_time = None
                    text = None
                    
                    # Time fields
                    for time_field in ['start', 'begin', 'time', 'timestamp']:
                        if time_field in item:
                            start_time = float(item[time_field])
                            break
                    
                    for end_field in ['end', 'stop', 'duration']:
                        if end_field in item:
                            end_value = float(item[end_field])
                            if end_field == 'duration':
                                end_time = start_time + end_value if start_time else end_value
                            else:
                                end_time = end_value
                            break
                    
                    # Text fields
                    for text_field in ['text', 'content', 'subtitle', 'caption']:
                        if text_field in item:
                            text = str(item[text_field])
                            break
                    
                    if start_time is not None and text:
                        if end_time is None:
                            end_time = start_time + 3.0
                        segments.append(TranscriptSegment(start_time, end_time, text))
            
            return segments
        
        except (json.JSONDecodeError, ValueError, TypeError):
            return []
    
    def _parse_plain_text_segments(self, content: str) -> List[TranscriptSegment]:
        """Parse plain text by creating segments with estimated timing"""
        sentences = re.split(r'(?<=[.!?])\s+', content)
        segments = []
        current_time = 0.0
        
        for sentence in sentences:
            if not sentence.strip():
                continue
            
            # Estimate duration based on word count (average 2 words per second)
            word_count = len(sentence.split())
            duration = max(word_count * 0.5, 1.0)
            
            segments.append(TranscriptSegment(
                start=current_time,
                end=current_time + duration,
                text=sentence.strip()
            ))
            
            current_time += duration
        
        return segments
    
    def _parse_timestamp_line(self, line: str) -> Tuple[float, float]:
        """Parse a timestamp line like '00:01:30.500 --> 00:01:33.400'"""
        parts = line.split(' --> ')
        if len(parts) != 2:
            raise ValueError(f"Invalid timestamp line: {line}")
        
        start_time = self._parse_time_string(parts[0].strip())
        end_time = self._parse_time_string(parts[1].strip())
        
        return start_time, end_time
    
    def _parse_time_string(self, time_str: str) -> float:
        """Parse time string like '00:01:30.500' or '1:30.500'"""
        # Remove any extra formatting
        time_str = re.split(r'\s+', time_str)[0]
        
        # Handle different formats
        if time_str.count(':') == 2:
            # HH:MM:SS.mmm
            match = re.match(r'(\d{1,2}):(\d{2}):(\d{2})(?:[\.,](\d{1,3}))?', time_str)
            if match:
                hours = int(match.group(1))
                minutes = int(match.group(2))
                seconds = int(match.group(3))
                milliseconds = int(match.group(4) or 0)
                return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
        
        elif time_str.count(':') == 1:
            # MM:SS.mmm
            match = re.match(r'(\d{1,2}):(\d{2})(?:[\.,](\d{1,3}))?', time_str)
            if match:
                minutes = int(match.group(1))
                seconds = int(match.group(2))
                milliseconds = int(match.group(3) or 0)
                return minutes * 60 + seconds + milliseconds / 1000.0
        
        raise ValueError(f"Cannot parse time string: {time_str}")
    
    def _parse_youtube_timestamp(self, timestamp_str: str) -> float:
        """Parse YouTube format timestamp like '1:23' or '1:23:45'"""
        parts = timestamp_str.split(':')
        
        if len(parts) == 2:  # MM:SS
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:  # HH:MM:SS
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        else:
            raise ValueError(f"Invalid YouTube timestamp: {timestamp_str}")
    
    def segments_to_vtt(self, segments: List[TranscriptSegment]) -> str:
        """Convert segments to VTT format"""
        vtt_lines = ["WEBVTT", ""]
        
        for segment in segments:
            start_time = self._seconds_to_vtt_time(segment.start)
            end_time = self._seconds_to_vtt_time(segment.end)
            
            vtt_lines.append(f"{start_time} --> {end_time}")
            vtt_lines.append(segment.text)
            vtt_lines.append("")
        
        return "\n".join(vtt_lines)
    
    def _seconds_to_vtt_time(self, seconds: float) -> str:
        """Convert seconds to VTT timestamp format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    
    def get_format_info(self, format_type: TranscriptFormat) -> Dict[str, str]:
        """Get human-readable information about a format"""
        format_info = {
            TranscriptFormat.VTT: {
                "name": "WebVTT",
                "description": "Standard web video text track format",
                "example": "WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nHello world"
            },
            TranscriptFormat.SRT: {
                "name": "SubRip",
                "description": "Common subtitle format",
                "example": "1\n00:00:01,000 --> 00:00:03,000\nHello world"
            },
            TranscriptFormat.YOUTUBE_COPY_PASTE: {
                "name": "YouTube Copy-Paste",
                "description": "Format when copying from YouTube transcript panel",
                "example": "0:00 Hello world\n0:03 Welcome to the video"
            },
            TranscriptFormat.PLAIN_TEXT: {
                "name": "Plain Text",
                "description": "Simple text without timing",
                "example": "Hello world. Welcome to the video."
            },
            TranscriptFormat.JSON_TIMESTAMPS: {
                "name": "JSON with Timestamps",
                "description": "JSON format with timing data",
                "example": '[{"start": 0, "end": 3, "text": "Hello world"}]'
            }
        }
        
        return format_info.get(format_type, {"name": "Unknown", "description": "", "example": ""})