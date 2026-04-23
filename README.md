# 🤖 Friday AI Assistant

A **JARVIS-inspired, offline web & system integration AI Assistant** designed to control your PC, browse the web, and answer questions. Friday listens for wake words, supports clap detection, and features a sleek HUD overlay.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![PyQt5](https://img.shields.io/badge/PyQt5-GUI-green)
![Gemini](https://img.shields.io/badge/LLM-Generative_AI-orange)
[![Live Demo](https://img.shields.io/badge/🌐_Watch_Demo-Visit_Portfolio-6c63ff?style=for-the-badge)](#)

---

## 📺 Demo

[Friday AI Demo](https://drive.google.com/file/d/19orM2MOdW4ts1FcqLH55TzxLB2V6_sz8/view?usp=sharing)


---

## ✨ Features

- **Wake Word Activation** — Always listening for its name to wake up.
- **Clap Detection** — Gesture-based triggers to get Friday's attention instantly.
- **Quick Commands** — Lightning-fast, regex-based command execution (e.g., volume control, app launching) without waiting for the LLM.
- **LLM Brain Engine** — Conversational agent that parses complex instructions and generates executable actions.
- **System & App Control** — Launch apps natively, control system volume, and open URLs on the fly.
- **Routine Engine** — YAML-based automation for morning/night routines or workflow setups.
- **Graphical HUD** — A sleek, non-intrusive PyQt5 overlay that shows real-time status and transcription.
- **Contextual Memory** — Remembers the flow of conversation across interactions using SQLite.

---

## 🏗️ Architecture

```text
User Speech / Clap
      ↓
Wake Word / Gesture Detector
      ↓
Transcribe Audio (STT)
      ↓
┌───────────────────────────────────────┐
│ Is Quick Command?                     │
│ YES → Execute Action Instantly        │
│ NO  → Send text to LLM Brain          │
└───────────────────────────────────────┘
      ↓
LLM Brain Generates Response & parsed [ACTION:] tags
      ↓
Dispatcher Executes System/Web Actions
      ↓
Text-To-Speech (TTS) Responds
```

---

## 📁 Project Structure

```text
Friday/
├── core/                  # Core AI components
│   ├── brain.py           # LLM logic and action parsing
│   ├── dispatcher.py      # Action routing hub
│   ├── listener.py        # Audio capture
│   ├── memory.py          # SQLite contextual memory
│   ├── stt.py / tts.py    # Speech-to-Text & Text-to-Speech
│   └── wake_word.py       # Wake word detection
├── gestures/              
│   └── clap_detector.py   # Audio-based clap detection
├── modules/               # App, System, and Web controllers
│   ├── app_launcher.py    
│   ├── browser_control.py 
│   ├── system_control.py  
│   └── routine_engine.py  # Automation routines
├── ui/                    
│   └── hud.py             # PyQt5 Graphical Interface
├── main.py                # Main execution loop
├── config.yaml            # Configurations and app aliases
└── routines.yaml          # Defined automated workflows
```

---

## 🚀 Quick Start

### 1. Clone & enter the project

```bash
cd Friday
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Friday

Edit `config.yaml` to specify your name, API keys (if applicable for STT/LLM), and application paths.

### 5. Run the Assistant

```bash
# Launch with the GUI HUD (Default)
python main.py

# Launch in CLI-only mode
python main.py --cli
```

*You can also double-click `Launch Friday.bat` to start it instantly!*

---

## 💬 Example Commands

### Quick Commands (Instant)
- *"Open Spotify"*
- *"Close Notepad"*
- *"Set volume to 50"*
- *"Run morning routine"*
- *"Go to YouTube"*

### Conversational Queries (LLM Brain)
- *"Friday, what's a good recipe for dinner tonight?"*
- *"Summarize the latest AI news and open my browser."*
- *"Shut down the system. Goodbye, Friday."*

---

## ⚙️ Configuration

Edit `config.yaml` to customize:

| Category | Description |
|----------|-------------|
| **User Settings** | Set your `user_name` (e.g., Boss) for customized interactions. |
| **App Aliases** | Map spoken words to native Windows executable names. |
| **API Keys** | Configure your LLM and transcription API keys. |
| **Volumes / Thresholds**| Tune wake-word and clap detection sensitivity. |

---

## 📝 License

MIT

---
⭐ Star this repo if you found it useful!

Made with ❤️ by Anvesh Pavuluri
