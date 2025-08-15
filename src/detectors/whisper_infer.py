import numpy as np
import whisper
import torch
from typing import Optional
import io
import tempfile
import wave

class WhisperKeywordDetector:
    def __init__(self, model_name: str = "tiny"):
        """Initialize Whisper model for keyword detection."""
        self.model = whisper.load_model(model_name)
        self.help_keywords = ["help", "救命", "HELP", "Help", "救命啊"]
        
    def detect_help_keyword(self, audio_chunk: np.ndarray, sample_rate: int = 16000) -> bool:
        """
        Detect help keywords in audio chunk.
        Args:
            audio_chunk: Audio data as numpy array
            sample_rate: Sample rate of audio
        Returns:
            bool: True if help keyword detected
        """
        try:
            # Ensure audio is float32 and normalized
            if audio_chunk.dtype != np.float32:
                audio_chunk = audio_chunk.astype(np.float32)
            
            # Normalize audio to [-1, 1] range
            if np.max(np.abs(audio_chunk)) > 1.0:
                audio_chunk = audio_chunk / np.max(np.abs(audio_chunk))
            
            # Skip if audio is too quiet
            if np.max(np.abs(audio_chunk)) < 0.01:
                return False
                
            # Transcribe audio using Whisper
            result = self.model.transcribe(audio_chunk, language=None)
            text = result["text"].strip().lower()
            
            # Check for help keywords
            for keyword in self.help_keywords:
                if keyword.lower() in text:
                    print(f"Detected keyword: '{keyword}' in text: '{text}'")
                    return True
                    
            return False
            
        except Exception as e:
            print(f"Error in keyword detection: {e}")
            return False
    
    def audio_chunk_to_whisper_format(self, audio_chunk: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
        """Convert audio chunk to format suitable for Whisper."""
        # Whisper expects 16kHz mono audio
        if sample_rate != 16000:
            # Simple resampling (in production, use proper resampling)
            ratio = 16000 / sample_rate
            new_length = int(len(audio_chunk) * ratio)
            audio_chunk = np.interp(
                np.linspace(0, len(audio_chunk), new_length),
                np.arange(len(audio_chunk)),
                audio_chunk
            )
        
        return audio_chunk

# Global detector instance
_whisper_detector = None

def detect_help_keyword(audio_chunk: np.ndarray, sample_rate: int = 16000) -> bool:
    """
    Legacy function for backward compatibility.
    Detect help keywords using global detector instance.
    """
    global _whisper_detector
    if _whisper_detector is None:
        _whisper_detector = WhisperKeywordDetector()
    return _whisper_detector.detect_help_keyword(audio_chunk, sample_rate)
