# RAG Desktop UI - Ollama Style

A desktop chat interface built with PyQt6 that mimics Ollama's clean UI design.

## Features

✅ **Ollama-style Interface** - Dark theme with sidebar and chat area  
✅ **Auto-saving Chats** - All conversations saved to local JSON files  
✅ **Chat History** - Browse and reload previous conversations  
✅ **New Chat Button** - Start fresh conversations instantly  
✅ **Responsive Layout** - Resizable sidebar and chat panels  

## Quick Start

### Option 1: Automated Setup (Windows)
```bash
# Run setup script
setup.bat

# Start the application
run.bat
```

### Option 2: Manual Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Project Structure

```
rag_desktop_ui/
│
├── main.py               # Entry point
├── requirements.txt      # Dependencies
├── setup.bat            # Windows setup script
├── run.bat              # Windows run script
│
├── ui/                  # UI components
│   ├── __init__.py
│   ├── main_window.py   # Main Ollama-style layout
│   ├── chat_widget.py   # Central chat interface
│   └── sidebar.py       # Chat history + new chat button
│
└── data/                # Local data storage
    └── chats/           # JSON chat files
        ├── chat_2025-11-03_17-05-00.json
        └── ...
```

## How It Works

1. **New Chat**: Click "+ New Chat" to start a fresh conversation
2. **Send Messages**: Type in the input box and click "Send" or press Enter
3. **Auto-Save**: Every message is automatically saved to a timestamped JSON file
4. **Load History**: Click any chat in the sidebar to reload that conversation
5. **Persistent Storage**: All chats are stored locally in `data/chats/`

## Next Steps

To integrate with your RAG backend:

1. Replace the placeholder AI response in `chat_widget.py`
2. Add your RAG engine import and query logic
3. Optionally add settings for model configuration
4. Add markdown rendering for better message formatting

## Customization

The UI uses CSS-like styling. Modify the `setStyleSheet()` calls in each component to change:
- Colors and themes
- Fonts and sizing  
- Button styles
- Layout spacing