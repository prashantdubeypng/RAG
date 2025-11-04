# ui/file_card.py
import os
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, 
    QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QColor, QFontMetrics, QCursor


class FileCard(QWidget):
    """Modern file card widget with hover effects and actions"""
    
    file_deleted = pyqtSignal(str)  # Emit file path when deleted
    file_opened = pyqtSignal(str)   # Emit file path when opened
    
    def __init__(self, file_info):
        super().__init__()
        self.file_info = file_info
        self.file_path = file_info.get('path', '')
        self.file_name = file_info.get('name', 'Unknown')
        self.file_type = file_info.get('type', 'unknown')
        
        self.setup_ui()
        self.setup_animations()
    
    def setup_ui(self):
        """Setup the card UI with enhanced styling"""
        self.setFixedHeight(85)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                margin: 6px 4px;
                padding: 12px 16px;
            }
            QWidget:hover {
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(124, 58, 237, 0.4);
                transform: translateY(-1px);
            }
        """)
        
        # Add enhanced shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)
        
        # Main layout with better spacing
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)
        
        # File type indicator (larger and more prominent)
        self.type_indicator = QLabel()
        self.type_indicator.setFixedSize(16, 16)
        type_color = self.get_type_color()
        self.type_indicator.setStyleSheet(f"""
            QLabel {{
                background-color: {type_color};
                border-radius: 8px;
            }}
        """)
        layout.addWidget(self.type_indicator)
        
        # File info section with improved layout
        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)
        
        # File name with text eliding
        self.name_label = QLabel()
        self.name_label.setFont(QFont("Inter", 14, QFont.Weight.DemiBold))
        self.name_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
            }
            QLabel:hover {
                color: #a78bfa;
                text-decoration: underline;
            }
        """)
        
        # Apply text eliding for long filenames
        metrics = QFontMetrics(self.name_label.font())
        elided_text = metrics.elidedText(self.file_name, Qt.ElideRight, 240)
        self.name_label.setText(elided_text)
        self.name_label.setToolTip(self.file_name)  # Show full name on hover
        self.name_label.setCursor(QCursor(Qt.PointingHandCursor))
        self.name_label.mousePressEvent = lambda e: self.open_file()
        
        info_layout.addWidget(self.name_label)
        
        # File details with better formatting
        file_size = self.get_file_size()
        file_date = self.get_file_date()
        self.details_label = QLabel(f"{file_size} • {file_date}")
        self.details_label.setFont(QFont("Inter", 11))
        self.details_label.setStyleSheet("color: rgba(255, 255, 255, 0.55);")
        info_layout.addWidget(self.details_label)
        
        layout.addLayout(info_layout)
        
        # Spacer
        layout.addStretch()
        
        # Action buttons
        self.create_action_buttons(layout)
    
    def get_type_color(self):
        """Get color based on file type"""
        file_type = self.file_type.lower()
        if 'pdf' in file_type:
            return "#E53E3E"  # Red
        elif 'image' in file_type:
            return "#9F7AEA"  # Purple
        elif 'text' in file_type:
            return "#38A169"  # Green
        elif 'audio' in file_type:
            return "#D69E2E"  # Orange
        elif 'csv' in file_type or 'excel' in file_type:
            return "#3182CE"  # Blue
        else:
            return "#718096"  # Gray
    
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
                import datetime
                mtime = os.path.getmtime(self.file_path)
                date = datetime.datetime.fromtimestamp(mtime)
                return date.strftime("%b %d")
        except:
            pass
        return "Unknown"
    
    def create_action_buttons(self, layout):
        """Create enhanced action buttons"""
        # Actions container for better spacing
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)
        
        # Open button with improved styling
        self.open_btn = QPushButton("Open")
        self.open_btn.setFixedSize(65, 30)
        self.open_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.open_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(124, 58, 237, 0.15);
                border: 1px solid rgba(124, 58, 237, 0.3);
                border-radius: 8px;
                color: #a78bfa;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(124, 58, 237, 0.25);
                border-color: rgba(124, 58, 237, 0.5);
                color: white;
            }
            QPushButton:pressed {
                background-color: rgba(124, 58, 237, 0.35);
            }
        """)
        self.open_btn.clicked.connect(self.open_file)
        actions_layout.addWidget(self.open_btn)
        
        # Delete button with enhanced styling
        self.delete_btn = QPushButton("×")
        self.delete_btn.setFixedSize(30, 30)
        self.delete_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.delete_btn.setToolTip("Delete file")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                color: rgba(255, 255, 255, 0.6);
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.2);
                border-color: rgba(239, 68, 68, 0.4);
                color: #f87171;
            }
            QPushButton:pressed {
                background-color: rgba(239, 68, 68, 0.3);
            }
        """)
        self.delete_btn.clicked.connect(self.delete_file)
        actions_layout.addWidget(self.delete_btn)
        
        layout.addLayout(actions_layout)
    
    def setup_animations(self):
        """Setup hover animations"""
        self.setProperty("hovered", False)
        self.hover_animation = None
    
    def enterEvent(self, event):
        """Handle mouse enter with smooth animation"""
        self.animate_hover(True)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave with smooth animation"""
        self.animate_hover(False)
        super().leaveEvent(event)
    
    def animate_hover(self, hovered):
        """Animate hover effect with subtle scaling"""
        if self.hover_animation:
            self.hover_animation.stop()
        
        # Create a subtle scale animation
        self.hover_animation = QPropertyAnimation(self, b"geometry")
        self.hover_animation.setDuration(150)
        self.hover_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        current_rect = self.geometry()
        if hovered:
            # Slightly expand on hover
            new_rect = current_rect.adjusted(-1, -1, 1, 1)
        else:
            # Return to original size
            new_rect = current_rect.adjusted(1, 1, -1, -1)
        
        self.hover_animation.setStartValue(current_rect)
        self.hover_animation.setEndValue(new_rect)
        self.hover_animation.start()
    
    def open_file(self):
        """Open file with system default application"""
        self.file_opened.emit(self.file_path)
    
    def delete_file(self):
        """Delete file"""
        self.file_deleted.emit(self.file_path)