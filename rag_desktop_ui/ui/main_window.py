# ui/main_window.py
import os
import json
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy
from PyQt5.QtCore import Qt
from .sidebar import Sidebar
from .upload_dialog import UploadDialog, META_FILE
from .chat_widget import ChatWidget
from .styles import DARK, LIGHT


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOURDATA")
        self.resize(1200, 760)
        self.init_ui()
        # default theme:
        self.apply_theme(dark=True)

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.setFixedWidth(320)
        self.sidebar.upload_clicked.connect(self.open_upload_dialog)
        self.sidebar.newchat_clicked.connect(self.start_new_chat)
        self.sidebar.theme_toggled.connect(self.on_theme_toggle)
        self.sidebar.chat_selected.connect(self.handle_chat_selected)
        layout.addWidget(self.sidebar)

        # Chat area (full right side)
        self.chat = ChatWidget()
        self.chat.setObjectName("chat_area")
        self.chat.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.chat)
        
        # Set stretch factors: sidebar smaller, chat area larger
        layout.setStretch(0, 1)  # sidebar
        layout.setStretch(1, 4)  # chat area wider

    def open_upload_dialog(self):
        dlg = UploadDialog(self)
        res = dlg.exec_()
        # after close, reload meta and notify chat
        uploads = []
        if os.path.exists(META_FILE):
            try:
                with open(META_FILE, "r", encoding="utf-8") as f:
                    uploads = json.load(f)
            except Exception:
                uploads = []
        # pass paths to chat widget if you implemented set_uploaded_files
        try:
            self.chat.set_uploaded_files([u["path"] for u in uploads])
        except Exception:
            pass

    def start_new_chat(self):
        # call existing new chat routine on ChatWidget
        try:
            self.chat.start_new_chat()
            self.sidebar.refresh_chats()
        except Exception:
            pass

    def handle_chat_selected(self, file_path):
        try:
            self.chat.load_chat(file_path)
        except Exception:
            pass

    def on_theme_toggle(self, checked):
        self.apply_theme(dark=checked)

    def apply_theme(self, dark=True):
        if dark:
            self.setStyleSheet(DARK)
        else:
            self.setStyleSheet(LIGHT)