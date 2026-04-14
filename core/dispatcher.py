"""
core/dispatcher.py — Action tag parser and router.

Scans LLM responses for [ACTION: ...] tags, parses the parameters,
and routes them to the appropriate module (app_launcher, browser_control,
system_control, routine_engine).
"""

import re
import yaml
import os


class Dispatcher:
    """Parses [ACTION:] tags from LLM responses and executes them."""

    # Regex to match [ACTION: type | key: value | key: value ...]
    ACTION_PATTERN = re.compile(r'\[ACTION:\s*(.+?)\]')

    def __init__(self, config_path="config.yaml"):
        """Load config and initialize action modules."""
        config_file = config_path
        if not os.path.isabs(config_path):
            config_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                config_path,
            )

        with open(config_file, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        # Lazy-load modules to avoid circular imports
        self._app_launcher = None
        self._browser_control = None
        self._system_control = None
        self._routine_engine = None
        self._tts = None

        print("[Dispatcher] Ready to process action tags.")

    @property
    def app_launcher(self):
        """Lazy-load the app launcher module."""
        if self._app_launcher is None:
            from modules.app_launcher import AppLauncher
            self._app_launcher = AppLauncher()
        return self._app_launcher

    @property
    def browser_control(self):
        """Lazy-load the browser control module."""
        if self._browser_control is None:
            from modules.browser_control import BrowserControl
            self._browser_control = BrowserControl()
        return self._browser_control

    @property
    def system_control(self):
        """Lazy-load the system control module."""
        if self._system_control is None:
            from modules.system_control import SystemControl
            self._system_control = SystemControl()
        return self._system_control

    @property
    def tts(self):
        """Lazy-load TTS for speak actions."""
        if self._tts is None:
            from core.tts import TextToSpeech
            self._tts = TextToSpeech()
        return self._tts

    def set_tts(self, tts):
        """Set the TTS instance (avoids creating a second engine)."""
        self._tts = tts

    def parse_action(self, action_str: str) -> dict:
        """
        Parse an action string like 'launch_app | app: spotify' into a dict.

        Args:
            action_str: The content inside [ACTION: ...]

        Returns:
            dict with 'action' key and parameter key-value pairs.
            e.g. {'action': 'launch_app', 'app': 'spotify'}
        """
        parts = [p.strip() for p in action_str.split('|')]
        if not parts:
            return {}

        result = {'action': parts[0].strip()}

        for part in parts[1:]:
            if ':' in part:
                key, value = part.split(':', 1)
                result[key.strip()] = value.strip()

        return result

    def extract_actions(self, text: str) -> list:
        """
        Extract all [ACTION:] tags from LLM response text.

        Args:
            text: The full LLM response.

        Returns:
            List of parsed action dicts.
        """
        matches = self.ACTION_PATTERN.findall(text)
        actions = []
        for match in matches:
            parsed = self.parse_action(match)
            if parsed:
                actions.append(parsed)
        return actions

    def dispatch(self, text: str) -> list:
        """
        Extract and execute all actions from LLM response text.

        Args:
            text: The full LLM response containing [ACTION:] tags.

        Returns:
            List of result strings for each action executed.
        """
        actions = self.extract_actions(text)
        results = []

        if not actions:
            return results

        print(f"[Dispatcher] Found {len(actions)} action(s) to execute.")

        for action in actions:
            action_type = action.get('action', '')
            print(f"[Dispatcher] Executing: {action_type} — {action}")

            try:
                result = self._execute_action(action)
                results.append(result)
                print(f"[Dispatcher] Result: {result}")
            except Exception as e:
                error_msg = f"Error executing {action_type}: {e}"
                results.append(error_msg)
                print(f"[Dispatcher] ERROR: {error_msg}")

        return results

    def _execute_action(self, action: dict) -> str:
        """
        Route and execute a single action.

        Args:
            action: Parsed action dict with 'action' key and params.

        Returns:
            Result string describing what happened.
        """
        action_type = action.get('action', '').lower().strip()

        if action_type == 'launch_app':
            app_name = action.get('app', '')
            result = self.app_launcher.launch(app_name)
            
            # Fallback to web if APP_NOT_FOUND
            if result == "APP_NOT_FOUND":
                print(f"[Dispatcher] '{app_name}' not found installed natively, attempting web fallback.")
                known_urls = {
                    'claude': 'https://claude.ai',
                    'gmail': 'https://mail.google.com',
                    'youtube': 'https://youtube.com',
                    'calendar': 'https://calendar.google.com'
                }
                url = known_urls.get(app_name.lower(), f"https://{app_name}.com")
                return self.browser_control.open_url(url, "brave")
            
            return result

        elif action_type == 'close_app':
            app_name = action.get('app', '')
            return self.app_launcher.close(app_name)

        elif action_type == 'open_url':
            url = action.get('url', '')
            browser = action.get('browser', 'brave')

            # Smart redirect: if the URL matches a known installed app,
            # launch the app instead of opening the website
            url_to_app = {
                'spotify.com': 'spotify',
                'open.spotify.com': 'spotify',
            }
            for domain, app_name in url_to_app.items():
                if domain in url.lower():
                    print(f"[Dispatcher] Redirecting URL '{url}' → launch_app '{app_name}'")
                    return self.app_launcher.launch(app_name)

            return self.browser_control.open_url(url, browser)

        elif action_type == 'set_volume':
            level = int(action.get('level', 50))
            return self.system_control.set_volume(level)

        elif action_type == 'run_routine':
            routine_name = action.get('name', '')
            # Routine engine will be loaded in Phase 4
            try:
                from modules.routine_engine import RoutineEngine
                engine = RoutineEngine()
                return engine.run(routine_name, self)
            except Exception as e:
                return f"Routine engine not available yet: {e}"

        elif action_type == 'notify':
            title = action.get('title', 'Friday')
            message = action.get('message', '')
            
            # Phase 6: Route securely through our dedicated Notifier UI module
            from ui.notifier import Notifier
            return Notifier.send(title, message)

        elif action_type == 'speak':
            text = action.get('text', '')
            self.tts.speak(text)
            return f"Spoke: {text}"

        elif action_type == 'wait':
            import time
            seconds = int(action.get('seconds', 1))
            time.sleep(seconds)
            return f"Waited {seconds}s"

        else:
            return f"Unknown action: {action_type}"
