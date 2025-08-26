import pytest
from app.segments import SegmentFinder

@pytest.fixture
def sample_transcript_segments():
    return [
        {'start': 0, 'end': 2, 'text': 'Hello and welcome to our introduction.'},
        {'start': 3, 'end': 5, 'text': 'Today we will be discussing Python.'},
        {'start': 6, 'end': 8, 'text': 'Python is a great language.'},
        {'start': 9, 'end': 11, 'text': 'In conclusion, Python is the best.'},
        {'start': 12, 'end': 14, 'text': 'Thank you for watching.'},
    ]

def test_find_segments_with_keywords(sample_transcript_segments):
    segment_finder = SegmentFinder(keywords=['python', 'conclusion'])
    interesting_segments = segment_finder.find_segments(sample_transcript_segments, 2)
    assert len(interesting_segments) == 2
    assert 'Python' in interesting_segments[0]['text']
    assert 'conclusion' in interesting_segments[1]['text']

def test_find_segments_no_keywords(sample_transcript_segments):
    # This will use the default keywords from the config file
    segment_finder = SegmentFinder()
    interesting_segments = segment_finder.find_segments(sample_transcript_segments, 2)
    assert len(interesting_segments) == 2
