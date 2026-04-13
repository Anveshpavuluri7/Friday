"""
modules/system_control.py — System-level controls.

Volume control, and other Windows system commands.
"""

import subprocess
import os


class SystemControl:
    """Controls system-level settings like volume."""

    def __init__(self):
        """Initialize system control."""
        print("[SystemControl] Ready.")

    def set_volume(self, level: int) -> str:
        """
        Set the system volume level.

        Uses PowerShell to set the Windows master volume.

        Args:
            level: Volume level from 0 to 100.

        Returns:
            Result message string.
        """
        level = max(0, min(100, level))

        try:
            # Use nircmd if available (most reliable)
            # Fallback to PowerShell + audio COM object
            ps_script = f"""
            $wshShell = New-Object -ComObject WScript.Shell
            # Mute then set volume (workaround)
            1..50 | ForEach-Object {{ $wshShell.SendKeys([char]174) }}
            $steps = [math]::Round({level} / 2)
            1..$steps | ForEach-Object {{ $wshShell.SendKeys([char]175) }}
            """

            subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                timeout=10,
            )
            return f"Volume set to approximately {level}%."

        except Exception as e:
            # Alternative: use pycaw if available
            try:
                return self._set_volume_pycaw(level)
            except Exception:
                return f"Could not set volume: {e}"

    def _set_volume_pycaw(self, level: int) -> str:
        """Set volume using pycaw (if installed)."""
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None
            )
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            # SetMasterVolumeLevelScalar takes 0.0 to 1.0
            volume.SetMasterVolumeLevelScalar(level / 100.0, None)
            return f"Volume set to {level}%."
        except ImportError:
            return "pycaw not installed — install with: pip install pycaw"
