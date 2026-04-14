"""
ui/hud.py — Phase 7: Interactive PyQt5 breathing sphere HUD

Replaces the generic pill UI with an animated, glowing orb that responds to 
real-time system status smoothly natively imitating flagship AI products.
"""

import sys
import math
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QRectF
from PyQt5.QtGui import QPainter, QColor, QRadialGradient, QFont

class AssistantThread(QThread):
    """Runs the main assistant loop in the background without freezing the GUI."""
    status_signal = pyqtSignal(str)
    
    def run(self):
        # Import main at runtime to avoid circular dependencies
        import main
        try:
            main.main(
                status_callback=self.status_signal.emit
            )
        except Exception as e:
            self.status_signal.emit(f"Error | {e}")

class PulseOrb(QWidget):
    """A floating glowing sphere that breathes and changes color based on state."""
    def __init__(self):
        super().__init__()
        
        # Transparent UI parameters
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.size = 200
        self.setFixedSize(self.size, self.size)
        
        # Color mapping based on HUD text
        self.state_colors = {
            "Passive": QColor(0, 150, 255),       # Deep calm blue
            "Listening": QColor(0, 255, 120),     # Bright cyan / neon green
            "Transcribing": QColor(0, 255, 120),
            "Processing": QColor(200, 50, 255),   # Magenta trigger
            "Thinking": QColor(180, 50, 255),     # Deep Purple
            "Executing": QColor(255, 150, 0),     # Orange burst
            "Speaking": QColor(255, 200, 0),      # Yellow talk
        }
        
        self.current_color = QColor(0, 150, 255)
        self.pulse_phase = 0.0
        self.status_text = "Initializing..."
        
        # Timer for 60 fps smooth animation refresh sequence
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(16)

    def animate(self):
        """Ticks forward the breathing phase dynamically."""
        pulse_speed = 0.03
        # Accelerate pulse effect during interactive actions
        if "Listening" in self.status_text:
            pulse_speed = 0.12 # Attentive heartbeat
        elif "Thinking" in self.status_text or "Processing" in self.status_text:
            pulse_speed = 0.18 # Very fast compute indicator
        
        self.pulse_phase += pulse_speed
        self.update()

    def update_status(self, text: str):
        """Intercepts state hooks explicitly from main.main() mapping UI paints."""
        self.status_text = text
        # Parse for matching keywords
        for key, color in self.state_colors.items():
            if key in text:
                self.current_color = color
                break
        self.update()

    def paintEvent(self, event):
        """Draws the dynamic breathing orb using transparent fluid ring geometry."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center_x = self.size / 2
        center_y = self.size / 2
        
        # Number of overlapping transparent aura rings to draw
        num_rings = 4 
        
        for i in range(num_rings):
            # Phase shifts so they offset visually and 'breathe' outward independently
            phase_offset = i * 1.5 
            radius_mod = math.sin(self.pulse_phase + phase_offset) * (self.size * 0.05)
            
            # Decrease base radius mathematically towards the core
            base_radius = self.size * 0.15 + (i * 18) 
            radius = base_radius + radius_mod
            
            ring_color = QColor(self.current_color)
            # The innermost core is most opaque. The outer rings fade away elegantly.
            opacity = max(10, 200 - (i * 50))  
            ring_color.setAlpha(opacity)
            
            painter.setBrush(ring_color)
            painter.setPen(Qt.NoPen)
            
            painter.drawEllipse(QRectF(
                center_x - radius, center_y - radius, 
                radius * 2, radius * 2
            ))
        
        # Overlay textual identifier cleanly at the bottom so the beautiful core is purely visible
        painter.setPen(QColor(255, 255, 255, 230))
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        # Nudge text to the bottom edge structurally
        t_rect = QRectF(0, self.size - 40, self.size, 40)
        painter.drawText(t_rect, Qt.AlignCenter, self.status_text)
        painter.end()

    def mousePressEvent(self, event):
        """Allows seamlessly closing the assistant by right-clicking the orb."""
        if event.button() == Qt.RightButton:
            print("[HUD] Right-clicked orb. Shutting down system natively.")
            QApplication.quit()
            import os
            os._exit(0)

def launch_hud():
    """Initializes the QApplication and starts the assistant thread."""
    app = QApplication(sys.argv)
    
    orb = PulseOrb()
    
    # Position gracefully off to the bottom right of the primary screen
    screen = app.primaryScreen().geometry()
    orb.move(screen.width() - orb.width() - 80, screen.height() - orb.height() - 100)
    
    orb.show()
    
    # Spin up isolated assistant
    assistant = AssistantThread()
    assistant.status_signal.connect(orb.update_status)
    assistant.start()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    launch_hud()
