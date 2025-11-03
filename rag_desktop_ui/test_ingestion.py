#!/usr/bin/env python3
"""
Test script to verify ingestion pipeline integration
"""
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
ingestion_path = os.path.join(current_dir, '..', 'ingestion_pipeline')
ingestion_path = os.path.abspath(ingestion_path)
sys.path.insert(0, ingestion_path)

try:
    from client import create_client
    print("✓ Successfully imported ingestion client")
    
    # Test client creation
    client = create_client(image_model=None, offline_mode=False)
    print("✓ Successfully created ingestion client")
    
    # Test collection info
    info = client.get_collection_info()
    print(f"✓ Collection info: {info}")
    
    print("\n Ingestion pipeline is working correctly!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()