from app.config import get_setting

class SegmentFinder:
    """Find interesting segments based on keywords"""

    def __init__(self, keywords=None):
        if keywords:
            self.keywords = [kw.lower() for kw in keywords]
        else:
            self.keywords = [kw.lower() for kw in get_setting("segment_finder.default_keywords", [])]
        
        self.context_window = get_setting("segment_finder.context_window", 5)

    def find_segments(self, transcript_segments, num_cards):
        """Find the most interesting segments"""
        keyword_segments = []
        
        # Find segments containing keywords
        for i, segment in enumerate(transcript_segments):
            text_lower = segment['text'].lower()
            for keyword in self.keywords:
                if keyword in text_lower:
                    keyword_segments.append({
                        'start': segment['start'],
                        'end': segment['end'],
                        'text': segment['text'],
                        'keyword': keyword,
                        'score': len([kw for kw in self.keywords if kw in text_lower]),
                        'index': i
                    })
                    break
        
        # Sort by score and remove duplicates based on original segment ranges
        keyword_segments.sort(key=lambda x: x['score'], reverse=True)
        unique_segments = []
        used_indices = set()
        
        for segment in keyword_segments:
            if segment['index'] not in used_indices:
                unique_segments.append(segment)
                used_indices.add(segment['index'])

        # Now, apply the context window to the unique segments
        final_segments = []
        for segment in unique_segments[:num_cards]:
            start_idx = max(0, segment['index'] - self.context_window)
            end_idx = min(len(transcript_segments), segment['index'] + self.context_window + 1)
            
            context_segments = transcript_segments[start_idx:end_idx]
            combined_text = ' '.join([s['text'] for s in context_segments])
            
            final_segments.append({
                'start': context_segments[0]['start'],
                'end': context_segments[-1]['end'],
                'text': combined_text,
                'keyword': segment['keyword'],
                'score': segment['score']
            })

        final_segments.sort(key=lambda x: x['start'])
        return final_segments
