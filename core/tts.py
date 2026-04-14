"""
core/tts.py — Text-to-Speech using pyttsx3 (offline, Windows SAPI).

Initializes a pyttsx3 engine in a dedicated background thread to safely
handle speech from multiple threads without COM threading errors.
"""

import yaml
import os
import sys
import threading
import queue

class TextToSpeech:
    """Speaks text aloud using pyttsx3 (Windows SAPI voices)."""

    def __init__(self, config_path="config.yaml"):
        """Load config and initialize the TTS worker thread."""
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

        self.tts_queue = queue.Queue()
        self.worker = threading.Thread(target=self._tts_worker, daemon=True)
        self.worker.start()

    def _tts_worker(self):
        """Dedicated thread to run pyttsx3 (fixes COM concurrency issues)."""
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
                self.engine.setProperty("voice", voices[0].id)
        
        print(f"[TTS] Engine ready — rate: {self.rate}, volume: {self.volume}")

        while True:
            item = self.tts_queue.get()
            if item is None:
                break
            
            text, event = item
            if self.engine:
                try:
                    self.engine.say(text)
                    self.engine.runAndWait()
                except Exception as e:
                    print(f"[TTS] ERROR during speech: {e}")
            
            event.set()

    def speak(self, text: str):
        """
        Speak the given text aloud (blocking call).

        Args:
            text: The text string to speak.
        """
        if not text or not text.strip():
            return
            
        evt = threading.Event()
        self.tts_queue.put((text, evt))
        evt.wait()
