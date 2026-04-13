"""
main.py — Friday Phase 3

Loop: listen → transcribe → quick-command check → LLM brain → dispatch → speak.
Simple commands (open/close apps, open URLs) are handled instantly without
waiting for the LLM. Only conversational queries go to the brain.
Ctrl+C to exit cleanly.
"""

import sys
import os
import time
import re
import yaml

# Ensure the project root is on the path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from core.listener import Listener
from core.stt import SpeechToText
from core.tts import TextToSpeech
from core.brain import Brain
from core.dispatcher import Dispatcher


def load_config():
    """Load the main config.yaml."""
    config_path = os.path.join(PROJECT_ROOT, "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ─── Quick command patterns ────────────────────────────────────
# These are handled INSTANTLY without calling the LLM.
# Format: (regex_pattern, handler_function_name)

QUICK_COMMANDS = [
    # App launching: "open spotify", "launch notepad", "start vscode"
    (r"(?:open|launch|start|run)\s+(\w+)", "quick_launch_app"),
    # App closing: "close spotify", "quit notepad", "exit brave"
    (r"(?:close|quit|exit|stop|kill)\s+(\w+)", "quick_close_app"),
    # URL opening: "open gmail", "go to youtube"
    (r"(?:open|go\s+to)\s+(gmail|youtube|claude|google|calendar)", "quick_open_url"),
    # Volume: "set volume to 50", "volume 80"
    (r"(?:set\s+)?volume\s+(?:to\s+)?(\d+)", "quick_set_volume"),
    # Routine: "morning routine", "night routine", "run morning routine"
    (r"(?:run\s+)?(\w+)\s+routine", "quick_run_routine"),
]

# Known URLs for quick access
KNOWN_URLS = {
    "gmail": "https://mail.google.com",
    "youtube": "https://youtube.com",
    "claude": "https://claude.ai",
    "google": "https://google.com",
    "calendar": "https://calendar.google.com",
}


def try_quick_command(text: str, config: dict, dispatcher: Dispatcher, tts) -> bool:
    """
    Check if the user input matches a quick command pattern.
    If yes, execute it immediately and return True.
    If no match, return False (will fall through to LLM).

    Args:
        text: Transcribed user input.
        config: The loaded config dict.
        dispatcher: Dispatcher instance for executing actions.
        tts: TextToSpeech instance.

    Returns:
        True if a quick command was handled, False otherwise.
    """
    text_lower = text.lower().strip().rstrip(".")

    apps = config.get("apps", {})

    # --- Check: Open/Launch an app ---
    match = re.search(r"(?:open|launch|start|run)\s+(\w+)", text_lower)
    if match:
        app_name = match.group(1).lower()
        # Check if it's a known app
        if app_name in apps:
            app_path = apps[app_name]
            # If it's a URL entry (like claude_url), open in browser
            if app_path.startswith("http"):
                tts.speak(f"Opening {app_name} in the browser, Boss.")
                result = dispatcher.browser_control.open_url(app_path)
                print(f"    → {result}")
                return True
            else:
                tts.speak(f"Opening {app_name} now, Boss.")
                result = dispatcher.app_launcher.launch(app_name)
                print(f"    → {result}")
                return True
        # Check if it's a known URL alias
        elif app_name in KNOWN_URLS:
            tts.speak(f"Opening {app_name} for you, Boss.")
            result = dispatcher.browser_control.open_url(KNOWN_URLS[app_name])
            print(f"    → {result}")
            return True

    # --- Check: Close an app ---
    match = re.search(r"(?:close|quit|exit|stop|kill)\s+(\w+)", text_lower)
    if match:
        app_name = match.group(1).lower()
        if app_name in apps:
            tts.speak(f"Closing {app_name}, Boss.")
            result = dispatcher.app_launcher.close(app_name)
            print(f"    → {result}")
            return True

    # --- Check: Open URL aliases ---
    match = re.search(r"(?:open|go\s+to)\s+(gmail|youtube|claude|google|calendar)", text_lower)
    if match:
        site = match.group(1).lower()
        if site in KNOWN_URLS:
            tts.speak(f"Opening {site} for you, Boss.")
            result = dispatcher.browser_control.open_url(KNOWN_URLS[site])
            print(f"    → {result}")
            return True

    # --- Check: Volume ---
    match = re.search(r"(?:set\s+)?volume\s+(?:to\s+)?(\d+)", text_lower)
    if match:
        level = int(match.group(1))
        tts.speak(f"Setting volume to {level} percent, Boss.")
        result = dispatcher.system_control.set_volume(level)
        print(f"    → {result}")
        return True

    # No quick command matched — will go to LLM
    return False


def main():
    """Phase 3 loop: listen → transcribe → quick-cmd or LLM → speak."""
    print("=" * 50)
    print("  FRIDAY — Phase 3: App & Browser Control")
    print("=" * 50)
    print()

    config = load_config()
    user_name = config.get("friday", {}).get("user_name", "Boss")

    # Initialize components
    print("[main] Initializing listener...")
    listener = Listener()

    print("[main] Initializing speech-to-text...")
    stt = SpeechToText()

    print("[main] Initializing text-to-speech...")
    tts = TextToSpeech()

    print("[main] Initializing brain...")
    brain = Brain()

    print("[main] Initializing dispatcher...")
    dispatcher = Dispatcher()
    dispatcher.set_tts(tts)

    print()
    print("=" * 50)
    print("  Friday Phase 3 online")
    print(f"  Ready to listen, {user_name}.")
    print("  Try: 'Open Spotify' or 'Open Gmail'")
    print("  Press Ctrl+C to exit.")
    print("=" * 50)
    print()

    tts.speak(f"Friday Phase 3 online. Ready, {user_name}.")
    time.sleep(0.5)

    try:
        while True:
            # Step 1: Listen
            audio = listener.listen()
            if audio is None or len(audio) == 0:
                continue

            # Step 2: Transcribe
            print("[main] Transcribing...")
            text = stt.transcribe(audio)
            if not text:
                print("[main] (no speech recognized)")
                continue

            print(f"\n>>> You: \"{text}\"\n")

            # Step 3: Try quick command first (instant, no LLM needed)
            if try_quick_command(text, config, dispatcher, tts):
                print("[main] Handled via quick command.\n")
                time.sleep(0.5)
                continue

            # Step 4: Not a quick command → send to LLM brain
            print("[main] Sending to brain...")
            response = brain.think(text)
            print(f">>> Friday: {response}\n")

            # Step 5: Execute any [ACTION:] tags
            results = dispatcher.dispatch(response)
            if results:
                for r in results:
                    print(f"    → {r}")

            # Step 6: Speak the clean response
            spoken_text = Brain.strip_action_tags(response)
            if spoken_text:
                tts.speak(spoken_text)
                time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n")
        print("[main] Shutting down...")
        tts.speak(f"Goodbye, {user_name}.")
        print("[main] Friday offline. Goodbye.")
        sys.exit(0)


if __name__ == "__main__":
    main()
