# ui/main_window.py
import os
import json
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame, 
    QSizePolicy, QGraphicsDropShadowEffect, QShortcut, QScrollArea, 
    QLineEdit, QMessageBox
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor, QFont, QKeySequence
from .sidebar import Sidebar
from .upload_dialog import UploadDialog, META_FILE
from .chat_widget import ChatWidget
from .file_card import FileCard
from .modern_files_panel import ModernFilesPanel
from .styles import DARK, LIGHT


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOURDATA")
        self.resize(1200, 760)
        self.sidebar_visible = True
        self.init_ui()
        # default theme:
        self.apply_theme(dark=True)

    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top bar with hamburger menu
        self.create_top_bar()
        main_layout.addWidget(self.top_bar)

        # Content area (sidebar + chat)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.setFixedWidth(320)
        self.sidebar.upload_clicked.connect(self.open_upload_dialog)
        self.sidebar.newchat_clicked.connect(self.start_new_chat)
        self.sidebar.theme_toggled.connect(self.on_theme_toggle)
        self.sidebar.chat_selected.connect(self.handle_chat_selected)
        
        # Add shadow to sidebar
        sidebar_shadow = QGraphicsDropShadowEffect()
        sidebar_shadow.setBlurRadius(20)
        sidebar_shadow.setOffset(2, 0)
        sidebar_shadow.setColor(QColor(0, 0, 0, 60))
        self.sidebar.setGraphicsEffect(sidebar_shadow)
        
        content_layout.addWidget(self.sidebar)

        # Chat area
        self.chat = ChatWidget()
        self.chat.setObjectName("chat_area")
        self.chat.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_layout.addWidget(self.chat)
        
        # Modern Files panel (right side)
        self.create_modern_files_panel()
        content_layout.addWidget(self.modern_files_panel)
        
        # Set stretch factors
        content_layout.setStretch(0, 0)  # sidebar fixed width
        content_layout.setStretch(1, 1)  # chat area expands
        content_layout.setStretch(2, 0)  # files panel fixed width

        # Add content to main layout
        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        main_layout.addWidget(content_widget)
        
        # Add keyboard shortcut for sidebar toggle (Ctrl+B)
        self.sidebar_shortcut = QShortcut(QKeySequence("Ctrl+B"), self)
        self.sidebar_shortcut.activated.connect(self.toggle_sidebar)
        
        # Add keyboard shortcut for files panel toggle (Ctrl+F)
        self.files_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.files_shortcut.activated.connect(self.toggle_files_panel)
        
        # Initialize panel states
        self.files_panel_visible = False

    def create_top_bar(self):
        """Create the top bar with hamburger menu and title"""
        self.top_bar = QFrame()
        self.top_bar.setFixedHeight(60)
        self.top_bar.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.05);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(16, 8, 16, 8)
        
        # Hamburger menu button
        self.menu_button = QPushButton("☰")
        self.menu_button.setFixedSize(40, 40)
        self.menu_button.setToolTip("Toggle Sidebar (Ctrl+B)")
        self.menu_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(124, 58, 237, 0.3);
                transform: scale(1.05);
            }
            QPushButton:pressed {
                background-color: rgba(124, 58, 237, 0.5);
            }
        """)
        self.menu_button.clicked.connect(self.toggle_sidebar)
        top_layout.addWidget(self.menu_button)
        
        # Title
        title_label = QLabel("YOURDATA")
        title_label.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                margin-left: 16px;
            }
        """)
        top_layout.addWidget(title_label)
        
        # Spacer
        top_layout.addStretch()
        
        # My Files button
        self.files_button = QPushButton("📁 My Files")
        self.files_button.setFixedHeight(35)
        self.files_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 14px;
                font-weight: 600;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: rgba(124, 58, 237, 0.3);
            }
            QPushButton:pressed {
                background-color: rgba(124, 58, 237, 0.5);
            }
        """)
        self.files_button.clicked.connect(self.toggle_files_panel)
        top_layout.addWidget(self.files_button)
        
        # Optional: Add status indicator
        status_label = QLabel("● Online")
        status_label.setStyleSheet("""
            QLabel {
                color: #22c55e;
                font-size: 12px;
                margin-right: 8px;
            }
        """)
        top_layout.addWidget(status_label)

    def toggle_sidebar(self):
        """Toggle sidebar visibility with smooth animation"""
        if self.sidebar_visible:
            # Hide sidebar
            self.animate_sidebar(320, 0)
            self.sidebar_visible = False
            self.menu_button.setToolTip("Show Sidebar (Ctrl+B)")
            # Add visual feedback
            self.menu_button.setStyleSheet(self.menu_button.styleSheet() + """
                QPushButton { background-color: rgba(255, 255, 255, 0.05); }
            """)
        else:
            # Show sidebar
            self.animate_sidebar(0, 320)
            self.sidebar_visible = True
            self.menu_button.setToolTip("Hide Sidebar (Ctrl+B)")
            # Reset visual feedback
            self.menu_button.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.1);
                    border: none;
                    border-radius: 8px;
                    color: white;
                    font-size: 18px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: rgba(124, 58, 237, 0.3);
                }
                QPushButton:pressed {
                    background-color: rgba(124, 58, 237, 0.5);
                }
            """)

    def animate_sidebar(self, start_width, end_width):
        """Animate sidebar width change"""
        self.animation = QPropertyAnimation(self.sidebar, b"maximumWidth")
        self.animation.setDuration(250)
        self.animation.setStartValue(start_width)
        self.animation.setEndValue(end_width)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Also animate minimum width to ensure smooth collapse
        self.animation2 = QPropertyAnimation(self.sidebar, b"minimumWidth")
        self.animation2.setDuration(250)
        self.animation2.setStartValue(start_width)
        self.animation2.setEndValue(end_width)
        self.animation2.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.animation.start()
        self.animation2.start()

    def create_modern_files_panel(self):
        """Create the modern files panel using the new ModernFilesPanel component"""
        # Create a container frame for the modern files panel
        self.modern_files_panel = QFrame()
        self.modern_files_panel.setFixedWidth(0)  # Start hidden
        self.modern_files_panel.setObjectName("modernFilesPanel")
        
        # Add shadow to files panel
        files_shadow = QGraphicsDropShadowEffect()
        files_shadow.setBlurRadius(25)
        files_shadow.setOffset(-3, 0)
        files_shadow.setColor(QColor(0, 0, 0, 80))
        self.modern_files_panel.setGraphicsEffect(files_shadow)
        
        # Container layout
        container_layout = QVBoxLayout(self.modern_files_panel)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Load initial files data
        files_data = self.load_files_data()
        
        # Create the modern files panel widget
        self.files_panel_widget = ModernFilesPanel(files_data)
        
        # Connect signals
        self.files_panel_widget.upload_requested.connect(self.open_upload_dialog)
        self.files_panel_widget.file_opened.connect(self.handle_file_open)
        self.files_panel_widget.file_deleted.connect(self.handle_file_delete)
        
        container_layout.addWidget(self.files_panel_widget)
    
    def load_files_data(self):
        """Load files data from the upload metadata"""
        files_data = []
        try:
            if os.path.exists(META_FILE):
                with open(META_FILE, "r", encoding="utf-8") as f:
                    uploads = json.load(f)
                files_data = uploads
        except Exception as e:
            print(f"Error loading files data: {e}")
        return files_data

    def toggle_files_panel(self):
        """Toggle files panel visibility with smooth animation"""
        if self.files_panel_visible:
            # Hide files panel
            self.animate_files_panel(300, 0)
            self.files_panel_visible = False
            self.files_button.setText("📁 My Files")
            self.files_button.setToolTip("Show Files Panel (Ctrl+F)")
        else:
            # Show files panel
            self.animate_files_panel(0, 300)
            self.files_panel_visible = True
            self.files_button.setText("📁 Hide Files")
            self.files_button.setToolTip("Hide Files Panel (Ctrl+F)")
            # Refresh files when opening
            self.refresh_files_list()

    def animate_files_panel(self, start_width, end_width):
        """Animate files panel width change"""
        self.files_animation = QPropertyAnimation(self.modern_files_panel, b"maximumWidth")
        self.files_animation.setDuration(250)
        self.files_animation.setStartValue(start_width)
        self.files_animation.setEndValue(end_width)
        self.files_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Also animate minimum width
        self.files_animation2 = QPropertyAnimation(self.modern_files_panel, b"minimumWidth")
        self.files_animation2.setDuration(250)
        self.files_animation2.setStartValue(start_width)
        self.files_animation2.setEndValue(end_width)
        self.files_animation2.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.files_animation.start()
        self.files_animation2.start()

    def refresh_files_list(self):
        """Refresh the files list from uploaded files"""
        # Load fresh files data and update the modern files panel
        files_data = self.load_files_data()
        if hasattr(self, 'files_panel_widget'):
            self.files_panel_widget.update_files_data(files_data)



    def handle_file_delete(self, file_path):
        """Handle file deletion"""
        reply = QMessageBox.question(
            self, 
            "Delete File", 
            "Are you sure you want to delete this file?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Remove from uploads metadata
                if os.path.exists(META_FILE):
                    with open(META_FILE, "r", encoding="utf-8") as f:
                        uploads = json.load(f)
                    
                    # Filter out the deleted file
                    uploads = [u for u in uploads if u.get('path') != file_path]
                    
                    # Save updated metadata
                    with open(META_FILE, "w", encoding="utf-8") as f:
                        json.dump(uploads, f, indent=2)
                
                # Delete the actual file
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                # Refresh the files list
                self.refresh_files_list()
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to delete file: {str(e)}")

    def handle_file_open(self, file_path):
        """Handle file opening"""
        try:
            if os.path.exists(file_path):
                import subprocess
                import platform
                
                if platform.system() == "Windows":
                    os.startfile(file_path)
                elif platform.system() == "Darwin":
                    subprocess.call(["open", file_path])
                else:
                    subprocess.call(["xdg-open", file_path])
            else:
                QMessageBox.warning(self, "Error", "File not found")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open file: {str(e)}")

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
        
        # Refresh the modern files panel
        self.refresh_files_list()

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
        
        # Update top bar styling based on theme
        if hasattr(self, 'top_bar'):
            if dark:
                self.top_bar.setStyleSheet("""
                    QFrame {
                        background-color: rgba(255, 255, 255, 0.08);
                        border-bottom: 1px solid rgba(255, 255, 255, 0.15);
                    }
                """)
            else:
                self.top_bar.setStyleSheet("""
                    QFrame {
                        background-color: rgba(0, 0, 0, 0.05);
                        border-bottom: 1px solid rgba(0, 0, 0, 0.1);
                    }
                """)
        
        # Update modern files panel styling based on theme
        if hasattr(self, 'modern_files_panel'):
            if dark:
                self.modern_files_panel.setStyleSheet("""
                    QFrame {
                        background-color: rgba(255, 255, 255, 0.05);
                        border-left: 1px solid rgba(255, 255, 255, 0.1);
                    }
                """)
            else:
                self.modern_files_panel.setStyleSheet("""
                    QFrame {
                        background-color: rgba(0, 0, 0, 0.05);
                        border-left: 1px solid rgba(0, 0, 0, 0.1);
                    }
                """)

    def resizeEvent(self, event):
        """Handle window resize - auto-hide sidebar on small screens"""
        super().resizeEvent(event)
        
        # Auto-hide sidebar on small screens (< 800px width)
        if event.size().width() < 800 and self.sidebar_visible:
            self.toggle_sidebar()
        elif event.size().width() >= 800 and not self.sidebar_visible:
            # Optionally auto-show sidebar on larger screens
            pass