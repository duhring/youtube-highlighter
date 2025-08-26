import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Union
from app.transcript_formatter import TranscriptFormatter, TranscriptFormat

logger = logging.getLogger(__name__)

class TranscriptParser:
    """Parse WebVTT and SRT transcript files with robust error handling"""

    @staticmethod
    def parse(file_path: Union[str, Path]) -> List[Dict[str, Union[float, str]]]:
        """
        Parses a transcript file with enhanced format detection and fallback strategies.
        
        Args:
            file_path: Path to the transcript file
            
        Returns:
            List of transcript segments with start, end, and text
            
        Raises:
            ValueError: If file format is unsupported or file is invalid
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Transcript file not found: {file_path}")
        
        if file_path.stat().st_size == 0:
            raise ValueError(f"Transcript file is empty: {file_path}")
        
        # Try enhanced parsing first
        try:
            segments = TranscriptParser._parse_with_formatter(file_path)
            if segments:
                return segments
        except Exception as e:
            logger.warning(f"Enhanced parsing failed for {file_path}: {e}")
        
        # Fallback to legacy parsing methods
        file_extension = file_path.suffix.lower()
        
        try:
            if file_extension == '.vtt':
                return TranscriptParser._parse_vtt(file_path)
            elif file_extension == '.srt':
                return TranscriptParser._parse_srt(file_path)
            else:
                # Try to detect format from content
                return TranscriptParser._parse_auto_detect(file_path)
        except Exception as e:
            logger.error(f"All parsing methods failed for transcript file {file_path}: {e}")
            raise ValueError(f"Could not parse transcript file {file_path}: {e}")
    
    @staticmethod
    def _parse_with_formatter(file_path: Path) -> List[Dict[str, Union[float, str]]]:
        """Parse using the enhanced TranscriptFormatter"""
        try:
            # Read file content with encoding detection
            content = TranscriptParser._read_file_with_encoding_detection(file_path)
            
            # Use TranscriptFormatter for detection and parsing
            formatter = TranscriptFormatter()
            detected_format, confidence = formatter.detect_format(content)
            
            logger.info(f"Detected format: {detected_format.value} with confidence {confidence:.2f} for {file_path}")
            
            if confidence < 0.2:
                logger.warning(f"Low confidence format detection for {file_path}, trying legacy parsing")
                return []
            
            # Parse with the formatter
            segments = formatter.parse_to_segments(content, detected_format)
            
            # Convert to the expected format
            result_segments = []
            for segment in segments:
                result_segments.append({
                    'start': segment.start,
                    'end': segment.end,
                    'text': segment.text
                })
            
            logger.info(f"Successfully parsed {len(result_segments)} segments using enhanced formatter")
            return result_segments
            
        except Exception as e:
            logger.error(f"Enhanced parsing failed for {file_path}: {e}")
            return []
    
    @staticmethod
    def _read_file_with_encoding_detection(file_path: Path) -> str:
        """Read file with multiple encoding attempts"""
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                if encoding != 'utf-8':
                    logger.info(f"Successfully read {file_path} using {encoding} encoding")
                return content
            except UnicodeDecodeError:
                continue
        
        # Final attempt with error replacement
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                logger.warning(f"Read {file_path} with character replacement due to encoding issues")
                return content
        except Exception as e:
            raise ValueError(f"Could not read file {file_path} with any encoding: {e}")

    @staticmethod
    def _parse_vtt(file_path: Path) -> List[Dict[str, Union[float, str]]]:
        """Parse WebVTT format with robust error handling"""
        segments = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try different encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    logger.info(f"Successfully read file using {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError(f"Could not decode file with any supported encoding")
        
        # Normalize line endings
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Validate VTT format
        if not content.strip().startswith('WEBVTT'):
            logger.warning(f"File may not be valid VTT format: {file_path}")
        
        # More robust parsing approach
        # Split content into blocks separated by empty lines
        blocks = re.split(r'\n\s*\n', content)
        
        for block in blocks:
            block = block.strip()
            if not block or block.startswith('WEBVTT') or block.startswith('NOTE'):
                continue
            
            lines = [line.strip() for line in block.split('\n') if line.strip()]
            if len(lines) < 2:
                continue
            
            timestamp_line = None
            text_lines = []
            cue_id = None
            
            # Parse lines in the block
            for i, line in enumerate(lines):
                if ' --> ' in line:
                    timestamp_line = line
                    # Everything before timestamp might be cue ID
                    if i > 0:
                        cue_id = lines[i-1]
                    # Everything after timestamp is text
                    text_lines = lines[i+1:]
                    break
            
            if timestamp_line and text_lines:
                try:
                    # Parse timestamp
                    timestamp_parts = timestamp_line.split(' --> ')
                    if len(timestamp_parts) != 2:
                        continue
                    
                    start_time = timestamp_parts[0].strip()
                    end_time = timestamp_parts[1].strip()
                    
                    # Remove positioning/styling info from end time
                    end_time = re.split(r'\s+', end_time)[0]
                    
                    start_seconds = TranscriptParser._time_to_seconds(start_time)
                    end_seconds = TranscriptParser._time_to_seconds(end_time)
                    
                    # Clean and join text
                    clean_text_lines = []
                    for text_line in text_lines:
                        # Remove HTML tags and VTT styling
                        clean_line = re.sub(r'<[^>]+>', '', text_line)
                        clean_line = re.sub(r'&[a-zA-Z0-9#]+;', '', clean_line)  # HTML entities
                        # Remove timestamp patterns that might be mixed in with text
                        clean_line = re.sub(r'^\d+:\d+$', '', clean_line)  # Remove standalone timestamps like "0:02"
                        clean_line = re.sub(r'^\[\w+\]$', '', clean_line)  # Remove [Music], [Applause] etc.
                        clean_line = clean_line.strip()
                        
                        if clean_line and not clean_line.isdigit():
                            clean_text_lines.append(clean_line)
                    
                    if clean_text_lines:
                        text = ' '.join(clean_text_lines)
                        segments.append({
                            'start': start_seconds,
                            'end': end_seconds,
                            'text': text
                        })
                        
                except (ValueError, IndexError) as e:
                    logger.debug(f"Skipped invalid cue in {file_path}: {e}")
                    continue
        
        logger.info(f"Parsed {len(segments)} segments from VTT file: {file_path}")
        return segments
    
    @staticmethod
    def _parse_srt(file_path: Path) -> List[Dict[str, Union[float, str]]]:
        """Parse SRT format with robust error handling"""
        segments = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try different encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    logger.info(f"Successfully read file using {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError(f"Could not decode file with any supported encoding")
        
        # Normalize line endings
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Split into subtitle blocks
        blocks = re.split(r'\n\s*\n', content.strip())
        
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            
            lines = [line.strip() for line in block.split('\n') if line.strip()]
            if len(lines) < 3:
                continue
            
            try:
                # First line should be sequence number
                sequence_num = lines[0]
                if not sequence_num.isdigit():
                    continue
                
                # Second line should be timestamp
                timestamp_line = lines[1]
                if ' --> ' not in timestamp_line:
                    continue
                
                # Remaining lines are text
                text_lines = lines[2:]
                
                # Parse timestamp
                start_time_str, end_time_str = timestamp_line.split(' --> ')
                start_time_str = start_time_str.strip()
                end_time_str = end_time_str.strip()
                
                # Convert SRT time format (HH:MM:SS,mmm) to seconds
                start_seconds = TranscriptParser._time_to_seconds(start_time_str.replace(',', '.'))
                end_seconds = TranscriptParser._time_to_seconds(end_time_str.replace(',', '.'))
                
                # Clean and join text
                clean_text_lines = []
                for text_line in text_lines:
                    # Remove HTML tags
                    clean_line = re.sub(r'<[^>]+>', '', text_line)
                    # Remove common SRT formatting
                    clean_line = re.sub(r'\{[^}]*\}', '', clean_line)
                    # Remove HTML entities
                    clean_line = re.sub(r'&[a-zA-Z0-9#]+;', '', clean_line)
                    clean_line = clean_line.strip()
                    
                    if clean_line:
                        clean_text_lines.append(clean_line)
                
                if clean_text_lines:
                    text = ' '.join(clean_text_lines)
                    segments.append({
                        'start': start_seconds,
                        'end': end_seconds,
                        'text': text
                    })
                    
            except (ValueError, IndexError) as e:
                logger.debug(f"Skipped invalid subtitle block in {file_path}: {e}")
                continue
        
        logger.info(f"Parsed {len(segments)} segments from SRT file: {file_path}")
        return segments
    
    @staticmethod
    def _parse_auto_detect(file_path: Path) -> List[Dict[str, Union[float, str]]]:
        """Auto-detect format and parse"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(1000)  # Read first 1KB for detection
            
            if 'WEBVTT' in content:
                logger.info(f"Auto-detected VTT format for {file_path}")
                return TranscriptParser._parse_vtt(file_path)
            elif re.search(r'^\d+\s*\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}', content, re.MULTILINE):
                logger.info(f"Auto-detected SRT format for {file_path}")
                return TranscriptParser._parse_srt(file_path)
            else:
                raise ValueError(f"Could not auto-detect format for {file_path}")
                
        except Exception as e:
            raise ValueError(f"Auto-detection failed for {file_path}: {e}")
    
    @staticmethod
    def _time_to_seconds(time_str: str) -> float:
        """Convert time string to seconds with robust parsing"""
        try:
            time_str = time_str.strip()
            
            # Handle different time formats
            if ':' in time_str:
                parts = time_str.split(':')
                if len(parts) == 3:
                    hours, minutes, seconds = parts
                    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                elif len(parts) == 2:
                    minutes, seconds = parts  
                    return int(minutes) * 60 + float(seconds)
                else:
                    raise ValueError(f"Invalid time format: {time_str}")
            else:
                # Assume it's just seconds
                return float(time_str)
                
        except (ValueError, IndexError) as e:
            logger.error(f"Could not parse time string '{time_str}': {e}")
            raise ValueError(f"Invalid time format: {time_str}")
    
    @staticmethod
    def validate_segments(segments: List[Dict[str, Union[float, str]]]) -> List[Dict[str, Union[float, str]]]:
        """Validate and clean up parsed segments"""
        if not segments:
            return segments
        
        cleaned_segments = []
        
        for i, segment in enumerate(segments):
            try:
                # Validate required fields
                if not all(key in segment for key in ['start', 'end', 'text']):
                    logger.warning(f"Skipping segment {i}: missing required fields")
                    continue
                
                # Validate timing
                start = float(segment['start'])
                end = float(segment['end'])
                text = str(segment['text']).strip()
                
                if start < 0 or end < 0:
                    logger.warning(f"Skipping segment {i}: negative timestamp")
                    continue
                
                if start >= end:
                    logger.warning(f"Skipping segment {i}: invalid time range (start >= end)")
                    continue
                
                if not text:
                    logger.warning(f"Skipping segment {i}: empty text")
                    continue
                
                cleaned_segments.append({
                    'start': start,
                    'end': end, 
                    'text': text
                })
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid segment {i}: {e}")
                continue
        
        # Sort by start time
        cleaned_segments.sort(key=lambda x: x['start'])
        
        logger.info(f"Validated {len(cleaned_segments)} segments out of {len(segments)} total")
        return cleaned_segments
