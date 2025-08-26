import re
from typing import List, Dict, Union, Optional
from app.config import get_setting
import logging

logger = logging.getLogger(__name__)

class IntelligentSegmentFinder:
    """Find interesting segments based on natural language descriptions"""

    def __init__(self, content_description: str = None):
        self.content_description = content_description or ""
        self.context_window = get_setting("segment_finder.context_window", 5)
        
        # Extract key concepts from the description
        self.key_concepts = self._extract_concepts_from_description(self.content_description)
        
    def _extract_concepts_from_description(self, description: str) -> List[str]:
        """Extract key concepts and keywords from natural language description"""
        if not description:
            return get_setting("segment_finder.default_keywords", [])
        
        # Remove common stop words and extract meaningful terms
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 
            'by', 'from', 'that', 'which', 'who', 'where', 'when', 'why', 'how',
            'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'find', 'segments', 'contain', 'focus', 'should'
        }
        
        # Split into words and clean
        words = re.findall(r'\b[a-zA-Z]+\b', description.lower())
        
        # Extract meaningful concepts
        concepts = []
        for word in words:
            if len(word) > 3 and word not in stop_words:
                concepts.append(word)
        
        # Also look for key phrases that indicate important content
        key_phrases = [
            'key', 'important', 'main', 'primary', 'essential', 'critical',
            'concept', 'idea', 'principle', 'theory', 'method', 'approach',
            'example', 'case', 'study', 'demo', 'demonstration', 'practical',
            'insight', 'takeaway', 'lesson', 'learning', 'education',
            'explain', 'explain', 'describe', 'discuss', 'analyze',
            'introduction', 'overview', 'summary', 'conclusion',
            'problem', 'solution', 'challenge', 'opportunity',
            'question', 'answer', 'response', 'clarification'
        ]
        
        # Add phrases found in description
        description_lower = description.lower()
        for phrase in key_phrases:
            if phrase in description_lower:
                concepts.append(phrase)
        
        # Remove duplicates and return
        unique_concepts = list(set(concepts))
        logger.info(f"Extracted concepts from description: {unique_concepts}")
        
        return unique_concepts if unique_concepts else get_setting("segment_finder.default_keywords", [])

    def find_segments(self, transcript_segments: List[Dict[str, Union[float, str]]], num_cards: int) -> List[Dict[str, Union[float, str]]]:
        """Find the most interesting segments based on content description"""
        if not transcript_segments:
            return []
            
        scored_segments = []
        
        # Score each segment
        for i, segment in enumerate(transcript_segments):
            score = self._score_segment(segment, i, transcript_segments)
            if score > 0:
                scored_segments.append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text'],
                    'score': score,
                    'index': i,
                    'concepts': self._get_matching_concepts(segment['text'])
                })
        
        # Sort by score (highest first)
        scored_segments.sort(key=lambda x: x['score'], reverse=True)
        
        # Remove overlapping segments and select best ones
        final_segments = self._select_non_overlapping_segments(scored_segments, transcript_segments, num_cards)
        
        # Apply context window to final segments
        expanded_segments = []
        for segment in final_segments:
            expanded = self._expand_segment_with_context(segment, transcript_segments)
            expanded_segments.append(expanded)
        
        # Sort by start time
        expanded_segments.sort(key=lambda x: x['start'])
        
        logger.info(f"Found {len(expanded_segments)} segments using intelligent matching")
        return expanded_segments
    
    def _score_segment(self, segment: Dict[str, Union[float, str]], index: int, all_segments: List[Dict]) -> float:
        """Score a segment based on how well it matches the content description"""
        text = segment['text'].lower()
        score = 0.0
        
        # Base scoring: concept matching
        concept_matches = 0
        for concept in self.key_concepts:
            if concept in text:
                concept_matches += 1
                # Give extra weight to exact matches
                score += 2.0
                # Bonus for multiple occurrences
                score += text.count(concept) * 0.5
        
        # Bonus for multiple concepts in same segment
        if concept_matches > 1:
            score += concept_matches * 1.5
        
        # Look for educational/explanatory patterns
        educational_patterns = [
            r'\bexplain\b', r'\bexample\b', r'\bfor instance\b', r'\bsuch as\b',
            r'\bimportant\b', r'\bkey\b', r'\bmain\b', r'\bprimary\b',
            r'\bfirst\b', r'\bsecond\b', r'\bthird\b', r'\bnext\b',
            r'\bso\b', r'\bbecause\b', r'\btherefore\b', r'\bhowever\b',
            r'\bin other words\b', r'\bwhat this means\b', r'\bthe point is\b',
            r'\blet me\b', r'\bif you\b', r'\byou need to\b', r'\byou should\b'
        ]
        
        pattern_matches = 0
        for pattern in educational_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                pattern_matches += 1
                score += 1.0
        
        # Bonus for segments with questions or answers
        if '?' in segment['text'] or re.search(r'\b(question|answer|ask)\b', text, re.IGNORECASE):
            score += 1.5
        
        # Prefer longer segments with more content
        word_count = len(text.split())
        if word_count > 20:
            score += 0.5
        if word_count > 40:
            score += 0.5
        
        # Slight penalty for very short segments
        if word_count < 10:
            score -= 0.5
        
        # Position-based scoring (slight preference for intro/outro)
        total_segments = len(all_segments)
        if index < total_segments * 0.1:  # First 10%
            score += 0.5
        elif index > total_segments * 0.9:  # Last 10%
            score += 0.3
        
        return max(0, score)
    
    def _get_matching_concepts(self, text: str) -> List[str]:
        """Get list of concepts that match in this text"""
        text_lower = text.lower()
        return [concept for concept in self.key_concepts if concept in text_lower]
    
    def _select_non_overlapping_segments(self, scored_segments: List[Dict], all_segments: List[Dict], num_cards: int) -> List[Dict]:
        """Select best segments while avoiding temporal overlap"""
        if not scored_segments:
            return []
            
        selected = []
        used_ranges = []
        
        for segment in scored_segments:
            if len(selected) >= num_cards:
                break
            
            # Check if this segment overlaps with any already selected
            segment_start = segment['start']
            segment_end = segment['end']
            
            # Add buffer to avoid very close segments
            buffer = 30  # 30 seconds
            
            overlaps = False
            for used_start, used_end in used_ranges:
                if (segment_start < used_end + buffer and segment_end > used_start - buffer):
                    overlaps = True
                    break
            
            if not overlaps:
                selected.append(segment)
                used_ranges.append((segment_start, segment_end))
        
        # If we don't have enough segments, relax overlap constraints
        if len(selected) < min(num_cards, len(scored_segments)):
            remaining_needed = num_cards - len(selected)
            for segment in scored_segments:
                if len(selected) >= num_cards:
                    break
                if segment not in selected:
                    selected.append(segment)
        
        return selected[:num_cards]
    
    def _expand_segment_with_context(self, segment: Dict, all_segments: List[Dict]) -> Dict:
        """Expand segment with surrounding context"""
        segment_index = segment['index']
        
        # Calculate context window
        start_idx = max(0, segment_index - self.context_window)
        end_idx = min(len(all_segments), segment_index + self.context_window + 1)
        
        # Get context segments
        context_segments = all_segments[start_idx:end_idx]
        
        if context_segments:
            # Combine text from context
            combined_text = ' '.join([s['text'] for s in context_segments])
            
            return {
                'start': context_segments[0]['start'],
                'end': context_segments[-1]['end'],
                'text': combined_text,
                'score': segment['score'],
                'concepts': segment.get('concepts', []),
                'keyword': ', '.join(segment.get('concepts', ['intelligent'])[:3])  # For compatibility
            }
        else:
            # Fallback to original segment
            return {
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text'],
                'score': segment['score'],
                'concepts': segment.get('concepts', []),
                'keyword': ', '.join(segment.get('concepts', ['intelligent'])[:3])
            }