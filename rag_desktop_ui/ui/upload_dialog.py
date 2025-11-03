# ui/upload_dialog.py
import os
import sys
import json
import shutil
import mimetypes
import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QListWidget, 
    QFileDialog, QMessageBox, QHBoxLayout, QFrame, QProgressBar,
    QTextEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

# Add the ingestion_pipeline directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
ingestion_path = os.path.join(current_dir, '..', '..', 'ingestion_pipeline')
ingestion_path = os.path.abspath(ingestion_path)

if ingestion_path not in sys.path:
    sys.path.insert(0, ingestion_path)

# Check if ingestion pipeline is available (lazy loading)
INGESTION_AVAILABLE = os.path.exists(os.path.join(ingestion_path, 'client.py'))

def get_ingestion_client():
    """Lazy load the ingestion client to avoid import issues at startup"""
    try:
        from client import IngestionClient
        return IngestionClient(
            text_model="BAAI/bge-base-en",
            image_model=None,  # Disable image processing for now
            offline_mode=False
        )
    except Exception as e:
        print(f"Error creating real ingestion client: {e}")
        print("Falling back to mock client for UI testing...")
        try:
            # Import mock client from the same directory
            import sys
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            sys.path.insert(0, parent_dir)
            from mock_ingestion import create_mock_client
            return create_mock_client()
        except Exception as e2:
            print(f"Error creating mock client: {e2}")
            return None

UPLOADS_DIR = os.path.join("data", "uploads")
META_FILE = os.path.join(UPLOADS_DIR, "uploads.json")
ALLOWED = [
    "PDF files (*.pdf)",
    "Word documents (*.doc *.docx)",
    "Text files (*.txt)",
    "CSV files (*.csv)",
    "Audio files (*.mp3 *.wav)",
    "Images (*.png *.jpg *.jpeg *.gif)",
    "All files (*)"
]


class FileProcessingWorker(QThread):
    """Worker thread for processing files with the ingestion pipeline"""
    progress_update = pyqtSignal(str)  # Status message
    file_processed = pyqtSignal(str, bool, str)  # filename, success, message
    finished_all = pyqtSignal()
    
    def __init__(self, file_paths, uploads_dir):
        super().__init__()
        self.file_paths = file_paths
        self.uploads_dir = uploads_dir
        self.client = None
        
    def run(self):
        """Process files in background thread"""
        if not INGESTION_AVAILABLE:
            for file_path in self.file_paths:
                filename = os.path.basename(file_path)
                self.file_processed.emit(filename, False, "Ingestion pipeline not available")
            self.finished_all.emit()
            return
            
        try:
            # Initialize ingestion client with image model disabled for faster startup
            self.progress_update.emit("Initializing AI processing...")
            self.client = get_ingestion_client()
            if self.client is None:
                raise Exception("Failed to initialize ingestion client")
            self.progress_update.emit("✓ AI processing initialized successfully")
            
            for file_path in self.file_paths:
                filename = os.path.basename(file_path)
                self.progress_update.emit(f"Processing {filename}...")
                
                try:
                    # Copy file to uploads directory first
                    timestamp = int(datetime.datetime.now().timestamp() * 1000)
                    dest_path = os.path.join(self.uploads_dir, f"{timestamp}_{filename}")
                    shutil.copyfile(file_path, dest_path)
                    
                    # Process with ingestion pipeline
                    result = self.client.upload_file(dest_path)
                    
                    success_msg = f"✓ Processed {result['chunks_processed']} chunks from {filename}"
                    self.file_processed.emit(filename, True, success_msg)
                    
                except Exception as e:
                    error_msg = f"✗ Failed to process {filename}: {str(e)}"
                    self.file_processed.emit(filename, False, error_msg)
                    
        except Exception as e:
            self.progress_update.emit(f"Error initializing: {str(e)}")
            
        self.finished_all.emit()


class UploadDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Upload Data Files")
        self.setModal(True)
        os.makedirs(UPLOADS_DIR, exist_ok=True)
        self.uploads = []  # list of dicts {path,name,type}
        self._load_meta()
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(700, 500)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header
        header = QLabel("Upload Knowledge Base Files")
        header.setFont(QFont("Inter", 20, QFont.Weight.Bold))
        header.setStyleSheet("color: #7c3aed; margin-bottom: 8px;")
        layout.addWidget(header)

        intro = QLabel("Upload files to use as your AI knowledge base. Supported formats: PDF, DOC, TXT, CSV, MP3, WAV, and images.")
        intro.setWordWrap(True)
        intro.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 14px; line-height: 1.4;")
        layout.addWidget(intro)

        # Upload section
        upload_frame = QFrame()
        upload_frame.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.05);
                border: 2px dashed rgba(124, 58, 237, 0.3);
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        upload_layout = QVBoxLayout(upload_frame)
        upload_layout.setAlignment(Qt.AlignCenter)
        
        self.add_btn = QPushButton("Choose Files to Upload")
        self.add_btn.setObjectName("primary")
        self.add_btn.setFixedHeight(44)
        self.add_btn.clicked.connect(self.select_files)
        
        upload_hint = QLabel("or drag and drop files here")
        upload_hint.setAlignment(Qt.AlignCenter)
        upload_hint.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 12px; margin-top: 8px;")
        
        upload_layout.addWidget(self.add_btn)
        upload_layout.addWidget(upload_hint)
        
        layout.addWidget(upload_frame)

        # Files list
        files_label = QLabel("Uploaded Files:")
        files_label.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        files_label.setStyleSheet("margin-top: 16px; margin-bottom: 8px;")
        layout.addWidget(files_label)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 8px;
                padding: 8px;
            }
            QListWidget::item {
                padding: 12px;
                border-radius: 6px;
                margin: 2px;
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.1);
            }
            QListWidget::item:selected {
                background: rgba(124, 58, 237, 0.2);
                border-color: #7c3aed;
            }
        """)
        layout.addWidget(self.list_widget)
        
        # Progress bar for processing
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: rgba(255,255,255,0.1);
                border-radius: 8px;
                text-align: center;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c3aed, stop:1 #06b6d4);
                border-radius: 8px;
            }
        """)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # Status text area
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setStyleSheet("""
            QTextEdit {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 8px;
                padding: 8px;
                color: #CCCCCC;
                font-size: 12px;
            }
        """)
        self.status_text.hide()
        layout.addWidget(self.status_text)
        
        self.refresh_list()

        # Bottom buttons
        btn_layout = QHBoxLayout()
        
        remove_btn = QPushButton("Remove Selected")
        remove_btn.setObjectName("ghost")
        remove_btn.clicked.connect(self.remove_selected)
        
        btn_layout.addWidget(remove_btn)
        btn_layout.addStretch()
        
        done_btn = QPushButton("Done")
        done_btn.setObjectName("primary")
        done_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(done_btn)
        layout.addLayout(btn_layout)

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, 
            "Choose files to upload", 
            "", 
            ";;".join(ALLOWED)
        )
        if not files:
            return
        
        # Show processing UI
        self.progress_bar.show()
        self.status_text.show()
        self.status_text.clear()
        self.add_btn.setEnabled(False)
        
        # Start background processing
        self.worker = FileProcessingWorker(files, UPLOADS_DIR)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.file_processed.connect(self.on_file_processed)
        self.worker.finished_all.connect(self.on_processing_finished)
        self.worker.start()
        
        self.progress_bar.setRange(0, len(files))
        self.progress_bar.setValue(0)
        self.processed_count = 0

    def refresh_list(self):
        self.list_widget.clear()
        for u in self.uploads:
            # Add file type indicator
            file_type = u.get('type', 'unknown')
            if 'pdf' in file_type:
                icon = "📕"
            elif 'image' in file_type:
                icon = "🖼️"
            elif 'text' in file_type:
                icon = "📘"
            elif 'audio' in file_type:
                icon = "🎵"
            elif 'csv' in file_type or 'excel' in file_type:
                icon = "📊"
            else:
                icon = "📄"
            
            # Add processing status
            processed = u.get('processed', False)
            status_icon = "✓" if processed else "⏳"
            
            display_text = f"{icon} {u['name']} — {u['type']} {status_icon}"
            self.list_widget.addItem(display_text)

    def remove_selected(self):
        current_row = self.list_widget.currentRow()
        if current_row < 0:
            return
            
        reply = QMessageBox.question(
            self, 
            "Remove File", 
            "Remove this file from your knowledge base?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            meta = self.uploads.pop(current_row)
            # Delete file from disk
            try:
                if os.path.exists(meta["path"]):
                    os.remove(meta["path"])
            except Exception:
                pass
            self._save_meta()
            self.refresh_list()

    def _save_meta(self):
        try:
            with open(META_FILE, "w", encoding="utf-8") as f:
                json.dump(self.uploads, f, indent=2)
        except Exception:
            pass

    def _load_meta(self):
        if os.path.exists(META_FILE):
            try:
                with open(META_FILE, "r", encoding="utf-8") as f:
                    self.uploads = json.load(f)
            except Exception:
                self.uploads = []

    def update_progress(self, message):
        """Update progress status"""
        self.status_text.append(message)
        # Auto-scroll to bottom
        cursor = self.status_text.textCursor()
        cursor.movePosition(cursor.End)
        self.status_text.setTextCursor(cursor)
    
    def on_file_processed(self, filename, success, message):
        """Handle individual file processing completion"""
        self.processed_count += 1
        self.progress_bar.setValue(self.processed_count)
        
        if success:
            # Add to uploads list
            mtype, _ = mimetypes.guess_type(filename)
            # Find the actual file path
            for f in os.listdir(UPLOADS_DIR):
                if filename in f:
                    file_path = os.path.join(UPLOADS_DIR, f)
                    self.uploads.append({
                        "path": file_path,
                        "name": filename,
                        "type": mtype or "unknown",
                        "processed": True
                    })
                    break
        
        self.update_progress(message)
        self.refresh_list()
    
    def on_processing_finished(self):
        """Handle completion of all file processing"""
        self.add_btn.setEnabled(True)
        self.update_progress("✓ Processing complete!")
        self._save_meta()
        
        # Show completion message
        if INGESTION_AVAILABLE:
            QMessageBox.information(
                self, 
                "Upload Complete", 
                f"Successfully processed {self.processed_count} files and added them to your knowledge base!"
            )
        else:
            QMessageBox.warning(
                self,
                "Upload Complete",
                "Files uploaded but AI processing is not available. Files are saved locally only."
            )

    def get_uploaded_files(self):
        """Return list of uploaded file paths"""
        return [u["path"] for u in self.uploads]