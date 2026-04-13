"""
core/listener.py — Microphone listener with Voice Activity Detection.

Opens the default mic via sounddevice, buffers 30ms frames, uses webrtcvad
to detect speech. Records until 1.5s of silence, then returns the audio
as a float32 numpy array suitable for Whisper.
"""

import numpy as np
import sounddevice as sd
import webrtcvad
import yaml
import os
import collections
import sys
import time


class Listener:
    """Captures voice from the microphone using VAD-based endpoint detection."""

    # Audio parameters — webrtcvad requires 16 kHz, 16-bit mono
    SAMPLE_RATE = 16000
    CHANNELS = 1
    DTYPE = "int16"
    FRAME_DURATION_MS = 30  # webrtcvad supports 10, 20, or 30 ms
    FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)  # 480 samples

    # How many consecutive silent frames = "silence detected"
    # 1.5s / 30ms = 50 frames
    SILENCE_FRAMES_THRESHOLD = 50

    # Maximum recording duration in seconds (safety timeout)
    MAX_RECORD_SECONDS = 30

    # Minimum frames of speech before we consider it a valid utterance
    MIN_SPEECH_FRAMES = 5  # ~150ms — filters out clicks/noise

    def __init__(self, config_path="config.yaml"):
        """Load config and initialize VAD."""
        # Load config
        config_file = config_path
        if not os.path.isabs(config_path):
            config_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                config_path,
            )

        with open(config_file, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        # Initialize VAD — aggressiveness 3 (most aggressive = best at
        # filtering out non-speech noise on laptop mics)
        self.vad = webrtcvad.Vad(3)

        # Verify a mic is available
        try:
            device_info = sd.query_devices(kind="input")
            self.device_name = device_info["name"]
            print(f"[Listener] Microphone found: {self.device_name}")
        except sd.PortAudioError:
            print("[Listener] ERROR: No microphone found!")
            print("           Please connect a microphone and try again.")
            sys.exit(1)

    def listen(self) -> np.ndarray:
        """
        Block until speech is detected, record it, and return audio buffer.

        Returns:
            np.ndarray: float32 audio array normalized to [-1, 1]
                        at 16 kHz — ready for Whisper.
        """
        print("[Listener] Listening... (speak now)")

        # Ring buffer to look back a few frames so we don't clip the start
        ring_buffer = collections.deque(maxlen=10)
        audio_frames = []
        is_recording = False
        silent_frame_count = 0
        speech_frame_count = 0
        total_frames = 0
        max_frames = int(self.MAX_RECORD_SECONDS * 1000 / self.FRAME_DURATION_MS)

        # Track time for progress dots
        last_dot_time = time.time()

        # Open a blocking stream — reads one frame at a time
        with sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=self.CHANNELS,
            dtype=self.DTYPE,
            blocksize=self.FRAME_SIZE,
        ) as stream:
            while True:
                # Read one frame (30ms = 480 samples)
                frame_data, overflowed = stream.read(self.FRAME_SIZE)
                if overflowed:
                    pass  # Dropping overflow — not critical

                # Convert to bytes for webrtcvad
                frame_bytes = frame_data.tobytes()

                # Check if this frame contains speech
                try:
                    is_speech = self.vad.is_speech(
                        frame_bytes, self.SAMPLE_RATE
                    )
                except Exception:
                    is_speech = False

                if not is_recording:
                    # Buffer frames so we capture the start of speech
                    ring_buffer.append(frame_data.copy())

                    if is_speech:
                        speech_frame_count += 1

                        # Start recording after a few speech frames
                        if speech_frame_count >= self.MIN_SPEECH_FRAMES:
                            is_recording = True
                            silent_frame_count = 0
                            total_frames = 0
                            print("[Listener] Speech detected — recording...", end="", flush=True)

                            # Prepend ring buffer to not lose the beginning
                            for buffered_frame in ring_buffer:
                                audio_frames.append(buffered_frame)
                                total_frames += 1
                            ring_buffer.clear()
                    else:
                        speech_frame_count = 0
                else:
                    # We are recording
                    audio_frames.append(frame_data.copy())
                    total_frames += 1

                    if is_speech:
                        silent_frame_count = 0
                    else:
                        silent_frame_count += 1

                    # Print a dot every second for progress feedback
                    now = time.time()
                    if now - last_dot_time >= 1.0:
                        print(".", end="", flush=True)
                        last_dot_time = now

                    # Stop if silence exceeds threshold (1.5 seconds)
                    if silent_frame_count >= self.SILENCE_FRAMES_THRESHOLD:
                        print()  # newline after dots
                        print("[Listener] Silence detected — done recording.")
                        break

                    # Safety timeout — don't record forever
                    if total_frames >= max_frames:
                        print()  # newline after dots
                        print(f"[Listener] Max recording time ({self.MAX_RECORD_SECONDS}s) reached.")
                        break

        # Concatenate all frames into one array
        if not audio_frames:
            return np.array([], dtype=np.float32)

        audio_int16 = np.concatenate(audio_frames, axis=0).flatten()

        # Convert int16 → float32 normalized to [-1.0, 1.0] for Whisper
        audio_float32 = audio_int16.astype(np.float32) / 32768.0

        duration = len(audio_float32) / self.SAMPLE_RATE
        print(f"[Listener] Captured {duration:.1f}s of audio.")

        return audio_float32
