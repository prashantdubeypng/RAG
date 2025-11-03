# ui/chat_widget.py
import os
import json
import datetime
import mimetypes
import subprocess
import platform
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QFrame, QLineEdit,
    QPushButton, QHBoxLayout, QFileDialog, QLabel, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt
import qtawesome as qta


class ChatWidget(QWidget):
    def __init__(self, chat_dir="./data/chats"):
        super().__init__()
        self.chat_dir = chat_dir
        self.chat_history = []
        self.current_chat_file = None

        # ---- Main Layout ----
        self.setStyleSheet("""
            QWidget {
                background-color: #1E1E1E;
                color: #FFFFFF;
                font-family: 'Segoe UI';
            }
            QLineEdit {
                background-color: #2C2C2C;
                border: 1px solid #3A3A3A;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                color: white;
            }
            QPushButton {
                background-color: #0078D7;
                border-radius: 8px;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QLabel {
                color: white;
            }
            QLabel:hover {
                color: #50a8ff;
            }
            a {
                color: #4FC3F7;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Scrollable chat area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background-color: #1E1E1E; border: none;")
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.chat_container)

        # Input + buttons
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Ask something or upload a file...")
        self.input_box.returnPressed.connect(self.send_message)  # Enter key support

        self.upload_button = QPushButton()
        self.upload_button.setIcon(qta.icon('fa5s.upload'))
        self.upload_button.setToolTip("Upload a file")
        self.upload_button.clicked.connect(self.upload_file)

        self.send_button = QPushButton()
        self.send_button.setIcon(qta.icon('fa5s.paper-plane'))
        self.send_button.setToolTip("Send message")
        self.send_button.clicked.connect(self.send_message)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.upload_button)
        input_layout.addWidget(self.input_box)
        input_layout.addWidget(self.send_button)

        layout.addWidget(self.scroll)
        layout.addLayout(input_layout)
        self.setLayout(layout)

    # ---- Chat Management ----
    def start_new_chat(self):
        self.clear_chat()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.current_chat_file = os.path.join(self.chat_dir, f"chat_{timestamp}.json")
        self.chat_history = []

    def load_chat(self, file_path):
        if not os.path.exists(file_path):
            return
        self.clear_chat()
        self.current_chat_file = file_path
        with open(file_path, "r", encoding="utf-8") as f:
            self.chat_history = json.load(f)
        for msg in self.chat_history:
            self.add_message(msg["role"], msg["content"], save=False)

    def clear_chat(self):
        for i in reversed(range(self.chat_layout.count())):
            widget = self.chat_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

    def add_message(self, role, content, save=True):
        """Add bubble-style message"""
        bubble = QFrame()
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(12, 8, 12, 8)
        bubble_layout.setSpacing(4)

        msg_label = QLabel()
        msg_label.setTextFormat(Qt.TextFormat.RichText)
        msg_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        msg_label.setOpenExternalLinks(False)  # We'll handle clicks manually
        msg_label.setText(content)
        msg_label.linkActivated.connect(self.open_file)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                line-height: 1.4em;
            }
        """)

        timestamp = datetime.datetime.now().strftime("%H:%M")
        time_label = QLabel(timestamp)
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        time_label.setStyleSheet("font-size: 11px; color: #888;")

        bubble_layout.addWidget(msg_label)
        bubble_layout.addWidget(time_label)

        if role.lower() == "you":
            bubble.setStyleSheet("""
                QFrame {
                    background-color: #0E639C;
                    border-radius: 10px;
                    margin-left: 120px;
                }
            """)
        else:
            bubble.setStyleSheet("""
                QFrame {
                    background-color: #2C2C2C;
                    border-radius: 10px;
                    margin-right: 120px;
                }
            """)

        self.chat_layout.addWidget(bubble)
        self.chat_layout.addItem(QSpacerItem(10, 8, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())

        if save:
            self.chat_history.append({"role": role, "content": content})
            self.save_chat()

    def send_message(self):
        text = self.input_box.text().strip()
        if not text:
            return
        self.add_message("You", text)
        self.input_box.clear()

        # Placeholder AI response (replace later)
        response = f"AI response for: {text}"
        self.add_message("AI", response)

    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select a file", "", "All Files (*)")
        if file_path:
            file_name = os.path.basename(file_path)
            file_type, _ = mimetypes.guess_type(file_path)
            icon_emoji = "📄"

            if file_type:
                if "pdf" in file_type:
                    icon_emoji = "📕"
                elif "image" in file_type:
                    icon_emoji = "🖼️"
                elif "text" in file_type:
                    icon_emoji = "📘"
                elif "csv" in file_type or "excel" in file_type:
                    icon_emoji = "📊"

            msg = f"{icon_emoji} <b>{file_name}</b> — <a href='{file_path}'>Open File</a>"
            self.add_message("You", msg)

    def open_file(self, path):
        """Open the uploaded file in system file explorer."""
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])

    def save_chat(self):
        if not self.current_chat_file:
            self.start_new_chat()
        os.makedirs(self.chat_dir, exist_ok=True)
        with open(self.current_chat_file, "w", encoding="utf-8") as f:
            json.dump(self.chat_history, f, indent=2)