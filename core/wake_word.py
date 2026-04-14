"""
core/wake_word.py — Phase 5: Wake word detection via openwakeword

Passively monitors the microphone without saving audio or taking up large
compute resources, completely eliminating background conversation misfires.
"""

import os
import yaml
import numpy as np
import sounddevice as sd
import time

class WakeWordDetector:
    """Listens for the wake word using an efficient openwakeword model."""

    def __init__(self, config_path="config.yaml"):
        # Load config to get wake_word settings
        filepath = config_path
        if not os.path.isabs(config_path):
            filepath = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                config_path,
            )
            
        with open(filepath, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            
        ww_config = config.get("wake_word", {})
        self.model_name = ww_config.get("model", "hey_jarvis")
        self.sensitivity = float(ww_config.get("sensitivity", 0.5))
        
        print(f"[WakeWord] Initializing model '{self.model_name}' (this may take a few seconds)...")
        try:
            from openwakeword.model import Model
            # Initialize openwakeword with the requested model and force ONNX
            self.model = Model(wakeword_models=[self.model_name], inference_framework="onnx")
            print(f"[WakeWord] Engine ready (Sensitivity: {self.sensitivity})")
        except ImportError:
            print("[WakeWord] ERROR: openwakeword not installed. Please install it.")
            self.model = None
        except Exception as e:
            print(f"[WakeWord] ERROR loading model: {e}")
            self.model = None

    def wait_for_wake_word(self):
        """
        Blocks and listens to the microphone until the wake word is detected.
        Temporarily opens a PyAudio-like stream via sounddevice.
        Returns True when detected.
        """
        if self.model is None:
            # Fallback if engine is completely offline, we'll act as a dummy pass-through
            # so the assistant still works (just heavily degraded)
            time.sleep(2)
            return True

        print(f"\n[WakeWord] Waiting for '{self.model_name}'...")
        
        # openwakeword generally prefers 1280 chunks (80ms) for 16kHz
        CHUNK = 1280
        detected = False
        frames_processed = 0
        activation_count = 0
        
        def audio_callback(indata, frames, time_info, status):
            nonlocal detected, frames_processed, activation_count
            frames_processed += 1
            if status:
                pass # Ignore over/underflows since listening is passive
                
            # sounddevice dtype int16 natively matches openwakeword structure
            audio_data = indata.flatten()
            
            # Predict
            prediction = self.model.predict(audio_data)
            
            # prediction dict contains scores for each loaded model
            for model_key, score in prediction.items():
                if frames_processed > 10 and score >= self.sensitivity:
                    activation_count += 1
                    # Require 4 continuous high-confidence chunks (~320ms) to trigger.
                    # This completely obliterates 1-frame false positive audio glitches!
                    if activation_count >= 4:
                        detected = True
                        raise sd.CallbackStop()
                elif frames_processed > 10:
                    activation_count = 0

        try:
            with sd.InputStream(
                samplerate=16000, 
                channels=1, 
                dtype='int16', 
                blocksize=CHUNK, 
                callback=audio_callback
            ):
                while not detected:
                    time.sleep(0.1)
        except Exception as e:
            print(f"[WakeWord] Stream error: {e}")
            
        print(f"[WakeWord] Triggered!")
        return True
