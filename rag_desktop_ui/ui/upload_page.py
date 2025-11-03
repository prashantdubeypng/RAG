# ui/upload_page.py
import os
import json
import datetime
import mimetypes
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget,
    QListWidgetItem, QFileDialog, QHBoxLayout, QMessageBox, QFrame,
    QScrollArea, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor


class FileCard(QFrame):
    remove_requested = pyqtSignal(dict)
    
    def __init__(self, file_meta):
        super().__init__()
        self.file_meta = file_meta
        self.setup_ui()
        
    def setup_ui(self):
        self.setFixedHeight(80)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 16px;
                margin: 4px;
            }
            QFrame:hover {
                background-color: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(0, 180, 219, 0.4);
            }
        """)
        
        # Add subtle shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        
        # File type indicator
        file_type = self.file_meta.get('type', 'unknown')
        type_color = "#00B4DB"  # Default teal
        if file_type:
            if "pdf" in file_type:
                type_color = "#E53E3E"  # Red for PDF
            elif "image" in file_type:
                type_color = "#9F7AEA"  # Purple for images
            elif "text" in file_type:
                type_color = "#38A169"  # Green for text
            elif "csv" in file_type or "excel" in file_type:
                type_color = "#D69E2E"  # Orange for spreadsheets
        
        type_indicator = QLabel()
        type_indicator.setFixedSize(12, 12)
        type_indicator.setStyleSheet(f"""
            QLabel {{
                background-color: {type_color};
                border-radius: 6px;
            }}
        """)
        
        # File info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        name_label = QLabel(self.file_meta['name'])
        name_label.setFont(QFont("Inter", 14, QFont.Weight.DemiBold))
        name_label.setStyleSheet("color: #FFFFFF;")
        
        type_label = QLabel(self.file_meta.get('type', 'Unknown type'))
        type_label.setFont(QFont("Inter", 11))
        type_label.setStyleSheet("color: rgba(255, 255, 255, 0.6);")
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(type_label)
        
        # Remove button
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(24, 24)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 12px;
                color: rgba(255, 255, 255, 0.6);
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(229, 62, 62, 0.8);
                color: white;
            }
        """)
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.file_meta))
        
        layout.addWidget(type_indicator)
        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addWidget(remove_btn)


class UploadPage(QWidget):
    ask_query = pyqtSignal(list)

    def __init__(self, uploads_dir="./data/uploads"):
        super().__init__()
        self.uploads_dir = uploads_dir
        os.makedirs(self.uploads_dir, exist_ok=True)
        self.uploads_meta_file = os.path.join(self.uploads_dir, "uploads.json")
        self.uploaded_files = []
        
        self.setup_ui()
        self._load_uploads_meta()

    def setup_ui(self):
        # Main gradient background
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0f1419, stop:0.3 #1a1f2e, stop:1 #0f1419);
                color: white;
                font-family: 'Inter', 'SF Pro Display', 'Segoe UI', sans-serif;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 40, 60, 40)
        layout.setSpacing(32)

        # Header section with glassmorphism
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 24px;
                padding: 32px;
            }
        """)
        
        # Add subtle shadow to header
        header_shadow = QGraphicsDropShadowEffect()
        header_shadow.setBlurRadius(30)
        header_shadow.setColor(QColor(0, 0, 0, 60))
        header_shadow.setOffset(0, 8)
        header_frame.setGraphicsEffect(header_shadow)
        
        header_layout = QVBoxLayout(header_frame)
        header_layout.setSpacing(16)
        
        # Title with modern typography
        title = QLabel("Upload Your Knowledge Base")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Inter", 32, QFont.Weight.Bold))
        title.setStyleSheet("""
            QLabel {
                color: #00B4DB;
                font-weight: bold;
            }
        """)

        subtitle = QLabel("Transform your documents into an intelligent knowledge base. Upload PDFs, text files, spreadsheets, and images to get started.")
        subtitle.setWordWrap(True)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Inter", 16))
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.7); line-height: 1.5;")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        # Upload section
        upload_frame = QFrame()
        upload_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.03);
                border: 2px dashed rgba(0, 180, 219, 0.3);
                border-radius: 20px;
                min-height: 120px;
            }
            QFrame:hover {
                border: 2px dashed rgba(0, 180, 219, 0.6);
                background-color: rgba(0, 180, 219, 0.05);
            }
        """)
        
        upload_layout = QVBoxLayout(upload_frame)
        upload_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_layout.setSpacing(16)
        
        self.upload_btn = QPushButton("Choose Files to Upload")
        self.upload_btn.setFont(QFont("Inter", 16, QFont.Weight.DemiBold))
        self.upload_btn.setFixedHeight(56)
        self.upload_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00B4DB, stop:1 #0083B0);
                border: none;
                border-radius: 28px;
                color: white;
                padding: 0 32px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00C4EB, stop:1 #0093C0);
            }
        """)
        self.upload_btn.clicked.connect(self.handle_upload)
        
        upload_hint = QLabel("or drag and drop files here")
        upload_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_hint.setFont(QFont("Inter", 14))
        upload_hint.setStyleSheet("color: rgba(255, 255, 255, 0.5);")
        
        upload_layout.addWidget(self.upload_btn)
        upload_layout.addWidget(upload_hint)

        # Files section
        files_header = QLabel("Uploaded Files")
        files_header.setFont(QFont("Inter", 20, QFont.Weight.Bold))
        files_header.setStyleSheet("color: #FFFFFF; margin-top: 16px;")

        # Scrollable files area
        self.files_scroll = QScrollArea()
        self.files_scroll.setWidgetResizable(True)
        self.files_scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: rgba(255, 255, 255, 0.1);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(0, 180, 219, 0.6);
                border-radius: 4px;
                min-height: 20px;
            }
        """)
        
        self.files_container = QWidget()
        self.files_layout = QVBoxLayout(self.files_container)
        self.files_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.files_layout.setSpacing(8)
        self.files_scroll.setWidget(self.files_container)
        self.files_scroll.setFixedHeight(300)

        # Empty state
        self.empty_state = QLabel("No files uploaded yet")
        self.empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_state.setFont(QFont("Inter", 16))
        self.empty_state.setStyleSheet("color: rgba(255, 255, 255, 0.4); margin: 60px;")

        # Bottom action section
        bottom_frame = QFrame()
        bottom_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                padding: 24px;
            }
        """)
        
        bottom_layout = QHBoxLayout(bottom_frame)
        
        privacy_note = QLabel("Your data stays private and secure on your device")
        privacy_note.setFont(QFont("Inter", 14))
        privacy_note.setStyleSheet("color: rgba(255, 255, 255, 0.6);")
        
        self.ask_btn = QPushButton("Start Chatting")
        self.ask_btn.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        self.ask_btn.setFixedHeight(52)
        self.ask_btn.setFixedWidth(180)
        self.ask_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #16a34a, stop:1 #15803d);
                border: none;
                border-radius: 26px;
                color: white;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #22c55e, stop:1 #16a34a);
            }
            QPushButton:disabled {
                background-color: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.4);
            }
        """)
        self.ask_btn.clicked.connect(self.handle_ask_query)
        
        bottom_layout.addWidget(privacy_note)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.ask_btn)

        # Add all sections to main layout
        layout.addWidget(header_frame)
        layout.addWidget(upload_frame)
        layout.addWidget(files_header)
        layout.addWidget(self.files_scroll)
        layout.addWidget(self.empty_state)
        layout.addWidget(bottom_frame)
        
        self.setLayout(layout)

    # ---------- uploads meta persistence (UI-only) ----------
    def _save_uploads_meta(self):
        with open(self.uploads_meta_file, "w", encoding="utf-8") as f:
            json.dump(self.uploaded_files, f, indent=2)

    def _load_uploads_meta(self):
        if os.path.exists(self.uploads_meta_file):
            try:
                with open(self.uploads_meta_file, "r", encoding="utf-8") as f:
                    self.uploaded_files = json.load(f)
            except Exception:
                self.uploaded_files = []
        self._refresh_files_list()

    # ---------- UI helpers ----------
    def _refresh_files_list(self):
        # Clear existing cards
        for i in reversed(range(self.files_layout.count())):
            child = self.files_layout.itemAt(i).widget()
            if child:
                child.deleteLater()
        
        # Show/hide empty state
        if not self.uploaded_files:
            self.empty_state.show()
            self.files_scroll.hide()
        else:
            self.empty_state.hide()
            self.files_scroll.show()
            
            # Add file cards with animation
            for f in self.uploaded_files:
                card = FileCard(f)
                card.remove_requested.connect(self._remove_file)
                
                # Add fade-in animation
                card.setStyleSheet(card.styleSheet() + "QFrame { opacity: 0; }")
                self.files_layout.addWidget(card)
                
                # Animate opacity
                self.animate_card_in(card)
    
    def animate_card_in(self, card):
        """Animate card appearance"""
        self.animation = QPropertyAnimation(card, b"windowOpacity")
        self.animation.setDuration(300)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        card.setStyleSheet(card.styleSheet().replace("opacity: 0;", "opacity: 1;"))
        self.animation.start()
    
    def _remove_file(self, file_meta):
        """Remove file from list"""
        self.uploaded_files = [f for f in self.uploaded_files if f["path"] != file_meta["path"]]
        # Optionally delete file from disk
        try:
            if os.path.exists(file_meta["path"]):
                os.remove(file_meta["path"])
        except:
            pass
        self._save_uploads_meta()
        self._refresh_files_list()

    def handle_upload(self):
        # allow multi-select
        paths, _ = QFileDialog.getOpenFileNames(self, "Select files", "", "All Files (*)")
        if not paths:
            return
        
        for p in paths:
            name = os.path.basename(p)
            mtype, _ = mimetypes.guess_type(p)
            # For UI-only, we copy file to local uploads dir so chat engine can access them later if needed
            dst = os.path.join(self.uploads_dir, f"{datetime.datetime.now().timestamp()}_{name}")
            try:
                with open(p, "rb") as srcf, open(dst, "wb") as dstf:
                    dstf.write(srcf.read())
            except Exception as e:
                QMessageBox.warning(self, "Upload error", f"Could not copy file {name}: {e}")
                continue
            meta = {"path": dst, "name": name, "type": mtype or "unknown"}
            self.uploaded_files.append(meta)

        self._save_uploads_meta()
        self._refresh_files_list()

    def handle_ask_query(self):
        if not self.uploaded_files:
            reply = QMessageBox.question(
                self, "No uploads", "No files uploaded. Do you want to proceed to chat anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        # Emit list of uploaded file paths to whoever is listening
        paths = [f["path"] for f in self.uploaded_files]
        self.ask_query.emit(paths)

