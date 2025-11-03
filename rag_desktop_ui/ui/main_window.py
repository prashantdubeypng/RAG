# ui/main_window.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QSplitter
from PyQt6.QtCore import Qt
from .sidebar import Sidebar
from .chat_widget import ChatWidget


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOURDATA")
        self.resize(1000, 700)
        self.setStyleSheet("background-color: #1E1E1E;")

        layout = QHBoxLayout(self)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Components
        self.sidebar = Sidebar()
        self.chat = ChatWidget()

        # Connect signals
        self.sidebar.new_chat_clicked.connect(self.handle_new_chat)
        self.sidebar.chat_selected.connect(self.handle_chat_selected)

        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.chat)
        self.splitter.setSizes([250, 750])

        layout.addWidget(self.splitter)
        self.setLayout(layout)

        # Start with a fresh chat
        self.chat.start_new_chat()

    def handle_new_chat(self):
        self.chat.start_new_chat()
        self.sidebar.refresh_chats()

    def handle_chat_selected(self, file_path):
        self.chat.load_chat(file_path)