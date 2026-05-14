"""
File integrity checking with SHA256
"""
import os
import hashlib

HASH_EXTENSION = ".sha256"


def verify_file_integrity(file_path: str) -> bool:
    """
    Verify file integrity by comparing with .sha256 file
    Returns True if integrity check passes or hash file doesn't exist
    """
    hash_path = file_path + HASH_EXTENSION
    
    if not os.path.exists(hash_path):
        return True  # No hash file, skip verification
    
    try:
        with open(hash_path, 'r', encoding='utf-8') as hf:
            stored_hash = hf.read().strip()
        
        with open(file_path, 'rb') as f:
            raw_bytes = f.read()
        
        actual_hash = hashlib.sha256(raw_bytes).hexdigest()
        return actual_hash == stored_hash
    except Exception:
        return False


def save_file_with_hash(file_path: str, content: bytes) -> bool:
    """
    Save file and create .sha256 checksum file
    Returns True if successful
    """
    try:
        # Save main file
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Create and save hash file
        file_hash = hashlib.sha256(content).hexdigest()
        hash_path = file_path + HASH_EXTENSION
        with open(hash_path, 'w', encoding='utf-8') as hf:
            hf.write(file_hash)
        
        # Verify
        with open(file_path, 'rb') as f:
            saved_content = f.read()
        verify_hash = hashlib.sha256(saved_content).hexdigest()
        
        return verify_hash == file_hash
    except Exception:
        return False