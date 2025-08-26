import subprocess
import re
import time
import json
from pathlib import Path
from typing import Optional, List, Tuple, Dict
from pytube import YouTube
import requests
from bs4 import BeautifulSoup
from app.config import get_setting
import logging

logger = logging.getLogger(__name__)

class TranscriptDownloader:
    """Unified transcript downloader with multiple fallback strategies"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir or get_setting("cache_dir", ".cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Get configuration settings
        self.preferred_languages = get_setting("transcript.languages", ["en", "en-US", "en-GB"])
        self.max_retries = get_setting("transcript.max_retries", 3)
        self.retry_delay = get_setting("transcript.retry_delay", 2)
        
    def download_transcript(self, youtube_url: str, video_id: Optional[str] = None) -> Optional[str]:
        """
        Download transcript with multiple fallback strategies.
        Returns path to downloaded transcript file or None if all methods fail.
        """
        if not video_id:
            video_id = self._extract_video_id(youtube_url)
            if not video_id:
                logger.error(f"Could not extract video ID from URL: {youtube_url}")
                return None
        
        logger.info(f"Downloading transcript for video: {video_id}")
        
        # Check cache first
        cached_file = self._find_cached_transcript(video_id)
        if cached_file:
            logger.info(f"Found cached transcript: {cached_file}")
            return str(cached_file)
        
        # Try multiple download strategies
        strategies = [
            self._download_with_web_scraping,
            self._download_with_ytdlp_manual,
            self._download_with_ytdlp_auto,
            self._download_with_pytube,
        ]
        
        for strategy in strategies:
            try:
                result = strategy(youtube_url, video_id)
                if result:
                    logger.info(f"Successfully downloaded transcript using {getattr(strategy, '__name__', str(strategy))}")
                    return result
            except Exception as e:
                logger.warning(f"Strategy {getattr(strategy, '__name__', str(strategy))} failed: {e}")
                continue
        
        logger.error(f"All transcript download strategies failed for video: {video_id}")
        return None
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from various YouTube URL formats"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
            r'youtube\.com/v/([^&\n?#]+)',
            r'youtube\.com/watch\?.*?v=([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _find_cached_transcript(self, video_id: str) -> Optional[Path]:
        """Find existing transcript in cache with flexible naming"""
        # Common naming patterns used by different download methods
        patterns = [
            f"{video_id}.vtt",
            f"{video_id}.srt", 
            f"{video_id}.en.vtt",
            f"{video_id}.en.srt",
            f"{video_id}_manual.vtt",
            f"{video_id}_manual.srt",
        ]
        
        for pattern in patterns:
            file_path = self.cache_dir / pattern
            if file_path.exists() and file_path.stat().st_size > 0:
                return file_path
        
        # Use glob for more flexible matching
        for ext in ['.vtt', '.srt']:
            matches = list(self.cache_dir.glob(f"{video_id}*{ext}"))
            if matches:
                # Return the most recent match
                return max(matches, key=lambda p: p.stat().st_mtime)
        
        return None
    
    def _download_with_web_scraping(self, youtube_url: str, video_id: str) -> Optional[str]:
        """Download transcript by scraping YouTube's transcript panel"""
        try:
            logger.info(f"Attempting web scraping for video: {video_id}")
            
            # Setup session with realistic headers
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
            
            # Get the main YouTube page
            response = session.get(youtube_url, timeout=30)
            response.raise_for_status()
            
            # Look for transcript data in the page
            transcript_data = self._extract_transcript_from_page(response.text, video_id)
            
            if transcript_data:
                # Save as VTT format
                output_path = self.cache_dir / f"{video_id}_scraped.vtt"
                vtt_content = self._convert_transcript_data_to_vtt(transcript_data)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(vtt_content)
                
                logger.info(f"Successfully scraped transcript: {output_path}")
                return str(output_path)
            
            # Try alternative method: look for transcript API endpoints
            api_transcript = self._try_transcript_api(session, video_id)
            if api_transcript:
                output_path = self.cache_dir / f"{video_id}_api.vtt"
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(api_transcript)
                
                logger.info(f"Successfully got transcript via API: {output_path}")
                return str(output_path)
            
            logger.warning(f"No transcript data found via web scraping for video: {video_id}")
            return None
            
        except Exception as e:
            logger.warning(f"Web scraping failed for {video_id}: {e}")
            return None
    
    def _extract_transcript_from_page(self, html_content: str, video_id: str) -> Optional[List[Dict]]:
        """Extract transcript data from YouTube page HTML"""
        try:
            # Look for transcript data in various script tags
            patterns = [
                # Pattern 1: Look for captions data in ytInitialPlayerResponse
                r'"captions":\s*({[^}]+tracksInfo[^}]+})',
                # Pattern 2: Look for transcript tracks
                r'"captionTracks":\s*(\[[^\]]+\])',
                # Pattern 3: Look for timedtext URLs
                r'"baseUrl":\s*"([^"]*timedtext[^"]*)"'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html_content)
                if matches:
                    logger.debug(f"Found potential transcript data with pattern: {pattern}")
                    # Try to parse and extract transcript
                    for match in matches:
                        transcript_data = self._parse_transcript_match(match, video_id)
                        if transcript_data:
                            return transcript_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting transcript from page: {e}")
            return None
    
    def _parse_transcript_match(self, match_data: str, video_id: str) -> Optional[List[Dict]]:
        """Parse matched transcript data"""
        try:
            # If it looks like a URL, fetch the transcript from it
            if match_data.startswith('http') and 'timedtext' in match_data:
                return self._fetch_timedtext_url(match_data)
            
            # If it looks like JSON, try to parse it
            if match_data.strip().startswith(('{', '[')):
                try:
                    data = json.loads(match_data)
                    return self._extract_from_json_data(data)
                except json.JSONDecodeError:
                    pass
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing transcript match: {e}")
            return None
    
    def _fetch_timedtext_url(self, url: str) -> Optional[List[Dict]]:
        """Fetch transcript from timedtext URL"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse the response based on format
            if 'fmt=json3' in url:
                return self._parse_json3_format(response.text)
            elif 'fmt=srv3' in url:
                return self._parse_srv3_format(response.text)
            else:
                return self._parse_xml_format(response.text)
                
        except Exception as e:
            logger.error(f"Error fetching timedtext URL {url}: {e}")
            return None
    
    def _parse_json3_format(self, content: str) -> Optional[List[Dict]]:
        """Parse JSON3 format transcript"""
        try:
            data = json.loads(content)
            transcript = []
            
            if 'events' in data:
                for event in data['events']:
                    if 'segs' in event and event.get('tStartMs') is not None:
                        start_time = float(event['tStartMs']) / 1000.0
                        duration = float(event.get('dDurationMs', 0)) / 1000.0
                        
                        text_parts = []
                        for seg in event['segs']:
                            if 'utf8' in seg:
                                text_parts.append(seg['utf8'])
                        
                        if text_parts:
                            transcript.append({
                                'start': start_time,
                                'end': start_time + duration,
                                'text': ''.join(text_parts).strip()
                            })
            
            return transcript if transcript else None
            
        except Exception as e:
            logger.error(f"Error parsing JSON3 format: {e}")
            return None
    
    def _parse_srv3_format(self, content: str) -> Optional[List[Dict]]:
        """Parse SRV3 format transcript"""
        try:
            soup = BeautifulSoup(content, 'xml')
            transcript = []
            
            for p in soup.find_all('p'):
                start = float(p.get('t', 0)) / 1000.0
                duration = float(p.get('d', 0)) / 1000.0
                text = p.get_text().strip()
                
                if text:
                    transcript.append({
                        'start': start,
                        'end': start + duration,
                        'text': text
                    })
            
            return transcript if transcript else None
            
        except Exception as e:
            logger.error(f"Error parsing SRV3 format: {e}")
            return None
    
    def _parse_xml_format(self, content: str) -> Optional[List[Dict]]:
        """Parse XML format transcript"""
        try:
            soup = BeautifulSoup(content, 'xml')
            transcript = []
            
            # Handle different XML formats
            for text_tag in soup.find_all(['text', 'p']):
                start_attr = text_tag.get('start') or text_tag.get('t')
                dur_attr = text_tag.get('dur') or text_tag.get('d')
                
                if start_attr is not None:
                    start = float(start_attr)
                    if start_attr == text_tag.get('t'):  # Convert from milliseconds
                        start = start / 1000.0
                    
                    duration = 0
                    if dur_attr is not None:
                        duration = float(dur_attr)
                        if dur_attr == text_tag.get('d'):  # Convert from milliseconds
                            duration = duration / 1000.0
                    
                    text = text_tag.get_text().strip()
                    if text:
                        transcript.append({
                            'start': start,
                            'end': start + duration,
                            'text': text
                        })
            
            return transcript if transcript else None
            
        except Exception as e:
            logger.error(f"Error parsing XML format: {e}")
            return None
    
    def _extract_from_json_data(self, data: Dict) -> Optional[List[Dict]]:
        """Extract transcript from JSON data structure"""
        try:
            # This would need to be implemented based on actual YouTube data structure
            # For now, return None as we don't have the exact structure
            return None
            
        except Exception as e:
            logger.error(f"Error extracting from JSON data: {e}")
            return None
    
    def _try_transcript_api(self, session: requests.Session, video_id: str) -> Optional[str]:
        """Try to get transcript via YouTube's internal API"""
        try:
            # This is a simplified version - real implementation would need
            # to handle authentication and proper API calls
            api_url = f"https://www.youtube.com/api/timedtext?v={video_id}&lang=en&fmt=vtt"
            
            response = session.get(api_url, timeout=30)
            if response.status_code == 200 and response.text.strip():
                return response.text
            
            return None
            
        except Exception as e:
            logger.warning(f"API transcript attempt failed: {e}")
            return None
    
    def _convert_transcript_data_to_vtt(self, transcript_data: List[Dict]) -> str:
        """Convert transcript data to VTT format"""
        vtt_lines = ["WEBVTT", ""]
        
        for i, segment in enumerate(transcript_data):
            start = segment['start']
            end = segment['end']
            text = segment['text']
            
            # Format timestamps
            start_time = self._seconds_to_vtt_time(start)
            end_time = self._seconds_to_vtt_time(end)
            
            vtt_lines.append(f"{start_time} --> {end_time}")
            vtt_lines.append(text)
            vtt_lines.append("")
        
        return "\n".join(vtt_lines)
    
    def _seconds_to_vtt_time(self, seconds: float) -> str:
        """Convert seconds to VTT timestamp format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    
    def _download_with_ytdlp_manual(self, youtube_url: str, video_id: str) -> Optional[str]:
        """Download manual subtitles using yt-dlp"""
        output_path = self.cache_dir / f"{video_id}"
        
        cmd = [
            "yt-dlp",
            "--skip-download",
            "--write-subs",
            "--sub-langs", ",".join(self.preferred_languages),
            "--sub-format", "vtt/srt/best",
            "--no-write-auto-subs",  # Only manual subtitles
            "-o", f"{output_path}.%(ext)s",
            youtube_url
        ]
        
        return self._execute_ytdlp_command(cmd, video_id)
    
    def _download_with_ytdlp_auto(self, youtube_url: str, video_id: str) -> Optional[str]:
        """Download auto-generated subtitles using yt-dlp"""
        output_path = self.cache_dir / f"{video_id}_auto"
        
        cmd = [
            "yt-dlp", 
            "--skip-download",
            "--write-auto-subs",
            "--sub-langs", ",".join(self.preferred_languages),
            "--sub-format", "vtt/srt/best",
            "-o", f"{output_path}.%(ext)s",
            youtube_url
        ]
        
        return self._execute_ytdlp_command(cmd, video_id, "_auto")
    
    def _download_with_pytube(self, youtube_url: str, video_id: str) -> Optional[str]:
        """Fallback using pytube for captions"""
        try:
            yt = YouTube(youtube_url)
            
            # Try to get captions in preferred languages
            for lang in self.preferred_languages:
                if lang in yt.captions:
                    caption = yt.captions[lang]
                    output_path = self.cache_dir / f"{video_id}_pytube.srt"
                    
                    # Download caption as SRT
                    srt_content = caption.generate_srt_captions()
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(srt_content)
                    
                    logger.info(f"Downloaded captions using pytube: {output_path}")
                    return str(output_path)
            
            logger.warning(f"No captions available in preferred languages: {self.preferred_languages}")
            return None
            
        except Exception as e:
            logger.error(f"Pytube download failed: {e}")
            return None
    
    def _execute_ytdlp_command(self, cmd: List[str], video_id: str, suffix: str = "") -> Optional[str]:
        """Execute yt-dlp command with retry logic"""
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Executing yt-dlp command (attempt {attempt + 1}): {' '.join(cmd)}")
                
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    check=True,
                    timeout=120  # 2 minute timeout
                )
                
                # Check if the output indicates no subtitles
                if "no subtitles" in result.stdout.lower() or "no captions" in result.stdout.lower():
                    logger.info(f"No subtitles available for video: {video_id}")
                    break  # Don't retry if subtitles don't exist
                
                # Check if subtitles were actually downloaded
                downloaded_file = self._find_downloaded_file(video_id, suffix)
                if downloaded_file:
                    self._validate_transcript_file(downloaded_file)
                    return str(downloaded_file)
                else:
                    logger.warning("yt-dlp completed but no subtitle file found")
                    
            except subprocess.CalledProcessError as e:
                if "no subtitles" in e.stderr.lower() or "no captions" in e.stderr.lower():
                    logger.info(f"No subtitles available for video: {video_id}")
                    break  # Don't retry if subtitles don't exist
                else:
                    logger.warning(f"yt-dlp attempt {attempt + 1} failed: {e.stderr}")
                    
            except subprocess.TimeoutExpired:
                logger.warning(f"yt-dlp timed out (attempt {attempt + 1})")
                
            except Exception as e:
                logger.warning(f"Unexpected error in yt-dlp (attempt {attempt + 1}): {e}")
            
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
        
        return None
    
    def _find_downloaded_file(self, video_id: str, suffix: str = "") -> Optional[Path]:
        """Find the file downloaded by yt-dlp"""
        # yt-dlp can create various filename patterns
        base_patterns = [
            f"{video_id}{suffix}",
            f"{video_id}{suffix}.en", 
            f"{video_id}{suffix}.en-US",
            f"{video_id}{suffix}.en-GB",
        ]
        
        for base in base_patterns:
            for ext in ['.vtt', '.srt']:
                file_path = self.cache_dir / f"{base}{ext}"
                if file_path.exists():
                    return file_path
        
        # Fallback: search for any file matching the video ID
        for ext in ['.vtt', '.srt']:
            matches = list(self.cache_dir.glob(f"{video_id}*{ext}"))
            if matches:
                return max(matches, key=lambda p: p.stat().st_mtime)
        
        return None
    
    def _validate_transcript_file(self, file_path: Path) -> bool:
        """Validate that the transcript file is not empty or corrupted"""
        try:
            if file_path.stat().st_size == 0:
                logger.warning(f"Transcript file is empty: {file_path}")
                file_path.unlink()  # Remove empty file
                return False
            
            # Basic content validation
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1000)  # Read first 1KB
                
                if file_path.suffix == '.vtt':
                    if 'WEBVTT' not in content and '-->' not in content:
                        logger.warning(f"Invalid VTT format: {file_path}")
                        return False
                elif file_path.suffix == '.srt':
                    if '-->' not in content:
                        logger.warning(f"Invalid SRT format: {file_path}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating transcript file {file_path}: {e}")
            return False
    
    def clear_cache(self, video_id: Optional[str] = None):
        """Clear transcript cache for specific video or all videos"""
        if video_id:
            # Remove files matching the video ID
            for file_path in self.cache_dir.glob(f"{video_id}*"):
                if file_path.is_file():
                    file_path.unlink()
                    logger.info(f"Removed cached file: {file_path}")
        else:
            # Clear entire cache
            for file_path in self.cache_dir.glob("*"):
                if file_path.is_file() and file_path.suffix in ['.vtt', '.srt']:
                    file_path.unlink()
            logger.info("Cleared transcript cache")