"""
ui/notifier.py — Phase 6: Plyer toast notifications

Wraps the plyer notification system into a clean, reusable static class to
trigger native OS toasts without cluttering the action dispatcher.
"""

class Notifier:
    """Static wrapper for sending system toast notifications."""

    @staticmethod
    def send(title: str, message: str) -> str:
        """
        Sends a native OS toast notification gracefully.
        
        Args:
            title: The title of the toast.
            message: The body text of the toast.
            
        Returns:
            A string describing the result exactly for the execution log.
        """
        try:
            from plyer import notification
            notification.notify(
                title=title,
                message=message,
                timeout=5
            )
            return f"Notification sent: {title} — {message}"
        except Exception as e:
            # Fallback purely to console if plyer fails (e.g. headless modes)
            print(f"[Notifier] {title}: {message} (Error: {e})")
            return f"Notification (console): {title} — {message}"
