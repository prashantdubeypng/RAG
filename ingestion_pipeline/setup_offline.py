"""
Setup script to download all required models offline.
Run this script once while connected to the internet to download all models locally.
After this, the pipeline will work completely offline.
"""
import os
import sys
from pathlib import Path

def download_text_model(model_name: str = "BAAI/bge-base-en"):
    """Download SentenceTransformer text model to local cache"""
    print(f"\n{'='*60}")
    print(f"Downloading text embedding model: {model_name}")
    print(f"{'='*60}")
    
    try:
        from sentence_transformers import SentenceTransformer
        
        print(f"Downloading {model_name} to local cache...")
        model = SentenceTransformer(model_name)
        print(f"✓ Successfully downloaded {model_name}")
        
        # Test that it works
        test_embedding = model.encode("test", show_progress_bar=False)
        print(f"✓ Model test successful (embedding dimension: {len(test_embedding)})")
        
        return True
    except Exception as e:
        print(f"✗ Error downloading text model: {str(e)}")
        return False


def download_image_model(model_name: str = "google/siglip-base-patch16-224"):
    """Download HuggingFace image model (SigLIP) to local cache"""
    print(f"\n{'='*60}")
    print(f"Downloading image embedding model: {model_name}")
    print(f"{'='*60}")
    
    try:
        from transformers import AutoProcessor, AutoModel
        from PIL import Image
        import torch
        import io
        
        print(f"Downloading {model_name} to local cache...")
        model = AutoModel.from_pretrained(model_name)
        processor = AutoProcessor.from_pretrained(model_name)
        print(f"✓ Successfully downloaded {model_name}")
        
        # Test that it works (create a dummy image)
        dummy_image = Image.new('RGB', (224, 224), color='red')
        inputs = processor(images=dummy_image, return_tensors="pt")
        with torch.no_grad():
            image_embeds = model.get_image_features(**inputs)
        image_embeds = image_embeds / image_embeds.norm(p=2, dim=-1, keepdim=True)
        print(f"✓ Model test successful (embedding dimension: {image_embeds.shape[-1]})")
        
        return True
    except Exception as e:
        print(f"✗ Error downloading image model: {str(e)}")
        return False


def download_whisper_model(model_name: str = "base.en"):
    """Download Whisper model to local cache"""
    print(f"\n{'='*60}")
    print(f"Downloading Whisper model: {model_name}")
    print(f"{'='*60}")
    
    try:
        import whisper
        
        print(f"Downloading {model_name} to local cache...")
        model = whisper.load_model(model_name)
        print(f"✓ Successfully downloaded {model_name}")
        
        return True
    except Exception as e:
        print(f"✗ Error downloading Whisper model: {str(e)}")
        return False


def main():
    """Download all required models"""
    print("\n" + "="*60)
    print("OFFLINE MODEL SETUP")
    print("="*60)
    print("\nThis script will download all required models to your local cache.")
    print("After running this, you can use the pipeline completely offline.")
    print("\n" + "-"*60 + "\n")
    
    # Check internet connection (optional)
    import socket
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        print("✓ Internet connection detected\n")
    except OSError:
        print("⚠ No internet connection detected. Please connect to download models.\n")
        sys.exit(1)
    
    # Download text model
    text_model = os.getenv("TEXT_MODEL", "BAAI/bge-base-en")
    text_success = download_text_model(text_model)
    
    # Download image model
    image_model = os.getenv("IMAGE_MODEL", "google/siglip-base-patch16-224")
    image_success = download_image_model(image_model)
    
    # Download Whisper model
    whisper_model = os.getenv("WHISPER_MODEL", "base.en")
    whisper_success = download_whisper_model(whisper_model)
    
    # Summary
    print(f"\n{'='*60}")
    print("DOWNLOAD SUMMARY")
    print(f"{'='*60}")
    print(f"Text model ({text_model}): {'✓ Downloaded' if text_success else '✗ Failed'}")
    print(f"Image model ({image_model}): {'✓ Downloaded' if image_success else '✗ Failed'}")
    print(f"Whisper model ({whisper_model}): {'✓ Downloaded' if whisper_success else '✗ Failed'}")
    
    if text_success and image_success and whisper_success:
        print(f"\n{'='*60}")
        print("✓ ALL MODELS DOWNLOADED SUCCESSFULLY")
        print(f"{'='*60}")
        print("\nYou can now use the pipeline offline!")
        print("Model cache locations:")
        print(f"  - Text/Image models: ~/.cache/huggingface/")
        print(f"  - Whisper: ~/.cache/whisper/")
    else:
        print(f"\n{'='*60}")
        print("⚠ SOME DOWNLOADS FAILED")
        print(f"{'='*60}")
        print("Please check the errors above and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()

