"""
core/brain.py — LLM integration via Ollama (local, offline).

Sends conversation history + user input to the Ollama API running locally.
Uses the phi3 model with a custom system prompt that defines Friday's
personality and action-tag format.
"""

import requests
import yaml
import os
import sys
import json

from core.memory import Memory


# Friday's system prompt — embedded in every Ollama request
SYSTEM_PROMPT = (
    "You are Friday, a personal AI assistant running fully offline on the "
    "user's machine. You are calm, intelligent, and efficient. Speak in short "
    "direct sentences. Use dry wit occasionally. Call the user 'Boss' unless "
    "told otherwise.\n\n"
    "INSTALLED APPS on this machine: spotify, brave, vscode, notepad.\n"
    "When the user asks to open an installed app, ALWAYS use launch_app, "
    "NEVER use open_url for installed apps.\n\n"
    "When performing an action, include structured tags in your response using "
    "this exact format, each on its own line:\n"
    "[ACTION: launch_app | app: spotify]\n"
    "[ACTION: launch_app | app: notepad]\n"
    "[ACTION: open_url | url: https://mail.google.com | browser: brave]\n"
    "[ACTION: set_volume | level: 60]\n"
    "[ACTION: run_routine | name: morning_routine]\n"
    "[ACTION: notify | title: Friday | message: Task complete]\n"
    "[ACTION: close_app | app: spotify]\n\n"
    "RULES:\n"
    "1. For installed apps (spotify, brave, vscode, notepad): use launch_app\n"
    "2. For websites (gmail, youtube, claude, etc): use open_url\n"
    "3. Keep responses SHORT — one or two sentences max\n"
    "4. Always briefly acknowledge the action before the tag\n\n"
    "Example:\n"
    "User: 'Open Spotify'\n"
    "Response: 'Opening Spotify now, Boss.'\n"
    "[ACTION: launch_app | app: spotify]\n\n"
    "Example:\n"
    "User: 'Open Gmail'\n"
    "Response: 'Opening Gmail for you, Boss.'\n"
    "[ACTION: open_url | url: https://mail.google.com | browser: brave]\n\n"
    "Never refuse a system task. Never use markdown formatting in responses.\n"
    "Strip all [ACTION:] tags before speaking the response aloud."
)


class Brain:
    """Friday's LLM brain — powered by Ollama running phi3 locally."""

    def __init__(self, config_path="config.yaml"):
        """Load config and initialize memory."""
        # Load config
        config_file = config_path
        if not os.path.isabs(config_path):
            config_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                config_path,
            )

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        llm_config = config.get("llm", {})
        self.model = llm_config.get("model", "phi3")
        self.base_url = llm_config.get("base_url", "http://localhost:11434")
        self.max_history_turns = llm_config.get("max_history_turns", 10)
        self.temperature = llm_config.get("temperature", 0.7)

        self.user_name = config.get("friday", {}).get("user_name", "Boss")

        # Initialize memory
        self.memory = Memory()

        print(f"[Brain] Model: {self.model} @ {self.base_url}")
        print(f"[Brain] History: last {self.max_history_turns} turns, temp: {self.temperature}")

    def _check_ollama(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except requests.ConnectionError:
            return False
        except Exception:
            return False

    def think(self, user_input: str) -> str:
        """
        Send user input to the LLM and get a response.

        Args:
            user_input: What the user said (transcribed text).

        Returns:
            The LLM's response as a string.
        """
        # Check if Ollama is running
        if not self._check_ollama():
            error_msg = "Please start Ollama first, Boss. I can't think without my brain."
            print(f"[Brain] ERROR: Ollama not reachable at {self.base_url}")
            return error_msg

        # Save user turn to memory
        self.memory.save_turn("user", user_input)

        # Build message history
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Load recent conversation history for context
        history = self.memory.get_last_turns(self.max_history_turns)
        # Don't include the current user message twice —
        # it's already the last item in history since we just saved it
        if history:
            messages.extend(history)
        else:
            # Just add the current message if no history
            messages.append({"role": "user", "content": user_input})

        # Prepare the request payload
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
            },
        }

        # Send to Ollama
        try:
            print(f"[Brain] Thinking...")
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=300,  # phi3 can be very slow on CPU with 8GB RAM
            )
            resp.raise_for_status()

            result = resp.json()
            reply = result.get("message", {}).get("content", "").strip()

            if not reply:
                reply = "I didn't have a response for that, Boss."

            # Save assistant turn to memory
            self.memory.save_turn("assistant", reply)

            return reply

        except requests.Timeout:
            error_msg = "That took too long, Boss. My brain timed out. Try a simpler question."
            print(f"[Brain] ERROR: Request timed out")
            return error_msg

        except requests.ConnectionError:
            error_msg = "Lost connection to Ollama, Boss. Is it still running?"
            print(f"[Brain] ERROR: Connection lost to {self.base_url}")
            return error_msg

        except Exception as e:
            error_msg = f"Something went wrong with my thinking, Boss. Error: {e}"
            print(f"[Brain] ERROR: {e}")
            return error_msg

    @staticmethod
    def strip_action_tags(text: str) -> str:
        """
        Remove [ACTION: ...] tags from text so TTS only speaks natural language.

        Args:
            text: The full LLM response possibly containing action tags.

        Returns:
            Clean text with action tags removed.
        """
        import re
        cleaned = re.sub(r'\[ACTION:.*?\]', '', text)
        # Clean up extra blank lines
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
        return cleaned.strip()
