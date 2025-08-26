import re
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from app.config import get_setting

class AISummarizer:
    """AI-powered text summarization"""

    def __init__(self):
        self.summarizer = None
        self.model_name = get_setting("summarizer.model", "facebook/bart-large-cnn")
        self.max_length = get_setting("summarizer.max_length", 60)
        self.min_length = get_setting("summarizer.min_length", 10)
        self._init_model()

    def _init_model(self):
        """Initialize the summarization model"""
        try:
            print("🤖 Loading AI summarization model...")
            self.summarizer = pipeline(
                "summarization",
                model=self.model_name,
                device=0 if torch.cuda.is_available() else -1
            )
            print("✅ AI model loaded successfully!")
        except Exception as e:
            print(f"⚠️  AI model failed to load: {e}")
            print("Falling back to extractive summarization")
            self.summarizer = None

    def summarize(self, text):
        """Summarize text using AI or fallback method"""
        if not text or len(text.strip()) < 20:
            return text

        if self.summarizer:
            try:
                # BART works best with 100-1024 tokens
                if len(text) > 1024:
                    text = text[:1024]
                
                result = self.summarizer(
                    text,
                    max_length=self.max_length,
                    min_length=self.min_length,
                    do_sample=False
                )
                return result[0]['summary_text']
            except Exception as e:
                print(f"AI summarization failed: {e}")

        # Fallback: extractive summarization
        return self._extractive_summary(text)

    def _extractive_summary(self, text):
        """Simple extractive summarization"""
        sentences = re.split(r'(?<=[.!?])\s*', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        if not sentences:
            return text[:self.max_length] + "..." if len(text) > self.max_length else text
        
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            score = 0
            if i == 0 or i == len(sentences) - 1:
                score += 2
            important_words = ['important', 'key', 'main', 'first', 'finally', 'conclusion']
            for word in important_words:
                if word in sentence.lower():
                    score += 1
            
            scored_sentences.append((score, sentence))
        
        scored_sentences.sort(reverse=True)
        selected = []
        total_length = 0
        
        for score, sentence in scored_sentences:
            if total_length + len(sentence) <= self.max_length:
                selected.append(sentence)
                total_length += len(sentence)
            if total_length >= self.max_length * 0.8:
                break
        
        return ' '.join(selected) if selected else sentences[0][:self.max_length]
