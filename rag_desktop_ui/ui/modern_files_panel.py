"""
Modern Files Panel - A clean, professional file list UI component
Designed to look like ChatGPT or Notion's sidebar file lists
"""
import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QLineEdit, QFrame, QGraphicsDropShadowEffect,
    QSizePolicy, QSpacerItem
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QFontMetrics, QColor, QCursor, QPalette


class FileCard(QFrame):
    """Individual file card with modern styling and hover effects"""
    
    file_clicked = pyqtSignal(str)  # Emit file path when clicked
    file_deleted = pyqtSignal(str)  # Emit file path when deleted
    
    def __init__(self, file_info):
        super().__init__()
        self.file_info = file_info
        self.file_path = file_info.get('path', '')
        self.file_name = file_info.get('name', 'Unknown')
        self.file_type = file_info.get('type', 'unknown')
        self.full_filename = self.file_name
        
        self.setup_ui()
        self.setup_animations()
    
    def setup_ui(self):
        """Setup the modern card UI"""
        self.setObjectName("fileCard")
        self.setFixedHeight(72)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
        # Card styling with modern dark theme
        self.setStyleSheet("""
            QFrame#fileCard {
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
                margin: 2px;
                padding: 0px;
            }
            QFrame#fileCard:hover {
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(124, 58, 237, 0.3);
            }
            QLabel {
                background: transparent;
                border: none;
            }
        """)
        
        # Add subtle shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 25))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)
        
        # File type icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(20, 20)
        icon_color = self.get_file_type_color()
        self.icon_label.setStyleSheet(f"""
            QLabel {{
                background-color: {icon_color};
                border-radius: 10px;
                border: 2px solid rgba(255, 255, 255, 0.1);
            }}
        """)
        layout.addWidget(self.icon_label)
        
        # File info section
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        # File name (with eliding)
        self.name_label = QLabel()
        self.name_label.setFont(QFont("Inter", 13, QFont.Weight.DemiBold))
        self.name_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                background: transparent;
            }
        """)
        self.update_filename_display()
        info_layout.addWidget(self.name_label)
        
        # File metadata
        file_size = self.get_file_size()
        file_date = self.get_file_date()
        self.meta_label = QLabel(f"{file_size} • {file_date}")
        self.meta_label.setObjectName("meta")
        self.meta_label.setFont(QFont("Inter", 10))
        self.meta_label.setStyleSheet("""
            QLabel#meta {
                color: rgba(255, 255, 255, 0.5);
                background: transparent;
            }
        """)
        info_layout.addWidget(self.meta_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Delete button (appears on hover)
        self.delete_btn = QPushButton("×")
        self.delete_btn.setFixedSize(24, 24)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 12px;
                color: rgba(255, 255, 255, 0.6);
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.8);
                color: white;
            }
        """)
        self.delete_btn.clicked.connect(lambda: self.file_deleted.emit(self.file_path))
        self.delete_btn.hide()  # Hidden by default
        layout.addWidget(self.delete_btn)
    
    def get_file_type_color(self):
        """Get color based on file type"""
        file_type = self.file_type.lower()
        if 'pdf' in file_type:
            return "#ef4444"  # Red
        elif 'image' in file_type:
            return "#8b5cf6"  # Purple
        elif 'text' in file_type or 'txt' in file_type:
            return "#22c55e"  # Green
        elif 'audio' in file_type or 'mp3' in file_type:
            return "#f59e0b"  # Orange
        elif 'csv' in file_type or 'excel' in file_type:
            return "#3b82f6"  # Blue
        elif 'doc' in file_type:
            return "#06b6d4"  # Cyan
        else:
            return "#6b7280"  # Gray
    
    def get_file_size(self):
        """Get formatted file size"""
        try:
            if os.path.exists(self.file_path):
                size_bytes = os.path.getsize(self.file_path)
                if size_bytes < 1024:
                    return f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    return f"{size_bytes / 1024:.1f} KB"
                else:
                    return f"{size_bytes / (1024 * 1024):.1f} MB"
        except:
            pass
        return "Unknown"
    
    def get_file_date(self):
        """Get formatted file date"""
        try:
            if os.path.exists(self.file_path):
                mtime = os.path.getmtime(self.file_path)
                date = datetime.fromtimestamp(mtime)
                return date.strftime("%b %d")
        except:
            pass
        return "Unknown"
    
    def update_filename_display(self):
        """Update filename with proper eliding"""
        if hasattr(self, 'name_label'):
            # Calculate available width (total width - margins - icon - spacing)
            available_width = max(200, self.width() - 80)
            
            # Apply text eliding
            metrics = QFontMetrics(self.name_label.font())
            elided_text = metrics.elidedText(self.full_filename, Qt.ElideRight, available_width)
            
            self.name_label.setText(elided_text)
            self.name_label.setToolTip(self.full_filename)
    
    def setup_animations(self):
        """Setup hover animations"""
        self.hover_animation = None
    
    def enterEvent(self, event):
        """Show delete button on hover"""
        self.delete_btn.show()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Hide delete button when not hovering"""
        self.delete_btn.hide()
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle card click"""
        if event.button() == Qt.LeftButton:
            self.file_clicked.emit(self.file_path)
        super().mousePressEvent(event)
    
    def resizeEvent(self, event):
        """Update filename display when resized"""
        super().resizeEvent(event)
        self.update_filename_display()


class ModernFilesPanel(QWidget):
    """Modern, professional files panel with ChatGPT-like styling"""
    
    upload_requested = pyqtSignal()
    file_opened = pyqtSignal(str)
    file_deleted = pyqtSignal(str)
    
    def __init__(self, files_data=None):
        super().__init__()
        self.files_data = files_data or []
        self.file_cards = []
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        
        self.setup_ui()
        self.load_files()
    
    def setup_ui(self):
        """Setup the modern panel UI"""
        self.setMinimumWidth(280)
        self.setMaximumWidth(400)
        
        # Main panel styling
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.02);
                color: white;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header section
        header_frame = self.create_header()
        layout.addWidget(header_frame)
        
        # Files scroll area
        self.scroll_area = self.create_scroll_area()
        layout.addWidget(self.scroll_area)
        
        # Bottom actions
        actions_frame = self.create_actions()
        layout.addWidget(actions_frame)
    
    def create_header(self):
        """Create the header with title and search"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.05);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 18, 20, 18)
        header_layout.setSpacing(14)
        
        # Title
        title_label = QLabel("My Files")
        title_label.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                background: transparent;
            }
        """)
        header_layout.addWidget(title_label)
        
        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search files...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 13px;
                color: white;
            }
            QLineEdit:focus {
                border-color: rgba(124, 58, 237, 0.6);
                background-color: rgba(255, 255, 255, 0.12);
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.4);
            }
        """)
        self.search_input.textChanged.connect(self.on_search_changed)
        header_layout.addWidget(self.search_input)
        
        return header_frame
    
    def create_scroll_area(self):
        """Create the scrollable files area"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Modern scrollbar styling
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.03);
                width: 8px;
                border-radius: 4px;
                margin: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(124, 58, 237, 0.4);
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(124, 58, 237, 0.6);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)
        
        # Files container
        self.files_container = QWidget()
        self.files_layout = QVBoxLayout(self.files_container)
        self.files_layout.setContentsMargins(16, 12, 16, 12)
        self.files_layout.setSpacing(8)
        self.files_layout.setAlignment(Qt.AlignTop)
        
        scroll_area.setWidget(self.files_container)
        return scroll_area
    
    def create_actions(self):
        """Create the bottom actions section"""
        actions_frame = QFrame()
        actions_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.03);
                border-top: 1px solid rgba(255, 255, 255, 0.08);
            }
        """)
        
        actions_layout = QHBoxLayout(actions_frame)
        actions_layout.setContentsMargins(20, 16, 20, 16)
        actions_layout.setSpacing(12)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                color: white;
                font-weight: 600;
                padding: 10px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.12);
                border-color: rgba(255, 255, 255, 0.25);
            }
        """)
        refresh_btn.clicked.connect(self.refresh_files)
        actions_layout.addWidget(refresh_btn)
        
        # Upload button
        upload_btn = QPushButton("+ Upload")
        upload_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c3aed, stop:1 #06b6d4);
                border: none;
                border-radius: 8px;
                color: white;
                font-weight: 600;
                padding: 10px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8b5cf6, stop:1 #0891b2);
            }
        """)
        upload_btn.clicked.connect(self.upload_requested.emit)
        actions_layout.addWidget(upload_btn)
        
        return actions_frame
    
    def load_files(self):
        """Load files into the panel"""
        self.clear_files()
        
        if not self.files_data:
            self.show_empty_state()
            return
        
        for file_info in self.files_data:
            self.add_file_card(file_info)
    
    def add_file_card(self, file_info):
        """Add a file card to the panel"""
        card = FileCard(file_info)
        card.file_clicked.connect(self.file_opened.emit)
        card.file_deleted.connect(self.handle_file_delete)
        
        self.file_cards.append(card)
        self.files_layout.addWidget(card)
    
    def clear_files(self):
        """Clear all file cards"""
        for card in self.file_cards:
            card.deleteLater()
        self.file_cards.clear()
    
    def show_empty_state(self):
        """Show empty state when no files"""
        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_layout.setContentsMargins(20, 40, 20, 40)
        
        empty_label = QLabel("No files uploaded yet")
        empty_label.setAlignment(Qt.AlignCenter)
        empty_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.4);
                font-size: 14px;
                background: transparent;
            }
        """)
        
        empty_layout.addWidget(empty_label)
        self.files_layout.addWidget(empty_widget)
    
    def on_search_changed(self, text):
        """Handle search input changes with debouncing"""
        self.search_timer.stop()
        self.search_timer.start(300)  # 300ms delay
    
    def perform_search(self):
        """Perform the actual search filtering"""
        search_text = self.search_input.text().lower()
        
        for card in self.file_cards:
            visible = search_text in card.file_name.lower()
            card.setVisible(visible)
    
    def handle_file_delete(self, file_path):
        """Handle file deletion request"""
        self.file_deleted.emit(file_path)
    
    def refresh_files(self):
        """Refresh the files list"""
        self.load_files()
    
    def update_files_data(self, files_data):
        """Update the files data and refresh display"""
        self.files_data = files_data
        self.load_files()


# Test/Demo code
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QWidget
    
    # Sample file data
    sample_files = [
        {
            "name": "Project_Requirements_Document_Final_Version_2024.pdf",
            "path": "/path/to/file1.pdf",
            "type": "application/pdf"
        },
        {
            "name": "meeting_notes.txt",
            "path": "/path/to/file2.txt", 
            "type": "text/plain"
        },
        {
            "name": "data_analysis_results.csv",
            "path": "/path/to/file3.csv",
            "type": "text/csv"
        },
        {
            "name": "presentation_slides.pptx",
            "path": "/path/to/file4.pptx",
            "type": "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        }
    ]
    
    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Modern Files Panel Demo")
            self.setGeometry(100, 100, 800, 600)
            
            # Dark theme
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1a1a1a;
                }
            """)
            
            # Central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            layout = QHBoxLayout(central_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            
            # Add the files panel
            files_panel = ModernFilesPanel(sample_files)
            files_panel.file_opened.connect(lambda path: print(f"Open file: {path}"))
            files_panel.file_deleted.connect(lambda path: print(f"Delete file: {path}"))
            files_panel.upload_requested.connect(lambda: print("Upload requested"))
            
            layout.addWidget(files_panel)
            
            # Add some placeholder content
            placeholder = QLabel("Main Content Area")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("""
                QLabel {
                    background-color: #2a2a2a;
                    color: white;
                    font-size: 18px;
                    border-radius: 8px;
                    margin: 10px;
                }
            """)
            layout.addWidget(placeholder, 1)
    
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())