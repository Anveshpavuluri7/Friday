"""
modules/app_launcher.py — Launch, focus, and close applications.

Uses subprocess.Popen to launch apps, psutil to check if running,
and pywin32 to bring windows to the foreground.
"""

import subprocess
import os
import yaml
import time


class AppLauncher:
    """Launches, focuses, and closes applications on Windows."""

    def __init__(self, config_path="config.yaml"):
        """Load app paths from config."""
        config_file = config_path
        if not os.path.isabs(config_path):
            config_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                config_path,
            )

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        self.apps = config.get("apps", {})
        print(f"[AppLauncher] Loaded {len(self.apps)} app(s): {', '.join(self.apps.keys())}")

    def _is_running(self, process_name: str) -> bool:
        """Check if a process is currently running."""
        try:
            import psutil
            process_name_lower = process_name.lower()
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'] and process_name_lower in proc.info['name'].lower():
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except ImportError:
            print("[AppLauncher] WARNING: psutil not installed, can't check running status.")
            return False

    def _focus_window(self, window_title_part: str) -> bool:
        """Try to bring a window to the foreground using pywin32."""
        try:
            import win32gui
            import win32con

            def callback(hwnd, results):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if window_title_part.lower() in title.lower():
                        results.append(hwnd)

            results = []
            win32gui.EnumWindows(callback, results)

            if results:
                hwnd = results[0]
                # Restore if minimized
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                # Bring to front
                win32gui.SetForegroundWindow(hwnd)
                return True
            return False
        except ImportError:
            print("[AppLauncher] WARNING: pywin32 not installed, can't focus windows.")
            return False
        except Exception as e:
            print(f"[AppLauncher] Could not focus window: {e}")
            return False

    def launch(self, app_name: str) -> str:
        """
        Launch an application dynamically by searching installed apps, then config fallback.
        """
        app_name_lower = app_name.lower().strip()

        # 1. Search Windows installed apps dynamically via PowerShell
        try:
            cmd = f"Get-StartApps | Where-Object Name -match '{app_name_lower}' | Select-Object -ExpandProperty AppID -First 1"
            result = subprocess.run(
                ["powershell", "-Command", cmd], 
                capture_output=True, 
                text=True, 
                creationflags=0x08000000
            )
            app_id = result.stdout.strip()
            if app_id:
                # Check if it's already running (fuzzy match focus)
                if self._is_running(app_name_lower):
                    if self._focus_window(app_name_lower):
                        return f"{app_name} is already running — brought to focus."
                
                # Launch it
                subprocess.Popen(
                    f"explorer.exe shell:AppsFolder\\{app_id}",
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return f"Launched {app_name} dynamically."
        except Exception as e:
            print(f"[AppLauncher] Dynamic Powershell search error: {e}")

        # 2. Config dictionary fallback
        app_path = self.apps.get(app_name_lower)
        if not app_path:
            for key, path in self.apps.items():
                if app_name_lower in key.lower():
                    app_path = path
                    app_name_lower = key
                    break

        # If it's a known URL or doesn't exist, signal not found
        if not app_path or app_path.startswith("http://") or app_path.startswith("https://") or not os.path.exists(app_path):
            return "APP_NOT_FOUND"

        # Check if already running again just for config path exe_name
        exe_name = os.path.basename(app_path)
        if self._is_running(exe_name):
            if self._focus_window(app_name_lower):
                return f"{app_name} is already running — brought to focus."
            else:
                return f"{app_name} is already running."

        # Launch the app from config
        try:
            subprocess.Popen([app_path], shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Launched {app_name}."
        except Exception as e:
            return f"Error launching {app_name}: {e}"

    def close(self, app_name: str) -> str:
        """
        Close an application by name.

        Uses psutil to find and terminate the process.

        Args:
            app_name: Key from the apps section in config.yaml.

        Returns:
            Result message string.
        """
        app_name_lower = app_name.lower().strip()
        app_path = self.apps.get(app_name_lower, "")
        exe_name = os.path.basename(app_path) if app_path else f"{app_name_lower}.exe"

        try:
            import psutil
            killed = False
            for proc in psutil.process_iter(['name', 'pid']):
                try:
                    if proc.info['name'] and exe_name.lower() in proc.info['name'].lower():
                        proc.terminate()
                        killed = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if killed:
                return f"Closed {app_name}."
            else:
                return f"{app_name} was not running."
        except ImportError:
            return "Cannot close apps — psutil not installed."
        except Exception as e:
            return f"Error closing {app_name}: {e}"
