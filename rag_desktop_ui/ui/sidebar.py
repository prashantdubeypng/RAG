# ui/sidebar.py
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QPushButton, QLabel
from PyQt6.QtCore import Qt, pyqtSignal


class Sidebar(QWidget):
    chat_selected = pyqtSignal(str)
    new_chat_clicked = pyqtSignal()

    def __init__(self, chat_dir="./data/chats"):
        super().__init__()
        self.chat_dir = chat_dir
        self.setStyleSheet("""
            QWidget {
                background-color: #202020;
                color: white;
                font-family: 'Segoe UI';
            }
            QListWidget {
                background-color: #2C2C2C;
                border: none;
                border-radius: 8px;
                padding: 5px;
            }
            QPushButton {
                background-color: #0E639C;
                border-radius: 6px;
                padding: 6px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background-color: #1177BB;
            }
            QLabel {
                color: #AAAAAA;
                padding: 4px;
                font-size: 14px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.title = QLabel("💬 Chat Sessions")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.new_chat_btn = QPushButton("+ New Chat")
        self.new_chat_btn.clicked.connect(self.new_chat_clicked.emit)

        self.chat_list = QListWidget()
        self.chat_list.itemClicked.connect(self.on_chat_selected)

        layout.addWidget(self.title)
        layout.addWidget(self.new_chat_btn)
        layout.addWidget(self.chat_list)
        layout.addStretch()
        self.setLayout(layout)

        self.refresh_chats()

    def refresh_chats(self):
        """Reload chat files into sidebar list."""
        self.chat_list.clear()
        os.makedirs(self.chat_dir, exist_ok=True)
        files = sorted(os.listdir(self.chat_dir))
        for f in files:
            if f.endswith(".json"):
                self.chat_list.addItem(f)

    def on_chat_selected(self, item):
        file_path = os.path.join(self.chat_dir, item.text())
        self.chat_selected.emit(file_path)