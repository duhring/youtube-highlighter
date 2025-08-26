import pytest
from app.transcript import TranscriptParser
from pathlib import Path

@pytest.fixture
def sample_vtt_file(tmp_path):
    vtt_content = """WEBVTT
Kind: captions
Language: en

00:00:01.000 --> 00:00:03.000
This is the first caption.

00:00:04.000 --> 00:00:06.000
This is the second caption.
"""
    vtt_file = tmp_path / "sample.vtt"
    vtt_file.write_text(vtt_content)
    return vtt_file

def test_parse_vtt(sample_vtt_file):
    segments = TranscriptParser.parse(str(sample_vtt_file))
    assert len(segments) == 2
    assert segments[0]['start'] == 1.0
    assert segments[0]['end'] == 3.0
    assert segments[0]['text'] == "This is the first caption."
    assert segments[1]['start'] == 4.0
    assert segments[1]['end'] == 6.0
    assert segments[1]['text'] == "This is the second caption."
