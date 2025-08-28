import numpy as np
from typing import Optional

class SimpleWhisperDetector:
    """
    Simplified whisper detector that works without OpenAI Whisper.
    Uses basic audio analysis for testing purposes.
    """
    def __init__(self):
        self.help_keywords = ["help", "救命", "HELP", "Help", "救命啊"]
        print("⚠️  Using simplified audio detector (Whisper not available)")
        
    def detect_help_keyword(self, audio_chunk: np.ndarray, sample_rate: int = 16000) -> bool:
        """
        Simple audio analysis - detects based on audio characteristics.
        In a real implementation, this would use speech recognition.
        """
        try:
            # Ensure audio is float32 and normalized
            if audio_chunk.dtype != np.float32:
                audio_chunk = audio_chunk.astype(np.float32)
            
            # Simple heuristics for audio analysis
            if len(audio_chunk) == 0:
                return False
                
            # Calculate audio features
            rms = np.sqrt(np.mean(audio_chunk**2))  # RMS volume
            max_amplitude = np.max(np.abs(audio_chunk))
            
            # Simple detection: loud, sustained sounds might be help calls
            # This is a placeholder - real implementation would use speech recognition
            is_loud = max_amplitude > 0.3
            is_sustained = rms > 0.1
            
            return is_loud and is_sustained
            
        except Exception as e:
            print(f"Error in simple audio detection: {e}")
            return False

# For compatibility
WhisperKeywordDetector = SimpleWhisperDetector
