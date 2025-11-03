"""
File Parsers for PDF, DOCX, Images, and Audio Files
"""
import fitz  # PyMuPDF
from docx import Document
from PIL import Image
import whisper
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pathlib import Path
from typing import List, Tuple, Dict, Any
import re
import logging

from logger_config import setup_logger

logger = setup_logger(__name__)


class PDFParser:
    """Parser for PDF files"""
    
    def __init__(self):
        # Reduced chunk size to ensure it fits within CLIP's 77 token limit
        # ~4 chars per token, so 250 chars should be safe for 77 tokens
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=250,
            chunk_overlap=50,
            length_function=len,
        )
    
    def parse(self, file_path: str) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Parse PDF file and return chunks with metadata.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            List of tuples: (text_chunk, metadata_dict)
        """
        logger.info(f"Parsing PDF: {Path(file_path).name}")
        doc = fitz.open(file_path)
        chunks = []
        
        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                if text.strip():
                    # Split text into chunks
                    text_chunks = self.text_splitter.split_text(text)
                    logger.debug(f"Page {page_num + 1}: Extracted {len(text)} chars, split into {len(text_chunks)} chunks")
                    
                    for i, chunk in enumerate(text_chunks):
                        metadata = {
                            "source_file": Path(file_path).name,
                            "type": "text",
                            "page": page_num + 1,
                            "chunk_index": i
                        }
                        chunks.append((chunk, metadata))
            
            logger.info(f"PDF parsed: {len(chunks)} total chunks extracted")
            return chunks
        finally:
            doc.close()


class DOCXParser:
    """Parser for DOCX files"""
    
    def __init__(self):
        # Reduced chunk size to ensure it fits within CLIP's 77 token limit
        # ~4 chars per token, so 250 chars should be safe for 77 tokens
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=250,
            chunk_overlap=50,
            length_function=len,
        )
    
    def parse(self, file_path: str) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Parse DOCX file and return chunks with metadata.
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            List of tuples: (text_chunk, metadata_dict)
        """
        logger.info(f"Parsing DOCX: {Path(file_path).name}")
        doc = Document(file_path)
        full_text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        
        logger.debug(f"Extracted {len(full_text)} chars from DOCX")
        
        # Split text into chunks
        text_chunks = self.text_splitter.split_text(full_text)
        logger.debug(f"Split into {len(text_chunks)} chunks")
        
        chunks = []
        for i, chunk in enumerate(text_chunks):
            metadata = {
                "source_file": Path(file_path).name,
                "type": "text",
                "chunk_index": i
            }
            chunks.append((chunk, metadata))
        
        logger.info(f"DOCX parsed: {len(chunks)} total chunks extracted")
        return chunks


class AudioParser:
    """Parser for audio files using Whisper"""
    
    def __init__(self, model_name: str = "base.en", offline_mode: bool = True):
        """
        Initialize Whisper model.
        
        Args:
            model_name: Whisper model name (base.en, small, medium, etc.)
        """
        import os
        logger.info(f"Loading Whisper model: {model_name}")
        if offline_mode:
            logger.info("  (Offline mode: using local cache only)")
        else:
            logger.info("  (Online mode: will download if not in cache)")
        
        try:
            # Whisper automatically uses local cache if available
            # If offline_mode=False and model not in cache, it will try to download
            self.model = whisper.load_model(model_name)
            logger.info("✓ Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {str(e)}")
            # If model not found locally, provide helpful error
            error_msg = str(e).lower()
            if offline_mode and ('not found' in error_msg or 'does not exist' in error_msg):
                raise RuntimeError(
                    f"Whisper model '{model_name}' not found in local cache.\n"
                    f"Please download it first (while online) using:\n"
                    f"  python ingestion_pipeline/setup_offline.py\n"
                    f"Or manually:\n"
                    f"  python -c \"import whisper; whisper.load_model('{model_name}')\""
                ) from e
            else:
                raise
    
    def _format_timestamp(self, seconds: float) -> str:
        """Convert seconds to HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def _chunk_by_time(self, segments: List[Dict], chunk_duration: int = 10) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Chunk transcript by time intervals (default 10 seconds).
        
        Args:
            segments: List of segments from Whisper transcription
            chunk_duration: Duration in seconds for each chunk
            
        Returns:
            List of tuples: (transcript_chunk, metadata_dict)
        """
        chunks = []
        current_chunk = []
        current_start = None
        current_end = None
        
        for segment in segments:
            if current_start is None:
                current_start = segment["start"]
            
            current_chunk.append(segment["text"].strip())
            current_end = segment["end"]
            
            # If chunk duration exceeded, save chunk and start new one
            if current_end - current_start >= chunk_duration:
                chunk_text = " ".join(current_chunk)
                metadata = {
                    "type": "audio",
                    "start": self._format_timestamp(current_start),
                    "end": self._format_timestamp(current_end),
                    "start_seconds": current_start,
                    "end_seconds": current_end
                }
                chunks.append((chunk_text, metadata))
                current_chunk = []
                current_start = None
        
        # Add remaining chunk if any
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            metadata = {
                "type": "audio",
                "start": self._format_timestamp(current_start),
                "end": self._format_timestamp(current_end),
                "start_seconds": current_start,
                "end_seconds": current_end
            }
            chunks.append((chunk_text, metadata))
        
        return chunks
    
    def parse(self, file_path: str, chunk_duration: int = 10) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Transcribe audio file and return chunks with metadata.
        
        Args:
            file_path: Path to audio file
            chunk_duration: Duration in seconds for each chunk
            
        Returns:
            List of tuples: (transcript_chunk, metadata_dict)
        """
        logger.info(f"Transcribing audio file: {Path(file_path).name}")
        try:
            result = self.model.transcribe(file_path, word_timestamps=False)
            
            # Get segments with timestamps
            segments = result.get("segments", [])
            logger.debug(f"Transcription complete: {len(segments)} segments")
            
            # Chunk by time intervals
            chunks = self._chunk_by_time(segments, chunk_duration)
            
            # Add source_file to all metadata
            source_file = Path(file_path).name
            chunks_with_metadata = []
            for chunk_text, metadata in chunks:
                metadata["source_file"] = source_file
                chunks_with_metadata.append((chunk_text, metadata))
            
            logger.info(f"Audio transcribed: {len(chunks_with_metadata)} chunks created")
            return chunks_with_metadata
        except Exception as e:
            logger.error(f"Error transcribing audio file {Path(file_path).name}: {str(e)}", exc_info=True)
            raise


class ImageParser:
    """Parser for image files"""
    
    def parse(self, file_path: str) -> Tuple[Image.Image, Dict[str, Any]]:
        """
        Load image file and return PIL Image with metadata.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Tuple: (PIL.Image, metadata_dict)
        """
        logger.info(f"Loading image: {Path(file_path).name}")
        try:
            image = Image.open(file_path).convert("RGB")
            
            metadata = {
                "source_file": Path(file_path).name,
                "type": "image",
                "format": image.format,
                "size": image.size,
                "mode": image.mode
            }
            
            logger.debug(f"Image loaded: {image.size}, format: {image.format}")
            return image, metadata
        except Exception as e:
            logger.error(f"Error loading image {Path(file_path).name}: {str(e)}", exc_info=True)
            raise

