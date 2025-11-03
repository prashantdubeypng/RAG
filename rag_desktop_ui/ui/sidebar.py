# ui/sidebar.py
import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
import qtawesome as qta


class Sidebar(QWidget):
    upload_clicked = pyqtSignal()
    newchat_clicked = pyqtSignal()
    theme_toggled = pyqtSignal(bool)  # emits True for dark, False for light
    chat_selected = pyqtSignal(str)

    def __init__(self, chat_dir="./data/chats", parent=None):
        super().__init__(parent)
        self.chat_dir = chat_dir
        self.setObjectName("sidebar")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Top logo + title
        logo_label = QLabel("YOURDATA")
        logo_label.setStyleSheet("font-weight:700; font-size:18px;")
        subtitle = QLabel("Intelligent AI Assistant")
        subtitle.setStyleSheet("color: rgba(255,255,255,0.6); font-size:11px;")

        layout.addWidget(logo_label)
        layout.addWidget(subtitle)

        # Upload button (above New Chat)
        upload_btn = QPushButton("Upload Data")
        upload_btn.setObjectName("primary")
        upload_btn.setIcon(qta.icon('fa.upload', color='white'))
        upload_btn.clicked.connect(lambda: self.upload_clicked.emit())
        upload_btn.setFixedHeight(44)
        layout.addWidget(upload_btn)

        # New Chat button
        newchat_btn = QPushButton("+ New Chat")
        newchat_btn.setObjectName("ghost")
        newchat_btn.setIcon(qta.icon('fa.plus', color='#E6EEF8'))
        newchat_btn.clicked.connect(lambda: self.newchat_clicked.emit())
        newchat_btn.setFixedHeight(42)
        layout.addWidget(newchat_btn)

        # Recent chats list
        lbl = QLabel("Recent Chats")
        lbl.setStyleSheet("margin-top: 8px; font-size: 12px; color: rgba(255,255,255,0.7);")
        layout.addWidget(lbl)
        
        self.chat_list = QListWidget()
        self.chat_list.setFixedHeight(220)
        self.chat_list.itemClicked.connect(self.on_chat_selected)
        layout.addWidget(self.chat_list)

        # spacer
        layout.addStretch()

        # Theme toggle area
        theme_layout = QHBoxLayout()
        self.theme_btn = QPushButton("🌙 Dark Mode")
        self.theme_btn.setObjectName("ghost")
        self.theme_btn.setCheckable(True)
        self.theme_btn.setChecked(True)  # Default to dark
        self.theme_btn.toggled.connect(self.on_theme_toggled)
        theme_layout.addWidget(self.theme_btn)
        layout.addLayout(theme_layout)

        self.setLayout(layout)
        self.refresh_chats()

    def on_theme_toggled(self, checked):
        # Update button text
        if checked:
            self.theme_btn.setText("🌙 Dark Mode")
        else:
            self.theme_btn.setText("☀️ Light Mode")
        # emit True for dark, False for light
        self.theme_toggled.emit(checked)

    def refresh_chats(self):
        """Reload chat files into sidebar list."""
        self.chat_list.clear()
        os.makedirs(self.chat_dir, exist_ok=True)
        files = sorted(os.listdir(self.chat_dir))
        for f in files:
            if f.endswith(".json"):
                # Clean up filename for display
                display_name = f.replace("chat_", "").replace(".json", "").replace("_", " ")
                self.chat_list.addItem(display_name)

    def on_chat_selected(self, item):
        # Convert display name back to filename
        display_text = item.text()
        # Find the actual file that matches
        files = os.listdir(self.chat_dir)
        for f in files:
            if f.endswith(".json") and display_text.replace(" ", "_") in f:
                file_path = os.path.join(self.chat_dir, f)
                self.chat_selected.emit(file_path)
                break