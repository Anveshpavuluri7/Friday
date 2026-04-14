"""
gestures/clap_detector.py — Phase 4: Double-clap detection via sounddevice
Continuously monitors the microphone in a background thread for a double-clap
pattern and runs the `clap_trigger` routine when detected.
"""

import numpy as np
import sounddevice as sd
import yaml
import os
import time
import threading

class ClapDetector(threading.Thread):
    def __init__(self, dispatcher, config_path="config.yaml"):
        """Initialize the background thread and load configuration."""
        super().__init__(daemon=True)
        self.dispatcher = dispatcher
        
        # Load config to get clap thresholds
        filepath = config_path
        if not os.path.isabs(config_path):
            filepath = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                config_path,
            )
            
        with open(filepath, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            self.clap_config = config.get("clap", {})
            
        self.threshold = self.clap_config.get("threshold", 0.35)
        self.window_ms = self.clap_config.get("window_ms", 800)
        self.cooldown_s = self.clap_config.get("cooldown_s", 3)
        
        self.last_clap_time = 0
        self.last_trigger_time = 0
        self.is_running = True

    def run(self):
        """Thread loop that listens via sounddevice."""
        print(f"[ClapDetector] Listening for double claps (threshold: {self.threshold})...")
        
        def audio_callback(indata, frames, time_info, status):
            if not self.is_running:
                raise sd.CallbackStop()
                
            now = time.time()
            if now - self.last_trigger_time < self.cooldown_s:
                return  # Cooldown active
                
            # Check for loud peak in this audio frame
            peak = np.max(np.abs(indata))
            if peak > self.threshold:
                # We got a peak. Debounce to prevent one long loud noise from registering multiple claps
                if now - self.last_clap_time > 0.1:  # Must be at least 100ms since last peak
                    if now - self.last_clap_time < (self.window_ms / 1000.0):
                        # It's a double clap!
                        print("\n[ClapDetector] Double clap detected!")
                        self.last_trigger_time = now
                        self.last_clap_time = 0  # Reset for next time
                        
                        # Trigger the routine in a new thread to avoid blocking the audio callback
                        action = {'action': 'run_routine', 'name': 'clap_trigger'}
                        threading.Thread(target=self.dispatcher._execute_action, args=(action,), daemon=True).start()
                    else:
                        # First clap detected, wait for the second
                        self.last_clap_time = now

        try:
            # We use float32 format, mono, at 16kHz
            with sd.InputStream(
                samplerate=16000, 
                channels=1, 
                dtype='float32', 
                blocksize=1600,  # 100ms chunks
                callback=audio_callback
            ):
                while self.is_running:
                    time.sleep(0.1)
        except Exception as e:
            print(f"[ClapDetector] Error starting audio stream: {e}")

    def stop(self):
        """Gracefully stop the background thread."""
        self.is_running = False
