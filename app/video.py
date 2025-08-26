import re
from pathlib import Path
from pytube import YouTube
from moviepy.editor import VideoFileClip
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import requests
import io
from app.config import get_setting

class VideoProcessor:
    """Handle video download and frame extraction"""

    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.video_id = None
        self.youtube_url = None
        self.video_quality = get_setting("video.quality", "720p")
        self.thumbnail_width = get_setting("video.thumbnail_width", 1280)
        self.thumbnail_height = get_setting("video.thumbnail_height", 720)

    def download_video(self, youtube_url):
        """Download video from YouTube, using cache if available."""
        self.youtube_url = youtube_url
        
        try:
            print(f"🔗 Connecting to YouTube: {youtube_url}")
            yt = YouTube(youtube_url)
            self.video_id = yt.video_id
            print(f"✅ Video info extracted: {yt.title[:50]}...")
        except Exception as e:
            print(f"❌ Failed to extract video info with pytube: {e}")
            print(f"🔄 Trying alternative method to extract video ID...")
            
            # Try to extract video ID manually
            import re
            video_id_match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n?#]+)', youtube_url)
            if video_id_match:
                self.video_id = video_id_match.group(1)
                print(f"✅ Extracted video ID manually: {self.video_id}")
            else:
                print(f"❌ Could not extract video ID from URL")
                return None, None
        
        cache_dir = Path(get_setting("cache_dir", ".cache"))
        cache_dir.mkdir(exist_ok=True)
        video_path = cache_dir / f"{self.video_id}.mp4"

        # Check if cached video exists and is valid
        if video_path.exists():
            try:
                # Validate cached video
                if self._validate_cached_video(video_path):
                    print(f"✅ Found valid video in cache: {video_path}")
                    return str(video_path), yt.title
                else:
                    print(f"⚠️  Cached video invalid, re-downloading: {video_path}")
                    video_path.unlink()  # Remove invalid cache
            except Exception as e:
                print(f"⚠️  Error validating cached video, re-downloading: {e}")
                try:
                    video_path.unlink()
                except:
                    pass

        try:
            print("📥 Downloading video...")
            print(f"🎯 Target quality: {self.video_quality}")
            
            # Try different stream selection strategies
            stream = self._select_optimal_stream(yt)
            
            if not stream:
                raise Exception("No suitable video stream found")

            print(f"📺 Selected stream: {stream.resolution} @ {stream.fps}fps ({stream.filesize // (1024*1024)}MB)")
            
            # Download with progress tracking
            downloaded_path = stream.download(output_path=str(cache_dir), filename=f"{self.video_id}.mp4")
            
            # Verify download
            if not self._validate_cached_video(video_path):
                raise Exception("Downloaded video failed validation")
            
            print(f"✅ Video downloaded successfully: {video_path}")
            return str(video_path), yt.title
            
        except Exception as e:
            print(f"❌ Video download failed with pytube: {e}")
            print(f"🔄 Trying yt-dlp as fallback...")
            
            # Try yt-dlp as fallback
            video_path_ytdlp = self._download_with_ytdlp(youtube_url, cache_dir)
            if video_path_ytdlp and self._validate_cached_video(Path(video_path_ytdlp)):
                # Get video title using yt-dlp
                title = self._get_video_title_ytdlp(youtube_url)
                return str(video_path_ytdlp), title
            
            # Clean up partial downloads
            for path in [video_path, video_path_ytdlp]:
                if path and Path(path).exists():
                    try:
                        Path(path).unlink()
                    except:
                        pass
            return None, None
    
    def _validate_cached_video(self, video_path):
        """Validate that cached video file is complete and playable"""
        try:
            # Check file exists and has reasonable size
            if not video_path.exists():
                return False
            
            file_size = video_path.stat().st_size
            if file_size < 1024 * 100:  # Less than 100KB
                print(f"⚠️  Video file too small: {file_size} bytes")
                return False
            
            # Try to open with MoviePy (quick check)
            from moviepy.editor import VideoFileClip
            try:
                with VideoFileClip(str(video_path)) as test_clip:
                    if test_clip.duration <= 0:
                        print(f"⚠️  Video has invalid duration: {test_clip.duration}")
                        return False
                    
                    # Quick frame test
                    try:
                        test_frame = test_clip.get_frame(min(1.0, test_clip.duration / 2))
                        if test_frame is None:
                            print("⚠️  Unable to extract test frame")
                            return False
                    except Exception as frame_error:
                        print(f"⚠️  Frame extraction test failed: {frame_error}")
                        return False
                    
                    return True
            except Exception as clip_error:
                print(f"⚠️  VideoFileClip validation failed: {clip_error}")
                return False
                
        except Exception as e:
            print(f"⚠️  Video validation error: {e}")
            return False
    
    def _select_optimal_stream(self, yt):
        """Select the optimal video stream based on quality preferences"""
        print(f"🔍 Available streams for video {yt.video_id}:")
        try:
            all_streams = yt.streams.filter(file_extension='mp4')
            for i, stream in enumerate(all_streams[:5]):  # Show first 5 streams
                print(f"   Stream {i+1}: {stream.resolution} - {stream.mime_type} - Progressive: {stream.is_progressive} - Size: {stream.filesize // (1024*1024) if stream.filesize else 'Unknown'}MB")
        except Exception as e:
            print(f"   ⚠️  Could not list streams: {e}")
        
        # Strategy 1: Try lower quality progressive streams first (more likely to work)
        for target_quality in ["360p", "480p", "720p", "1080p"]:
            stream = yt.streams.filter(
                res=target_quality,
                progressive=True, 
                file_extension='mp4'
            ).first()
            
            if stream:
                print(f"🎯 Found progressive stream: {target_quality}")
                return stream
        
        # Strategy 2: Try any progressive stream
        progressive_streams = yt.streams.filter(
            progressive=True, 
            file_extension='mp4'
        ).order_by('resolution')  # Try lower quality first
        
        if progressive_streams:
            stream = progressive_streams[0]  # Take first (lowest quality) progressive stream
            print(f"📹 Using progressive stream: {stream.resolution}")
            return stream
        
        # Strategy 3: Try adaptive streams (video only)
        adaptive_streams = yt.streams.filter(
            adaptive=True,
            file_extension='mp4',
            only_video=True
        ).order_by('resolution')
        
        if adaptive_streams:
            stream = adaptive_streams[0]
            print(f"🎬 Using adaptive video stream: {stream.resolution}")
            return stream
        
        # Strategy 4: Try any MP4 stream
        mp4_streams = yt.streams.filter(file_extension='mp4').order_by('resolution')
        if mp4_streams:
            stream = mp4_streams[0]
            print(f"📽️  Using any MP4 stream: {stream.resolution}")
            return stream
        
        print("❌ No suitable video streams found")
        return None

    def _download_with_ytdlp(self, youtube_url, cache_dir):
        """Download video using yt-dlp as fallback"""
        try:
            import subprocess
            
            output_path = cache_dir / f"{self.video_id}.mp4"
            
            # yt-dlp command optimized for HLS streams
            cmd = [
                'yt-dlp',
                '--format', '230/229/604/603/best[height<=480]/worst',  # Try specific formats from the list, then fallback
                '--output', str(output_path),
                '--no-playlist',
                '--no-warnings',
                '--concurrent-fragments', '4',  # Speed up HLS download
                '--hls-use-mpegts',  # Better HLS handling
                youtube_url
            ]
            
            print(f"🔧 Running yt-dlp command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and output_path.exists():
                print(f"✅ yt-dlp download successful: {output_path}")
                return str(output_path)
            else:
                print(f"❌ yt-dlp download failed:")
                print(f"   Return code: {result.returncode}")
                print(f"   Error: {result.stderr[:200]}")
                return None
                
        except subprocess.TimeoutExpired:
            print(f"❌ yt-dlp download timed out after 5 minutes")
            return None
        except FileNotFoundError:
            print(f"❌ yt-dlp not found - install with: pip install yt-dlp")
            return None
        except Exception as e:
            print(f"❌ yt-dlp download error: {e}")
            return None
    
    def _get_video_title_ytdlp(self, youtube_url):
        """Get video title using yt-dlp"""
        try:
            import subprocess
            
            cmd = [
                'yt-dlp',
                '--get-title',
                '--no-warnings',
                youtube_url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                title = result.stdout.strip()
                print(f"✅ Got video title: {title[:50]}...")
                return title
            else:
                print(f"⚠️  Could not get video title with yt-dlp")
                return "Unknown Video"
                
        except Exception as e:
            print(f"⚠️  Error getting video title: {e}")
            return "Unknown Video"

    def extract_thumbnails(self, video_path, segments):
        """Extract thumbnail images from video segments with enhanced error handling"""
        thumbnails = []
        successful_extractions = 0
        extracted_frame_hashes = []  # Track visual similarity of extracted frames
        
        if video_path:
            video = None
            try:
                print("🖼️  Extracting thumbnails from video...")
                print(f"📹 Video file: {video_path}")
                
                # Validate video file exists and has content
                video_file = Path(video_path)
                if not video_file.exists():
                    print(f"❌ Video file not found: {video_path}")
                    return self._fallback_thumbnail_generation(segments)
                
                if video_file.stat().st_size < 1024:  # Less than 1KB
                    print(f"❌ Video file too small: {video_file.stat().st_size} bytes")
                    return self._fallback_thumbnail_generation(segments)
                
                # Load video with enhanced error handling
                try:
                    video = VideoFileClip(video_path)
                    print(f"📊 Video duration: {video.duration:.2f}s, FPS: {video.fps}")
                except Exception as e:
                    print(f"❌ Failed to load video with MoviePy: {e}")
                    print("🔄 Trying alternative video loading...")
                    return self._fallback_thumbnail_generation(segments)
                
                if video.duration <= 0:
                    print(f"❌ Invalid video duration: {video.duration}")
                    return self._fallback_thumbnail_generation(segments)
                
                # Extract thumbnails for each segment with enhanced error handling
                for i, segment in enumerate(segments):
                    thumbnail_path = None
                    try:
                        print(f"🎬 Processing segment {i+1}/{len(segments)} at {segment['start']:.2f}s")
                        
                        # Try multiple timestamp positions for better frames
                        candidate_times = self._get_candidate_timestamps(segment, video.duration)
                        print(f"   📍 Candidate timestamps for segment {i+1}: {[f'{t:.1f}s' for t in candidate_times]}")
                        
                        frame_extracted = False
                        for attempt, timestamp in enumerate(candidate_times):
                            try:
                                print(f"   🎯 Attempting frame extraction at {timestamp:.2f}s (attempt {attempt+1})")
                                
                                # Extract frame at timestamp
                                frame = video.get_frame(timestamp)
                                
                                if frame is None:
                                    print(f"   ❌ Frame is None at {timestamp:.2f}s")
                                    continue
                                
                                print(f"   ✓ Frame extracted, shape: {frame.shape}, dtype: {frame.dtype}")
                                
                                # Validate frame quality with detailed logging
                                frame_valid, validation_msg = self._is_valid_frame_detailed(frame)
                                
                                # Check if frame is too similar to already extracted frames
                                if frame_valid:
                                    frame_hash = self._calculate_frame_hash(frame)
                                    is_unique = self._is_frame_unique(frame_hash, extracted_frame_hashes)
                                    
                                    if not is_unique:
                                        print(f"   ⚠️  Frame at {timestamp:.2f}s too similar to existing thumbnail, trying next position")
                                        continue
                                
                                if frame_valid:
                                    img = Image.fromarray(frame.astype('uint8'))
                                    
                                    # Resize to target dimensions while maintaining aspect ratio
                                    img = self._resize_thumbnail(img)
                                    
                                    # Save thumbnail
                                    thumbnail_path = self.output_dir / f"thumbnail_{i+1:03d}.png"
                                    img.save(thumbnail_path, "PNG", quality=95)
                                    
                                    print(f"✅ Extracted thumbnail {i+1} from {timestamp:.2f}s (attempt {attempt+1})")
                                    successful_extractions += 1
                                    frame_extracted = True
                                    
                                    # Store frame hash to avoid similar frames
                                    if frame_valid:
                                        extracted_frame_hashes.append(frame_hash)
                                    
                                    break
                                else:
                                    print(f"   ⚠️  Frame at {timestamp:.2f}s failed validation: {validation_msg}")
                                    
                            except Exception as frame_error:
                                print(f"   ❌ Frame extraction error at {timestamp:.2f}s: {type(frame_error).__name__}: {frame_error}")
                                continue
                        
                        if not frame_extracted:
                            print(f"❌ Failed to extract any valid frame for segment {i+1} after {len(candidate_times)} attempts")
                            
                            # Try emergency extraction strategies
                            print(f"   🚑 Attempting emergency extraction strategies...")
                            
                            # Strategy 1: Try random times around the segment
                            import random
                            segment_start = segment['start']
                            segment_end = segment.get('end', segment_start + 10)
                            
                            emergency_times = []
                            for _ in range(10):
                                random_offset = random.uniform(0, min(30, segment_end - segment_start))
                                emergency_time = max(0.5, min(segment_start + random_offset, video.duration - 0.5))
                                if emergency_time not in emergency_times:
                                    emergency_times.append(emergency_time)
                            
                            print(f"   📍 Emergency timestamps: {[f'{t:.1f}s' for t in emergency_times[:5]]}")
                            
                            for timestamp in emergency_times[:5]:
                                try:
                                    frame = video.get_frame(timestamp)
                                    if frame is not None:
                                        # Accept ANY frame, no validation
                                        img = Image.fromarray(frame.astype('uint8'))
                                        img = self._resize_thumbnail(img)
                                        thumbnail_path = self.output_dir / f"thumbnail_{i+1:03d}.png"
                                        img.save(thumbnail_path, "PNG", quality=95)
                                        print(f"✅ Emergency extraction successful for segment {i+1} at {timestamp:.2f}s")
                                        successful_extractions += 1
                                        frame_extracted = True
                                        break
                                except Exception as e:
                                    print(f"   ❌ Emergency extraction failed at {timestamp:.2f}s: {e}")
                                    continue
                            
                            # Strategy 2: If still failed, try a completely different part of the video
                            if not frame_extracted:
                                print(f"   🎲 Last resort: extracting from middle of video...")
                                try:
                                    middle_time = video.duration / 2
                                    frame = video.get_frame(middle_time)
                                    if frame is not None:
                                        img = Image.fromarray(frame.astype('uint8'))
                                        img = self._resize_thumbnail(img)
                                        thumbnail_path = self.output_dir / f"thumbnail_{i+1:03d}.png"
                                        img.save(thumbnail_path, "PNG", quality=95)
                                        print(f"✅ Last resort extraction successful for segment {i+1} from video middle")
                                        successful_extractions += 1
                                        frame_extracted = True
                                except Exception as e:
                                    print(f"   ❌ Last resort extraction failed: {e}")
                        
                        thumbnails.append(str(thumbnail_path) if thumbnail_path else None)
                        
                    except Exception as segment_error:
                        print(f"❌ Failed to process segment {i+1}: {segment_error}")
                        thumbnails.append(None)
                
                # Clean up video resource
                video.close()
                
                print(f"✅ Successfully extracted {successful_extractions}/{len(segments)} thumbnails")
                
                # Return thumbnails as-is - None values will be handled by HTML generator
                if successful_extractions > 0:
                    print(f"🎯 Returning {successful_extractions} real video frame thumbnails (others will use YouTube default)")
                    return thumbnails
                else:
                    print("⚠️  No thumbnails successfully extracted, will use YouTube defaults")
                    return [None] * len(segments)
                    
            except Exception as e:
                print(f"❌ Video processing error: {e}")
                if video:
                    try:
                        video.close()
                    except:
                        pass
                return self._fallback_thumbnail_generation(segments)
        
        return self._fallback_thumbnail_generation(segments)
    
    def _enhance_partial_thumbnails(self, thumbnails, segments):
        """Generate distinct fallback thumbnails for failed extractions"""
        print("🎨 Generating distinct fallbacks for failed thumbnail extractions...")
        
        enhanced_thumbnails = []
        for i, (thumbnail, segment) in enumerate(zip(thumbnails, segments)):
            if thumbnail is None:
                print(f"🔄 Creating distinct fallback for segment {i+1}")
                # Generate a unique styled thumbnail for this specific segment
                fallback_path = self._create_distinct_fallback_thumbnail(i, segment)
                enhanced_thumbnails.append(fallback_path)
            else:
                enhanced_thumbnails.append(thumbnail)
        
        return enhanced_thumbnails
    
    def _create_distinct_fallback_thumbnail(self, segment_index, segment):
        """Create a visually distinct fallback thumbnail for a specific segment"""
        try:
            # Try to get base YouTube thumbnail
            base_image = self._get_base_thumbnail()
            
            if base_image:
                # Apply heavy styling to make it visually distinct
                styled_image = self._create_heavily_styled_thumbnail(base_image, segment_index, segment)
                
                thumbnail_path = self.output_dir / f"thumbnail_{segment_index+1:03d}.png"
                styled_image.save(thumbnail_path, "PNG", quality=95)
                print(f"✅ Created distinct styled fallback for segment {segment_index+1}")
                return str(thumbnail_path)
            else:
                # Create a pure custom thumbnail
                custom_thumbnail = self._create_pure_custom_thumbnail(segment_index, segment)
                if custom_thumbnail:
                    return custom_thumbnail
        except Exception as e:
            print(f"⚠️  Failed to create distinct fallback for segment {segment_index+1}: {e}")
        
        return None
    
    def _create_heavily_styled_thumbnail(self, base_image, index, segment):
        """Apply heavy styling to make fallback thumbnails visually distinct"""
        img = base_image.copy().convert('RGB')
        
        # Enhanced color schemes with dramatic effects
        color_schemes = [
            {"primary": (255, 87, 51), "secondary": (255, 165, 0), "filter": "warm", "brightness": 1.4},    
            {"primary": (74, 144, 226), "secondary": (0, 191, 255), "filter": "cool", "brightness": 0.6},   
            {"primary": (156, 39, 176), "secondary": (186, 85, 211), "filter": "purple", "brightness": 1.3}, 
            {"primary": (76, 175, 80), "secondary": (139, 195, 74), "filter": "green", "brightness": 0.7},   
            {"primary": (244, 67, 54), "secondary": (255, 152, 0), "filter": "red", "brightness": 1.2},     
            {"primary": (96, 125, 139), "secondary": (176, 190, 197), "filter": "grey", "brightness": 0.8}, 
        ]
        
        scheme = color_schemes[index % len(color_schemes)]
        
        # Apply dramatic color filter
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(scheme["brightness"])
        
        # Apply color tinting
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(0.3 + (index * 0.15))  # More dramatic color changes
        
        # Create large, distinctive overlay
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Different overlay patterns for each segment
        patterns = ["diagonal", "corner", "center", "border", "split", "gradient"]
        pattern = patterns[index % len(patterns)]
        
        if pattern == "diagonal":
            # Diagonal stripe overlay
            for y in range(0, img.height, 20):
                draw.rectangle([0, y, img.width, y + 10], fill=scheme["primary"] + (100,))
        elif pattern == "corner":
            # Large corner triangle
            corner_size = min(img.width, img.height) // 2
            draw.polygon([(0, 0), (corner_size, 0), (0, corner_size)], fill=scheme["primary"] + (150,))
        elif pattern == "center":
            # Center circle
            center_x, center_y = img.width // 2, img.height // 2
            radius = min(img.width, img.height) // 4
            draw.ellipse([center_x - radius, center_y - radius, center_x + radius, center_y + radius], 
                        fill=scheme["secondary"] + (120,))
        elif pattern == "border":
            # Thick colored border
            border_width = 30
            draw.rectangle([0, 0, img.width, border_width], fill=scheme["primary"] + (180,))
            draw.rectangle([0, img.height - border_width, img.width, img.height], fill=scheme["primary"] + (180,))
        elif pattern == "split":
            # Vertical split
            draw.rectangle([0, 0, img.width // 2, img.height], fill=scheme["primary"] + (80,))
        else:  # gradient
            # Gradient overlay
            for y in range(img.height):
                alpha = int(150 * (y / img.height))
                draw.rectangle([0, y, img.width, y + 1], fill=scheme["secondary"] + (alpha,))
        
        # Add large, prominent timestamp and segment info
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 48)  # Larger font
            small_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 32)
        except IOError:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Add distinctive segment number
        segment_text = f"#{index + 1}"
        timestamp_text = self._format_timestamp(segment['start'])
        
        # Large segment number in corner
        draw.ellipse([img.width - 100, img.height - 100, img.width - 20, img.height - 20], 
                    fill=scheme["primary"] + (255,))
        
        # Center the text in the circle
        text_bbox = draw.textbbox((0, 0), segment_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = img.width - 60 - text_width // 2
        text_y = img.height - 70
        
        draw.text((text_x, text_y), segment_text, fill=(255, 255, 255), font=font)
        
        # Timestamp in contrasting corner
        timestamp_bg = [20, 20, 200, 60]
        draw.rectangle(timestamp_bg, fill=scheme["secondary"] + (220,))
        draw.text((30, 25), timestamp_text, fill=(255, 255, 255), font=small_font)
        
        # Apply the overlay
        final_img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        
        return final_img
    
    def _create_pure_custom_thumbnail(self, index, segment):
        """Create a pure custom thumbnail when no base image is available"""
        try:
            # Create a gradient background
            img = Image.new('RGB', (self.thumbnail_width, self.thumbnail_height), (50, 50, 50))
            draw = ImageDraw.Draw(img)
            
            color_schemes = [
                (255, 87, 51), (74, 144, 226), (156, 39, 176), 
                (76, 175, 80), (244, 67, 54), (96, 125, 139)
            ]
            
            primary_color = color_schemes[index % len(color_schemes)]
            
            # Create gradient background
            for y in range(img.height):
                alpha = int(255 * (1 - y / img.height))
                blend_color = tuple(int(c * alpha / 255) for c in primary_color)
                draw.rectangle([0, y, img.width, y + 1], fill=blend_color)
            
            # Add large segment number
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 120)
                small_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 36)
            except IOError:
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            segment_text = f"#{index + 1}"
            timestamp_text = self._format_timestamp(segment['start'])
            
            # Center the segment number
            text_bbox = draw.textbbox((0, 0), segment_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = (img.width - text_width) // 2
            y = (img.height - text_height) // 2
            
            # Text shadow
            draw.text((x + 3, y + 3), segment_text, fill=(0, 0, 0, 128), font=font)
            draw.text((x, y), segment_text, fill=(255, 255, 255), font=font)
            
            # Timestamp at bottom
            draw.text((20, img.height - 50), timestamp_text, fill=(255, 255, 255), font=small_font)
            
            thumbnail_path = self.output_dir / f"thumbnail_{index+1:03d}.png"
            img.save(thumbnail_path, "PNG", quality=95)
            
            return str(thumbnail_path)
            
        except Exception as e:
            print(f"Failed to create pure custom thumbnail: {e}")
            return None
    
    def _get_candidate_timestamps(self, segment, video_duration):
        """Get multiple candidate timestamps for frame extraction with better spread"""
        start_time = segment['start']
        end_time = segment.get('end', start_time + 10)  # Default to longer duration
        
        # Ensure times are within video bounds
        start_time = max(0.5, min(start_time, video_duration - 1.0))
        end_time = max(start_time + 1.0, min(end_time, video_duration - 0.5))
        
        segment_duration = end_time - start_time
        
        # Generate more candidate timestamps with better distribution
        candidates = []
        
        # Start with small offset to avoid transition frames
        candidates.append(start_time + 0.5)
        
        # If segment is long enough, sample multiple points
        if segment_duration > 2:
            # Early, middle, and late in segment
            candidates.append(start_time + segment_duration * 0.25)
            candidates.append(start_time + segment_duration * 0.5)
            candidates.append(start_time + segment_duration * 0.75)
        
        # Add more fallback positions
        candidates.append(start_time + 1.0)  # 1 second after start
        candidates.append(start_time + min(2.0, segment_duration - 0.5))  # 2 seconds after start or near end
        
        # Final fallbacks - try exact start and slightly before end
        candidates.append(start_time)
        if segment_duration > 3:
            candidates.append(end_time - 1.0)
        
        # Ensure all candidates are within bounds and remove duplicates
        valid_candidates = []
        for t in candidates:
            t_bounded = max(0.5, min(t, video_duration - 0.5))
            # Only add if not too close to existing candidates
            if not any(abs(t_bounded - existing) < 0.3 for existing in valid_candidates):
                valid_candidates.append(t_bounded)
        
        return valid_candidates[:8]  # Increase attempts to 8
    
    def _is_valid_frame(self, frame):
        """Check if extracted frame is of good quality (not black, not corrupted)"""
        valid, _ = self._is_valid_frame_detailed(frame)
        return valid
    
    def _is_valid_frame_detailed(self, frame):
        """Check if extracted frame is of good quality with detailed diagnostics"""
        try:
            import numpy as np
            
            # Check if frame is not None and has proper shape
            if frame is None:
                return False, "Frame is None"
            
            if len(frame.shape) != 3:
                return False, f"Invalid frame shape: {frame.shape}, expected 3D array"
            
            if frame.shape[2] != 3:
                return False, f"Invalid color channels: {frame.shape[2]}, expected 3 (RGB)"
            
            # Check if frame is not completely black or white
            mean_brightness = np.mean(frame)
            if mean_brightness < 5:
                return False, f"Frame too dark (mean brightness: {mean_brightness:.1f})"
            
            if mean_brightness > 250:
                return False, f"Frame too bright (mean brightness: {mean_brightness:.1f})"
            
            # Check for sufficient variation (not a solid color) - relaxed threshold
            std_brightness = np.std(frame)
            if std_brightness < 5:  # Reduced from 10 to 5 for more lenient validation
                return False, f"Frame lacks variation (std: {std_brightness:.1f})"
            
            return True, f"Valid frame (mean: {mean_brightness:.1f}, std: {std_brightness:.1f})"
            
        except Exception as e:
            # If numpy analysis fails, assume frame is valid
            return True, f"Validation failed, assuming valid: {e}"
    
    def _calculate_frame_hash(self, frame):
        """Calculate a simple hash of frame to detect visual similarity"""
        try:
            import numpy as np
            
            # Resize frame to small size for quick comparison
            small_frame = frame[::16, ::16]  # Sample every 16th pixel
            
            # Calculate simple statistics as hash
            mean_r = np.mean(small_frame[:, :, 0])
            mean_g = np.mean(small_frame[:, :, 1]) 
            mean_b = np.mean(small_frame[:, :, 2])
            std_r = np.std(small_frame[:, :, 0])
            std_g = np.std(small_frame[:, :, 1])
            std_b = np.std(small_frame[:, :, 2])
            
            # Create simple hash tuple
            hash_tuple = (
                round(mean_r, 1), round(mean_g, 1), round(mean_b, 1),
                round(std_r, 1), round(std_g, 1), round(std_b, 1)
            )
            
            return hash_tuple
            
        except Exception as e:
            # Return random hash if calculation fails
            import random
            return (random.random(), random.random(), random.random(), 
                   random.random(), random.random(), random.random())
    
    def _is_frame_unique(self, frame_hash, existing_hashes, similarity_threshold=0.15):
        """Check if frame is sufficiently different from existing frames"""
        if not existing_hashes:
            return True
        
        try:
            # Calculate similarity to existing frames
            for existing_hash in existing_hashes:
                # Calculate Euclidean distance between hash tuples
                distance = sum((a - b) ** 2 for a, b in zip(frame_hash, existing_hash)) ** 0.5
                
                # Normalize distance (max possible distance is ~sqrt(6*255^2) for RGB)
                normalized_distance = distance / (255 * 2.45)  # Approximate normalization
                
                if normalized_distance < similarity_threshold:
                    return False  # Too similar to existing frame
            
            return True  # Sufficiently unique
            
        except Exception as e:
            print(f"   ⚠️  Frame uniqueness check failed: {e}, assuming unique")
            return True
    
    def _resize_thumbnail(self, img):
        """Resize thumbnail to target dimensions while maintaining aspect ratio"""
        target_width = self.thumbnail_width
        target_height = self.thumbnail_height
        
        # Calculate aspect ratios
        img_aspect = img.width / img.height
        target_aspect = target_width / target_height
        
        if img_aspect > target_aspect:
            # Image is wider than target, fit to width
            new_width = target_width
            new_height = int(target_width / img_aspect)
        else:
            # Image is taller than target, fit to height
            new_height = target_height
            new_width = int(target_height * img_aspect)
        
        # Resize image
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create final image with target dimensions and center the resized image
        final_img = Image.new('RGB', (target_width, target_height), (0, 0, 0))
        
        # Center the image
        x_offset = (target_width - new_width) // 2
        y_offset = (target_height - new_height) // 2
        final_img.paste(img_resized, (x_offset, y_offset))
        
        return final_img
    
    def _fallback_thumbnail_generation(self, segments):
        """Fallback thumbnail generation with enhanced strategies"""
        print("🔄 Using fallback thumbnail generation...")
        
        # Try YouTube timestamp-specific thumbnails first
        youtube_thumbnails = self._try_youtube_timestamp_thumbnails(segments)
        if youtube_thumbnails and any(youtube_thumbnails):
            print("✅ Using YouTube timestamp thumbnails")
            return youtube_thumbnails
        
        # Fall back to custom generated thumbnails
        if self.video_id:
            try:
                print("🎨 Generating custom styled thumbnails...")
                return self._generate_custom_thumbnails(segments)
            except Exception as e:
                print(f"❌ Custom thumbnail generation failed: {e}")
        
        return [None] * len(segments)
    
    def _try_youtube_timestamp_thumbnails(self, segments):
        """Try to get YouTube's timestamp-specific thumbnails"""
        if not self.video_id:
            return None
        
        thumbnails = []
        successful_downloads = 0
        
        print("🎬 Attempting to download YouTube timestamp thumbnails...")
        
        for i, segment in enumerate(segments):
            thumbnail_path = None
            timestamp = int(segment['start'])
            
            # YouTube thumbnail URLs for different moments
            thumbnail_urls = [
                f"https://img.youtube.com/vi/{self.video_id}/maxres{i+1}.jpg",  # Different thumbnail variants
                f"https://i3.ytimg.com/vi/{self.video_id}/maxresdefault.jpg",
                f"https://img.youtube.com/vi/{self.video_id}/hqdefault.jpg",
            ]
            
            for url_idx, url in enumerate(thumbnail_urls):
                try:
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    
                    # Check if we got a valid image
                    img = Image.open(io.BytesIO(response.content))
                    
                    # Apply timestamp-specific styling to make them unique
                    img = self._style_timestamp_thumbnail(img, i, segment, timestamp)
                    
                    # Resize and save
                    img = self._resize_thumbnail(img)
                    thumbnail_path = self.output_dir / f"thumbnail_{i+1:03d}.png"
                    img.save(thumbnail_path, "PNG", quality=95)
                    
                    print(f"✅ Downloaded YouTube thumbnail {i+1} (variant {url_idx+1})")
                    successful_downloads += 1
                    break
                    
                except Exception as e:
                    print(f"⚠️  Failed to download thumbnail variant {url_idx+1} for segment {i+1}: {e}")
                    continue
            
            thumbnails.append(str(thumbnail_path) if thumbnail_path else None)
        
        if successful_downloads > 0:
            print(f"✅ Successfully downloaded {successful_downloads}/{len(segments)} YouTube thumbnails")
            return thumbnails
        
        return None
    
    def _style_timestamp_thumbnail(self, img, index, segment, timestamp):
        """Apply timestamp-specific styling to make YouTube thumbnails unique"""
        # Create a styled version with timestamp overlay and color theming
        styled_img = img.copy().convert('RGB')
        draw = ImageDraw.Draw(styled_img)
        
        # Color schemes for each segment
        color_schemes = [
            {"primary": (255, 87, 51), "secondary": (255, 165, 0)},    # Orange/Yellow
            {"primary": (74, 144, 226), "secondary": (0, 191, 255)},   # Blue/Cyan  
            {"primary": (156, 39, 176), "secondary": (186, 85, 211)},  # Purple/Violet
            {"primary": (76, 175, 80), "secondary": (139, 195, 74)},   # Green/Light Green
            {"primary": (244, 67, 54), "secondary": (255, 152, 0)},    # Red/Orange
            {"primary": (96, 125, 139), "secondary": (176, 190, 197)}, # Blue Grey/Light Blue Grey
        ]
        
        color_scheme = color_schemes[index % len(color_schemes)]
        primary_color = color_scheme["primary"]
        secondary_color = color_scheme["secondary"]
        
        # Add gradient overlay in corner
        overlay = Image.new('RGBA', styled_img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # Create corner overlay
        corner_size = min(styled_img.width // 3, styled_img.height // 3, 200)
        
        # Different corner for each segment
        corners = ["top-left", "top-right", "bottom-right", "bottom-left"]
        corner = corners[index % len(corners)]
        
        if corner == "top-left":
            points = [(0, 0), (corner_size, 0), (0, corner_size)]
        elif corner == "top-right":
            points = [(styled_img.width - corner_size, 0), (styled_img.width, 0), (styled_img.width, corner_size)]
        elif corner == "bottom-right":
            points = [(styled_img.width, styled_img.height - corner_size), (styled_img.width, styled_img.height), (styled_img.width - corner_size, styled_img.height)]
        else:  # bottom-left
            points = [(0, styled_img.height - corner_size), (0, styled_img.height), (corner_size, styled_img.height)]
        
        overlay_draw.polygon(points, fill=primary_color + (120,))
        
        # Add timestamp
        timestamp_text = self._format_timestamp(segment['start'])
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 36)
            small_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
        except IOError:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Position timestamp based on corner
        text_bbox = overlay_draw.textbbox((0, 0), timestamp_text, font=font)
        text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
        
        margin = 15
        if corner == "top-left":
            text_x, text_y = margin, margin
        elif corner == "top-right":
            text_x, text_y = styled_img.width - text_width - margin, margin
        elif corner == "bottom-right":
            text_x, text_y = styled_img.width - text_width - margin, styled_img.height - text_height - margin
        else:  # bottom-left
            text_x, text_y = margin, styled_img.height - text_height - margin
        
        # Add text background
        overlay_draw.rectangle([text_x - 10, text_y - 5, text_x + text_width + 10, text_y + text_height + 5], 
                              fill=secondary_color + (200,))
        overlay_draw.text((text_x, text_y), timestamp_text, fill=(255, 255, 255), font=font)
        
        # Add segment indicator
        segment_text = f"#{index + 1}"
        seg_bbox = overlay_draw.textbbox((0, 0), segment_text, font=small_font)
        seg_width, seg_height = seg_bbox[2] - seg_bbox[0], seg_bbox[3] - seg_bbox[1]
        
        # Position segment indicator opposite to timestamp
        if corner in ["top-left", "bottom-left"]:
            seg_x = styled_img.width - seg_width - margin - 5
        else:
            seg_x = margin + 5
            
        if corner in ["top-left", "top-right"]:
            seg_y = styled_img.height - seg_height - margin - 5
        else:
            seg_y = margin + 5
        
        overlay_draw.ellipse([seg_x - 15, seg_y - 5, seg_x + seg_width + 15, seg_y + seg_height + 5], 
                            fill=primary_color + (255,))
        overlay_draw.text((seg_x, seg_y), segment_text, fill=(255, 255, 255), font=small_font)
        
        # Apply overlay
        styled_img = Image.alpha_composite(styled_img.convert('RGBA'), overlay).convert('RGB')
        
        return styled_img

    def _generate_custom_thumbnails(self, segments):
        """Generate visually distinct thumbnail images for each segment"""
        base_image = self._get_base_thumbnail()
        if not base_image:
            return [None] * len(segments)

        thumbnails = []
        color_schemes = [
            {"gradient": (255, 87, 51), "name": "ORANGE", "brightness": 1.2},
            {"gradient": (74, 144, 226), "name": "BLUE", "brightness": 0.8},
            {"gradient": (156, 39, 176), "name": "PURPLE", "brightness": 1.15},
            {"gradient": (76, 175, 80), "name": "GREEN", "brightness": 0.85},
        ]

        for i, segment in enumerate(segments):
            try:
                img = self._create_themed_image(base_image, i, color_schemes)
                self._add_timestamp_and_segment_info(img, i, segment, color_schemes)
                thumbnail_path = self.output_dir / f"thumbnail_{i+1:03d}.png"
                img.save(thumbnail_path, "PNG")
                thumbnails.append(str(thumbnail_path))
            except Exception as e:
                print(f"Failed to generate custom thumbnail {i+1}: {e}")
                thumbnails.append(None)
        
        print(f"✅ Generated {len([t for t in thumbnails if t])} visually distinct thumbnails")
        return thumbnails

    def _get_base_thumbnail(self):
        """Downloads the base thumbnail from YouTube."""
        for resolution in ["maxresdefault", "hqdefault", "sddefault"]:
            base_thumbnail_url = f"https://img.youtube.com/vi/{self.video_id}/{resolution}.jpg"
            try:
                response = requests.get(base_thumbnail_url, timeout=10)
                response.raise_for_status()
                return Image.open(io.BytesIO(response.content))
            except requests.exceptions.RequestException:
                continue
        return None

    def _create_themed_image(self, base_image, index, color_schemes):
        """Applies a visual theme to the base image."""
        img = base_image.copy()
        color_scheme = color_schemes[index % len(color_schemes)]
        gradient_color = color_scheme["gradient"]

        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(color_scheme["brightness"])

        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(0.8 + (index * 0.1))

        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_alpha = 80
        
        # Simplified overlay patterns
        if index % 4 == 0:  # Top band
            overlay_draw.rectangle([0, 0, img.width, img.height//3], fill=gradient_color + (overlay_alpha,))
        elif index % 4 == 1:  # Right band
            overlay_draw.rectangle([2*img.width//3, 0, img.width, img.height], fill=gradient_color + (overlay_alpha,))
        elif index % 4 == 2:  # Bottom band
            overlay_draw.rectangle([0, 2*img.height//3, img.width, img.height], fill=gradient_color + (overlay_alpha,))
        else:  # Left band
            overlay_draw.rectangle([0, 0, img.width//3, img.height], fill=gradient_color + (overlay_alpha,))

        return Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')

    def _add_timestamp_and_segment_info(self, img, index, segment, color_schemes):
        """Adds timestamp and segment information to the image."""
        draw = ImageDraw.Draw(img)
        timestamp = self._format_timestamp(segment['start'])
        color_scheme = color_schemes[index % len(color_schemes)]
        gradient_color = color_scheme["gradient"]

        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 64)
            small_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 42)
        except IOError:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # Add timestamp
        text_bbox = draw.textbbox((0, 0), timestamp, font=font)
        text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
        margin = 30
        x, y = img.width - text_width - margin, img.height - text_height - margin
        draw.rectangle([x - 20, y - 15, x + text_width + 20, y + text_height + 15], fill=gradient_color)
        draw.text((x, y), timestamp, fill=(255, 255, 255), font=font)

        # Add segment indicator
        segment_text = f"SEGMENT {index+1}"
        segment_bbox = draw.textbbox((0, 0), segment_text, font=small_font)
        segment_width, segment_height = segment_bbox[2] - segment_bbox[0], segment_bbox[3] - segment_bbox[1]
        seg_x, seg_y = margin, margin
        contrast_color = (255 - gradient_color[0], 255 - gradient_color[1], 255 - gradient_color[2])
        draw.rectangle([seg_x - 20, seg_y - 15, seg_x + segment_width + 20, seg_y + segment_height + 15], fill=contrast_color)
        draw.text((seg_x, seg_y), segment_text, fill=gradient_color, font=small_font)

    def _format_timestamp(self, seconds):
        """Format seconds as MM:SS or HH:MM:SS"""
        if seconds < 3600:
            return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
