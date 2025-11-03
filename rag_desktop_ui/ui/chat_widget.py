# ui/chat_widget.py
import os
import sys
import json
import datetime
import mimetypes
import subprocess
import platform
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QFrame, QLineEdit,
    QPushButton, QHBoxLayout, QFileDialog, QLabel, QSpacerItem, QSizePolicy,
    QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import qtawesome as qta

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


class ChatWidget(QWidget):
    def __init__(self, chat_dir="./data/chats"):
        super().__init__()
        self.chat_dir = chat_dir
        self.chat_history = []
        self.current_chat_file = None
        
        # Initialize ingestion client for RAG functionality (lazy loaded)
        self.ingestion_client = None
        # We'll initialize this when first needed to avoid startup issues

        # ---- Main Layout ----
        self.setStyleSheet("""
            QWidget#chat_area {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0e111a, stop:0.5 #151922, stop:1 #0e111a);
                border-left: 1px solid rgba(255,255,255,0.08);
            }
            QWidget {
                background-color: transparent;
                color: #FFFFFF;
                font-family: 'Inter', 'SF Pro Display', 'Segoe UI', sans-serif;
            }
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.12);
                color: #E6E6E6;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 18px;
                padding: 12px 18px;
                font-size: 14px;
                font-weight: 400;
                selection-background-color: #6a5acd;
            }
            QLineEdit:focus {
                border: 2px solid qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #7c3aed, stop:1 #06b6d4
                );
                background-color: rgba(255, 255, 255, 0.15);
                color: #FFFFFF;
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.5);
                font-style: italic;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c3aed, stop:1 #06b6d4);
                border: none;
                border-radius: 18px;
                color: white;
                font-weight: 600;
                padding: 12px 16px;
                min-width: 50px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8b5cf6, stop:1 #0891b2);
                transform: scale(1.02);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6d28d9, stop:1 #0e7490);
            }
            QLabel {
                color: white;
            }
            QLabel:hover {
                color: #50a8ff;
            }
            a {
                color: #06b6d4;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scrollable chat area
        self.chat_area = QScrollArea()
        self.chat_area.setWidgetResizable(True)
        self.chat_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: rgba(255, 255, 255, 0.05);
                width: 8px;
                border-radius: 4px;
                margin: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(124, 58, 237, 0.6);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(124, 58, 237, 0.8);
            }
        """)
        
        self.chat_widget = QWidget()
        self.chat_widget.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setContentsMargins(20, 20, 20, 20)
        self.chat_layout.setSpacing(16)
        
        self.chat_area.setWidget(self.chat_widget)

        # Input area with modern styling
        input_container = QFrame()
        input_container.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.06);
                border-top: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 0px;
            }
        """)
        
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(24, 20, 24, 20)
        input_layout.setSpacing(16)

        self.upload_button = QPushButton()
        self.upload_button.setIcon(qta.icon('fa.upload', color='white'))
        self.upload_button.setToolTip("Upload a file")
        self.upload_button.setFixedSize(48, 48)
        self.upload_button.clicked.connect(self.upload_file)

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Type your message here...")
        self.input_box.returnPressed.connect(self.send_message)  # Enter key support
        self.input_box.setFixedHeight(48)
        
        # Add subtle shadow to input box
        input_shadow = QGraphicsDropShadowEffect()
        input_shadow.setBlurRadius(20)
        input_shadow.setOffset(0, 2)
        input_shadow.setColor(QColor(0, 0, 0, 80))
        self.input_box.setGraphicsEffect(input_shadow)

        self.send_button = QPushButton()
        self.send_button.setIcon(qta.icon('fa.paper-plane', color='white'))
        self.send_button.setToolTip("Send message")
        self.send_button.setFixedSize(48, 48)
        self.send_button.clicked.connect(self.send_message)

        input_layout.addWidget(self.upload_button)
        input_layout.addWidget(self.input_box)
        input_layout.addWidget(self.send_button)

        # Add to main layout
        layout.addWidget(self.chat_area)
        layout.addWidget(input_container)
        self.setLayout(layout)

    # ---- Chat Management ----
    def start_new_chat(self):
        self.clear_chat()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.current_chat_file = os.path.join(self.chat_dir, f"chat_{timestamp}.json")
        self.chat_history = []

    def load_chat(self, file_path):
        """Load chat history from file"""
        if not os.path.exists(file_path):
            return
        self.clear_chat()
        self.current_chat_file = file_path
        with open(file_path, "r", encoding="utf-8") as f:
            self.chat_history = json.load(f)
        for msg in self.chat_history:
            sender = "user" if msg["role"].lower() == "you" else "ai"
            self.add_message(msg["content"], sender=sender, save=False)

    def clear_chat(self):
        """Clear all messages from chat area"""
        for i in reversed(range(self.chat_layout.count())):
            item = self.chat_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()

    def add_message(self, text, sender="user", save=True):
        """Add ChatGPT-style message bubble"""
        # Create message label
        message_label = QLabel(text)
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextBrowserInteraction)
        message_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        message_label.setTextFormat(Qt.RichText)
        message_label.linkActivated.connect(self.open_file)
        
        # Add timestamp
        timestamp = datetime.datetime.now().strftime("%H:%M")
        
        # Style based on sender
        if sender.lower() == "user" or sender.lower() == "you":
            message_label.setStyleSheet("""
                QLabel {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #7c3aed, stop:1 #06b6d4);
                    color: white;
                    padding: 12px 16px;
                    border-radius: 18px;
                    font-size: 14px;
                    line-height: 1.4;
                    max-width: 400px;
                }
            """)
            alignment = Qt.AlignRight
        else:
            message_label.setStyleSheet("""
                QLabel {
                    background-color: rgba(255, 255, 255, 0.08);
                    color: #EAEAEA;
                    padding: 12px 16px;
                    border-radius: 18px;
                    font-size: 14px;
                    line-height: 1.4;
                    max-width: 400px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }
            """)
            alignment = Qt.AlignLeft

        # Create container for proper alignment
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add timestamp label
        time_label = QLabel(timestamp)
        time_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.5);
                font-size: 11px;
                padding: 4px 8px;
                background: transparent;
            }
        """)
        
        if alignment == Qt.AlignRight:
            container_layout.addStretch()
            container_layout.addWidget(time_label)
            container_layout.addWidget(message_label)
        else:
            container_layout.addWidget(message_label)
            container_layout.addWidget(time_label)
            container_layout.addStretch()

        # Add to chat layout
        self.chat_layout.addWidget(container)
        
        # Auto-scroll to bottom
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )

        # Save to history
        if save:
            role = "You" if sender.lower() == "user" or sender.lower() == "you" else "AI"
            self.chat_history.append({"role": role, "content": text})
            self.save_chat()

    def send_message(self):
        user_text = self.input_box.text().strip()
        if not user_text:
            return

        # Show user message
        self.add_message(user_text, sender="user")
        self.input_box.clear()

        # Generate AI response using RAG if available
        ai_response = self.generate_ai_response(user_text)
        self.add_message(ai_response, sender="ai")
    
    def generate_ai_response(self, query):
        """Generate AI response using RAG or fallback"""
        # Lazy load ingestion client if not already loaded
        if self.ingestion_client is None and INGESTION_AVAILABLE:
            self.ingestion_client = get_ingestion_client()
            if self.ingestion_client:
                print("✓ RAG functionality enabled")
        
        if self.ingestion_client:
            try:
                # Search the vector database
                search_results = self.ingestion_client.search(query, n_results=3)
                
                if search_results["documents"] and search_results["documents"][0]:
                    # We have relevant documents
                    relevant_docs = search_results["documents"][0]
                    
                    # Create context from relevant documents
                    context = "\n\n".join(relevant_docs[:2])  # Use top 2 results
                    
                    # Simple response generation (you can enhance this with an LLM)
                    response = f"Based on your uploaded documents, here's what I found:\n\n{context}\n\n"
                    response += f"This information is relevant to your query: '{query}'"
                    
                    return response
                else:
                    return f"I searched your uploaded documents but couldn't find specific information about '{query}'. You may want to upload more relevant documents or try rephrasing your question."
                    
            except Exception as e:
                return f"I encountered an error while searching your documents: {str(e)}. Please try again."
        else:
            # Fallback when RAG is not available
            return f"RAG functionality is not available. Your query was: '{query}'. Please ensure the ingestion pipeline is properly set up to get AI-powered responses based on your uploaded documents."

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
            self.add_message(msg, sender="user")

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

    def set_uploaded_files(self, file_paths):
        """
        Receives uploaded files from upload dialog.
        Shows information about the knowledge base.
        """
        if not file_paths:
            return
            
        files_display = "\n".join([f"• {os.path.basename(p)}" for p in file_paths])
        
        if self.ingestion_client:
            try:
                # Get collection info
                info = self.ingestion_client.get_collection_info()
                system_msg = f"📚 Knowledge Base Ready!\n\n"
                system_msg += f"Files processed: {len(file_paths)}\n{files_display}\n\n"
                system_msg += f"Total items in database: {info['count']}\n\n"
                system_msg += "You can now ask questions about your uploaded documents!"
            except Exception as e:
                system_msg = f"📚 Files uploaded: {len(file_paths)}\n{files_display}\n\n"
                system_msg += f"Note: There was an issue accessing the knowledge base: {str(e)}"
        else:
            system_msg = f"📚 Files uploaded: {len(file_paths)}\n{files_display}\n\n"
            system_msg += "Note: RAG functionality is not available. Files are stored locally only."
        
        # Add as a non-saver display (save=False) so a system message doesn't duplicate in saved history
        self.add_message(system_msg, sender="ai", save=False)