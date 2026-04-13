"""
core/stt.py — Speech-to-Text using OpenAI Whisper (local, offline).

Loads the Whisper 'base' model on CPU and transcribes audio buffers
(float32 numpy arrays at 16 kHz) to text strings.
"""

import numpy as np
import yaml
import os
import sys


class SpeechToText:
    """Transcribes audio using the local Whisper model."""

    def __init__(self, config_path="config.yaml"):
        """Load config and initialize the Whisper model."""
        # Load config
        config_file = config_path
        if not os.path.isabs(config_path):
            config_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                config_path,
            )

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        stt_config = config.get("stt", {})
        self.model_name = stt_config.get("model", "base")
        self.language = stt_config.get("language", "en")
        self.device = stt_config.get("device", "cpu")

        # Lazy-load whisper to avoid import overhead until needed
        self.model = None

    def _load_model(self):
        """Load the Whisper model (downloads on first run)."""
        if self.model is not None:
            return

        print(f"[STT] Loading Whisper model '{self.model_name}' on {self.device}...")
        print("[STT] NOTE: First run will download the model (~140 MB).")
        print("[STT]       This requires an internet connection just once.")

        try:
            import whisper

            self.model = whisper.load_model(
                self.model_name, device=self.device
            )
            print(f"[STT] Whisper '{self.model_name}' model loaded successfully.")
        except Exception as e:
            print(f"[STT] ERROR: Failed to load Whisper model: {e}")
            sys.exit(1)

    def transcribe(self, audio_buffer: np.ndarray) -> str:
        """
        Transcribe an audio buffer to text.

        Args:
            audio_buffer: float32 numpy array at 16 kHz, values in [-1, 1].

        Returns:
            Transcribed text string, stripped of whitespace.
        """
        self._load_model()

        if audio_buffer is None or len(audio_buffer) == 0:
            return ""

        # Whisper expects float32 array at 16 kHz — which is what we have
        # Ensure it's 1D
        audio = audio_buffer.flatten().astype(np.float32)

        try:
            result = self.model.transcribe(
                audio,
                language=self.language,
                fp16=False,  # CPU doesn't support fp16
            )
            text = result.get("text", "").strip()
            return text
        except Exception as e:
            print(f"[STT] ERROR during transcription: {e}")
            return ""
