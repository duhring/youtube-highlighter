import pytest
from app.summarize import AISummarizer

def test_extractive_summary():
    summarizer = AISummarizer()
    # Disable the AI model to test the fallback
    summarizer.summarizer = None
    
    text = "This is the first sentence. This is the second sentence. This is the third sentence. This is the fourth sentence. This is the fifth sentence."
    summary = summarizer.summarize(text)
    
    # The extractive summary should pick the first and last sentences
    assert "first sentence" in summary
    assert "fifth sentence" in summary
    assert "second sentence" not in summary

def test_short_text_summarization_fallback():
    summarizer = AISummarizer()
    # Disable the AI model to test the fallback
    summarizer.summarizer = None
    text = "This is a short text."
    summary = summarizer.summarize(text)
    assert summary == text
