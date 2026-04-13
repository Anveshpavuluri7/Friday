"""
core/tts.py — Text-to-Speech using pyttsx3 (offline, Windows SAPI).

Initializes a pyttsx3 engine with configurable rate, volume, and voice.
Speaks text aloud using the system's built-in speech synthesis.
"""

import yaml
import os
import sys


class TextToSpeech:
    """Speaks text aloud using pyttsx3 (Windows SAPI voices)."""

    def __init__(self, config_path="config.yaml"):
        """Load config and initialize the TTS engine."""
        # Load config
        config_file = config_path
        if not os.path.isabs(config_path):
            config_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                config_path,
            )

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        tts_config = config.get("tts", {})
        self.rate = tts_config.get("rate", 175)
        self.volume = tts_config.get("volume", 0.9)
        self.voice_index = tts_config.get("voice_index", 0)

        # Initialize pyttsx3 engine
        try:
            import pyttsx3

            self.engine = pyttsx3.init()
        except Exception as e:
            print(f"[TTS] ERROR: Failed to initialize TTS engine: {e}")
            print("[TTS]        Make sure pyttsx3 is installed: pip install pyttsx3")
            self.engine = None
            return

        # Configure engine
        self.engine.setProperty("rate", self.rate)
        self.engine.setProperty("volume", self.volume)

        # Set voice
        voices = self.engine.getProperty("voices")
        if voices:
            print(f"[TTS] Available voices ({len(voices)}):")
            for i, voice in enumerate(voices):
                marker = " <-- selected" if i == self.voice_index else ""
                print(f"       [{i}] {voice.name}{marker}")

            if self.voice_index < len(voices):
                self.engine.setProperty("voice", voices[self.voice_index].id)
            else:
                print(f"[TTS] WARNING: voice_index {self.voice_index} out of range, using default.")
                self.engine.setProperty("voice", voices[0].id)
        else:
            print("[TTS] WARNING: No voices found on this system.")

        print(f"[TTS] Engine ready — rate: {self.rate}, volume: {self.volume}")

    def speak(self, text: str):
        """
        Speak the given text aloud (blocking call).

        Args:
            text: The text string to speak.
        """
        if not text or not text.strip():
            return

        if self.engine is None:
            print(f"[TTS] (engine unavailable) Would say: {text}")
            return

        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"[TTS] ERROR during speech: {e}")
