"""
Main Ingestion Script
Processes PDF, DOCX, images, and audio files and stores them in ChromaDB.
"""
import os
from pathlib import Path
from typing import List
from sentence_transformers import SentenceTransformer
from transformers import AutoProcessor, AutoModel
import chromadb
import logging
import torch

from db_setup import setup_chromadb
from parsers import PDFParser, DOCXParser, AudioParser, ImageParser
from logger_config import setup_logger

logger = setup_logger(__name__)


class IngestionPipeline:
    """Main ingestion pipeline for multimodal files"""
    
    def __init__(self, db_path: str = "chroma_local_db", 
                 text_model: str = "BAAI/bge-base-en", 
                 image_model: str = "google/siglip-base-patch16-224",
                 offline_mode: bool = True):
        """
        Initialize the ingestion pipeline.
        
        Args:
            db_path: Path to ChromaDB storage directory
            text_model: SentenceTransformer model name for text embeddings
            image_model: HuggingFace model name for image embeddings (SigLIP)
            offline_mode: If True, only use cached models (no downloads)
        """
        # Setup ChromaDB
        self.client, self.collection = setup_chromadb(db_path)
        
        # Store offline mode
        self.offline_mode = offline_mode
        
        # Load text embedding model (BAAI/bge-base-en)
        logger.info(f"Loading text embedding model: {text_model}")
        if offline_mode:
            logger.info("  (Offline mode: using local cache only)")
            original_hf_offline = os.environ.get('HF_HUB_OFFLINE', None)
            os.environ['HF_HUB_OFFLINE'] = '1'
        else:
            logger.info("  (Online mode: will download if not in cache)")
        
        try:
            self.text_embedding_model = SentenceTransformer(text_model)
            logger.info("✓ Text embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load text embedding model: {str(e)}")
            error_msg = str(e).lower()
            if offline_mode and ('not found' in error_msg or 'does not exist' in error_msg or 'offline' in error_msg):
                raise RuntimeError(
                    f"Text model '{text_model}' not found in local cache.\n"
                    f"Please download it first (while online) using:\n"
                    f"  python ingestion_pipeline/setup_offline.py\n"
                ) from e
            else:
                raise
        finally:
            if offline_mode:
                if original_hf_offline is None:
                    os.environ.pop('HF_HUB_OFFLINE', None)
                else:
                    os.environ['HF_HUB_OFFLINE'] = original_hf_offline
        
        # Load image embedding model (SigLIP)
        if image_model is None:
            logger.info("Image embedding model disabled (image_model=None)")
            self.image_model = None
            self.image_processor = None
        else:
            logger.info(f"Loading image embedding model: {image_model}")
            if offline_mode:
                original_hf_offline = os.environ.get('HF_HUB_OFFLINE', None)
                os.environ['HF_HUB_OFFLINE'] = '1'
            else:
                logger.info("  (Online mode: will download if not in cache)")
            
            try:
                self.image_model = AutoModel.from_pretrained(image_model)
                self.image_processor = AutoProcessor.from_pretrained(image_model)
                self.image_model.eval()  # Set to evaluation mode
                logger.info("✓ Image embedding model (SigLIP) loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load image embedding model: {str(e)}")
                error_msg = str(e).lower()
                if offline_mode and ('not found' in error_msg or 'does not exist' in error_msg or 'offline' in error_msg):
                    raise RuntimeError(
                        f"Image model '{image_model}' not found in local cache.\n"
                        f"Please download it first (while online) using:\n"
                        f"  python ingestion_pipeline/setup_offline.py\n"
                    ) from e
                else:
                    raise
            finally:
                if offline_mode:
                    if original_hf_offline is None:
                        os.environ.pop('HF_HUB_OFFLINE', None)
                    else:
                        os.environ['HF_HUB_OFFLINE'] = original_hf_offline
        
        # Get max sequence length for text model
        try:
            if hasattr(self.text_embedding_model, 'tokenizer') and hasattr(self.text_embedding_model.tokenizer, 'model_max_length'):
                self.max_seq_length = self.text_embedding_model.tokenizer.model_max_length
            elif hasattr(self.text_embedding_model, 'max_seq_length'):
                self.max_seq_length = self.text_embedding_model.max_seq_length
            else:
                # Default for BGE models (typically 512)
                self.max_seq_length = 512
        except:
            self.max_seq_length = 512
        
        logger.info(f"Max sequence length for text: {self.max_seq_length} tokens")
        
        # Initialize parsers (with offline mode setting)
        self.pdf_parser = PDFParser()
        self.docx_parser = DOCXParser()
        self.audio_parser = AudioParser(offline_mode=offline_mode)
        self.image_parser = ImageParser()
        
        # Supported file extensions
        self.supported_extensions = {
            '.pdf': 'pdf',
            '.docx': 'docx',
            '.mp3': 'audio',
            '.wav': 'audio',
            '.m4a': 'audio',
            '.flac': 'audio',
            '.jpg': 'image',
            '.jpeg': 'image',
            '.png': 'image',
            '.gif': 'image',
            '.bmp': 'image',
            '.webp': 'image'
        }
    
    def _get_file_type(self, file_path: str) -> str:
        """Get file type based on extension"""
        ext = Path(file_path).suffix.lower()
        return self.supported_extensions.get(ext, None)
    
    def _truncate_text_for_encoding(self, text: str) -> str:
        """
        Truncate text to fit within the model's maximum sequence length.
        Uses tokenizer-based truncation with max_length parameter.
        
        Args:
            text: Text to truncate
            
        Returns:
            Truncated text that fits within token limit
        """
        if not text or not text.strip():
            return text
        
        original_len = len(text)
        try:
            # Try to access the tokenizer from the model
            tokenizer = None
            if hasattr(self.text_embedding_model, 'tokenizer'):
                tokenizer = self.text_embedding_model.tokenizer
            elif hasattr(self.text_embedding_model, '_first_module'):
                # Some SentenceTransformer models wrap the tokenizer
                try:
                    first_module = self.text_embedding_model._first_module()
                    if hasattr(first_module, 'tokenizer'):
                        tokenizer = first_module.tokenizer
                except:
                    pass
            
            if tokenizer is not None:
                # Use tokenizer with truncation directly - this is the most reliable method
                try:
                    # Tokenize with truncation enabled - this ensures it fits
                    encoded = tokenizer(
                        text,
                        add_special_tokens=True,
                        truncation=True,
                        max_length=self.max_seq_length,
                        return_tensors="pt" if torch.cuda.is_available() else None,
                        padding=False
                    )
                    
                    # Extract token IDs - handle both dict and list returns
                    if isinstance(encoded, dict):
                        tokens = encoded['input_ids']
                        # Convert tensor to list if needed
                        if hasattr(tokens, 'tolist'):
                            tokens = tokens.tolist()
                    elif isinstance(encoded, list):
                        tokens = encoded
                    else:
                        tokens = encoded
                    
                    # Handle list of lists (batch) or nested structure
                    if isinstance(tokens, list):
                        if len(tokens) > 0:
                            if isinstance(tokens[0], list):
                                tokens = tokens[0]
                            elif hasattr(tokens[0], 'tolist'):
                                tokens = tokens[0].tolist()
                    
                    # Decode back to text (this will be properly truncated)
                    truncated_text = tokenizer.decode(tokens, skip_special_tokens=True)
                    
                    # Verify the truncated text fits
                    verify_encoded = tokenizer(
                        truncated_text, 
                        add_special_tokens=True, 
                        return_tensors="pt" if torch.cuda.is_available() else None
                    )
                    verify_tokens = verify_encoded['input_ids'] if isinstance(verify_encoded, dict) else verify_encoded
                    if hasattr(verify_tokens, 'tolist'):
                        verify_tokens = verify_tokens.tolist()
                    if isinstance(verify_tokens, list) and len(verify_tokens) > 0 and isinstance(verify_tokens[0], list):
                        verify_tokens = verify_tokens[0]
                    
                    if len(verify_tokens) > self.max_seq_length:
                        logger.warning(f"Truncated text still exceeds limit: {len(verify_tokens)} > {self.max_seq_length}")
                        # Force truncate tokens
                        verify_tokens = verify_tokens[:self.max_seq_length]
                        truncated_text = tokenizer.decode(verify_tokens, skip_special_tokens=True)
                    
                    if len(text) != len(truncated_text):
                        logger.debug(f"Truncated text from {len(text)} to {len(truncated_text)} chars, tokens: {len(tokens)}")
                    
                    return truncated_text
                except Exception as tokenizer_error:
                    logger.warning(f"Tokenizer truncation failed: {tokenizer_error}, using character-based truncation")
            
            # Fallback: truncate by character count (very conservative)
            # CLIP tokenizer can have varying tokens per char, so use very safe limit
            # ~2.5-3 chars per token for English, so for 77 tokens: ~200 chars max
            max_chars = int((self.max_seq_length - 5) * 2.5)  # Very conservative estimate
            if len(text) > max_chars:
                logger.debug(f"Character-based truncation: {len(text)} -> {max_chars} chars")
                return text[:max_chars]
            return text
            
        except Exception as e:
            logger.error(f"Error in truncation: {str(e)}, using character fallback")
            # Ultimate fallback: very conservative character truncation
            max_chars = 200  # Safe for 77 tokens
            if len(text) > max_chars:
                return text[:max_chars]
            return text
    
    def _generate_id(self, filename: str, chunk_type: str, index: int = None) -> str:
        """Generate unique ID for a chunk"""
        base_name = Path(filename).stem
        if chunk_type == "image":
            return f"{filename}_image"
        elif chunk_type == "audio":
            return f"{base_name}_segment_{index}"
        elif chunk_type == "text":
            return f"{base_name}_chunk_{index}"
        else:
            return f"{base_name}_{chunk_type}_{index}"
    
    def process_file(self, file_path: str) -> tuple:
        """
        Process a single file and return batch data.
        
        Args:
            file_path: Path to file to process
            
        Returns:
            Tuple of lists: (ids, embeddings, documents, metadatas)
        """
        file_type = self._get_file_type(file_path)
        if not file_type:
            logger.warning(f"Skipping unsupported file: {file_path}")
            return ([], [], [], [])
        
        logger.info(f"Processing {file_type.upper()}: {Path(file_path).name}")
        
        ids_batch = []
        embeddings_batch = []
        documents_batch = []
        metadatas_batch = []
        
        try:
            if file_type == 'pdf':
                chunks = self.pdf_parser.parse(file_path)
                for i, (text_chunk, metadata) in enumerate(chunks):
                    # Truncate text to fit CLIP's token limit
                    truncated_text = self._truncate_text_for_encoding(text_chunk)
                    logger.debug(f"PDF Chunk {i}: original={len(text_chunk)} chars, truncated={len(truncated_text)} chars")
                    
                    try:
                        embedding = self.text_embedding_model.encode(
                            truncated_text,
                            normalize_embeddings=False,
                            show_progress_bar=False,
                            convert_to_numpy=True
                        ).tolist()
                        logger.debug(f"Successfully encoded PDF chunk {i}, embedding dim: {len(embedding)}")
                    except Exception as enc_error:
                        logger.error(f"Encoding failed for PDF chunk {i}: {enc_error}")
                        # If still fails, try with even shorter text
                        max_chars = 200  # Very conservative
                        truncated_text = text_chunk[:max_chars] if len(text_chunk) > max_chars else text_chunk
                        logger.warning(f"Retrying with {len(truncated_text)} chars")
                        embedding = self.text_embedding_model.encode(
                            truncated_text,
                            normalize_embeddings=False,
                            show_progress_bar=False,
                            convert_to_numpy=True
                        ).tolist()
                    chunk_id = self._generate_id(Path(file_path).name, "text", i)
                    
                    ids_batch.append(chunk_id)
                    embeddings_batch.append(embedding)
                    documents_batch.append(text_chunk)  # Store original text, not truncated
                    metadatas_batch.append(metadata)
            
            elif file_type == 'docx':
                chunks = self.docx_parser.parse(file_path)
                for i, (text_chunk, metadata) in enumerate(chunks):
                    # Truncate text to fit CLIP's token limit
                    truncated_text = self._truncate_text_for_encoding(text_chunk)
                    logger.debug(f"DOCX Chunk {i}: original={len(text_chunk)} chars, truncated={len(truncated_text)} chars")
                    
                    try:
                        embedding = self.text_embedding_model.encode(
                            truncated_text,
                            normalize_embeddings=False,
                            show_progress_bar=False,
                            convert_to_numpy=True
                        ).tolist()
                    except Exception as enc_error:
                        logger.error(f"Encoding failed for DOCX chunk {i}: {enc_error}")
                        max_chars = 200  # Very conservative
                        truncated_text = text_chunk[:max_chars] if len(text_chunk) > max_chars else text_chunk
                        logger.warning(f"Retrying with {len(truncated_text)} chars")
                        embedding = self.text_embedding_model.encode(
                            truncated_text,
                            normalize_embeddings=False,
                            show_progress_bar=False,
                            convert_to_numpy=True
                        ).tolist()
                    chunk_id = self._generate_id(Path(file_path).name, "text", i)
                    
                    ids_batch.append(chunk_id)
                    embeddings_batch.append(embedding)
                    documents_batch.append(text_chunk)  # Store original text, not truncated
                    metadatas_batch.append(metadata)
            
            elif file_type == 'audio':
                chunks = self.audio_parser.parse(file_path)
                for i, (transcript_chunk, metadata) in enumerate(chunks):
                    # Truncate text to fit CLIP's token limit
                    truncated_text = self._truncate_text_for_encoding(transcript_chunk)
                    logger.debug(f"Audio chunk {i}: original={len(transcript_chunk)} chars, truncated={len(truncated_text)} chars")
                    
                    try:
                        embedding = self.text_embedding_model.encode(
                            truncated_text,
                            normalize_embeddings=False,
                            show_progress_bar=False,
                            convert_to_numpy=True
                        ).tolist()
                    except Exception as enc_error:
                        logger.error(f"Encoding failed for audio chunk {i}: {enc_error}")
                        max_chars = 200  # Very conservative
                        truncated_text = transcript_chunk[:max_chars] if len(transcript_chunk) > max_chars else transcript_chunk
                        logger.warning(f"Retrying with {len(truncated_text)} chars")
                        embedding = self.text_embedding_model.encode(
                            truncated_text,
                            normalize_embeddings=False,
                            show_progress_bar=False,
                            convert_to_numpy=True
                        ).tolist()
                    chunk_id = self._generate_id(Path(file_path).name, "audio", i)
                    
                    ids_batch.append(chunk_id)
                    embeddings_batch.append(embedding)
                    documents_batch.append(transcript_chunk)  # Store original text, not truncated
                    metadatas_batch.append(metadata)
            
            elif file_type == 'image':
                image, metadata = self.image_parser.parse(file_path)
                
                # Use SigLIP for image embedding
                try:
                    inputs = self.image_processor(images=image, return_tensors="pt")
                    with torch.no_grad():
                        image_embeds = self.image_model.get_image_features(**inputs)
                    # Normalize the embedding
                    image_embeds = image_embeds / image_embeds.norm(p=2, dim=-1, keepdim=True)
                    embedding = image_embeds.squeeze().cpu().numpy().tolist()
                    logger.debug(f"Successfully encoded image, embedding dim: {len(embedding)}")
                except Exception as img_error:
                    logger.error(f"Error encoding image: {img_error}", exc_info=True)
                    raise
                
                chunk_id = self._generate_id(Path(file_path).name, "image")
                
                ids_batch.append(chunk_id)
                embeddings_batch.append(embedding)
                documents_batch.append("N/A")  # Images use "N/A" as document text
                metadatas_batch.append(metadata)
            
            logger.info(f"Successfully processed {len(ids_batch)} chunks from {Path(file_path).name}")
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}", exc_info=True)
            return ([], [], [], [])
        
        return (ids_batch, embeddings_batch, documents_batch, metadatas_batch)
    
    def ingest_directory(self, directory_path: str, batch_size: int = 100):
        """
        Process all supported files in a directory and ingest into ChromaDB.
        
        Args:
            directory_path: Path to directory containing files
            batch_size: Number of items to batch before inserting into ChromaDB
        """
        directory = Path(directory_path)
        if not directory.exists():
            raise ValueError(f"Directory does not exist: {directory_path}")
        
        logger.info(f"{'='*60}")
        logger.info(f"Starting ingestion from: {directory.absolute()}")
        logger.info(f"{'='*60}")
        
        # Collect all supported files
        files_to_process = []
        for ext, file_type in self.supported_extensions.items():
            files_to_process.extend(directory.glob(f"*{ext}"))
            files_to_process.extend(directory.glob(f"*{ext.upper()}"))
        
        if not files_to_process:
            logger.warning("No supported files found in directory")
            return
        
        logger.info(f"Found {len(files_to_process)} file(s) to process")
        
        # Process files and batch insert
        all_ids = []
        all_embeddings = []
        all_documents = []
        all_metadatas = []
        
        for file_path in files_to_process:
            ids, embeddings, documents, metadatas = self.process_file(str(file_path))
            
            all_ids.extend(ids)
            all_embeddings.extend(embeddings)
            all_documents.extend(documents)
            all_metadatas.extend(metadatas)
            
            # Batch insert if we've accumulated enough items
            if len(all_ids) >= batch_size:
                self.batch_insert(all_ids, all_embeddings, all_documents, all_metadatas)
                all_ids, all_embeddings, all_documents, all_metadatas = [], [], [], []
        
        # Insert remaining items
        if all_ids:
            self.batch_insert(all_ids, all_embeddings, all_documents, all_metadatas)
        
        logger.info(f"{'='*60}")
        logger.info(f"Ingestion complete! Total items in collection: {self.collection.count()}")
        logger.info(f"{'='*60}")
    
    def batch_insert(self, ids: List[str], embeddings: List[List[float]], 
                     documents: List[str], metadatas: List[dict]):
        """Insert a batch of items into ChromaDB"""
        if not ids:
            return
        
        try:
            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"Successfully inserted {len(ids)} items into ChromaDB")
        except Exception as e:
            logger.error(f"Error inserting batch: {str(e)}", exc_info=True)


def main():
    """Main entry point for the ingestion script"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest files into ChromaDB")
    parser.add_argument(
        "directory",
        type=str,
        help="Directory containing files to ingest"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="chroma_local_db",
        help="Path to ChromaDB storage directory (default: chroma_local_db)"
    )
    parser.add_argument(
        "--embedding-model",
        type=str,
        default="clip-ViT-B-32",
        help="SentenceTransformer model name (default: clip-ViT-B-32)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for inserting items (default: 100)"
    )
    parser.add_argument(
        "--offline-mode",
        type=str,
        default="1",
        choices=["0", "1"],
        help="Enable offline mode (1) or allow downloads (0) (default: 1)"
    )
    
    args = parser.parse_args()
    
    # Convert offline_mode string to boolean
    offline_mode = args.offline_mode == "1"
    
    # Create pipeline and ingest
    pipeline = IngestionPipeline(
        db_path=args.db_path,
        text_model=args.text_model,
        image_model=args.image_model,
        offline_mode=offline_mode
    )
    
    pipeline.ingest_directory(
        directory_path=args.directory,
        batch_size=args.batch_size
    )


if __name__ == "__main__":
    main()

