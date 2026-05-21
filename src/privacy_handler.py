"""
Privacy handler module - handles image deletion and hashing.
This module is separate from the privacy/ package to avoid naming conflicts.
"""
import os
import hashlib
from loguru import logger

def process_privacy(image_path: str) -> str:
    """
    Process image for privacy compliance:
    1. Generate SHA256 hash of file content
    2. Delete the original file
    3. Return the hash for logging
    
    Args:
        image_path: Path to the uploaded image file
        
    Returns:
        str: SHA256 hash of the file content
    """
    try:
        # Generate hash before deletion
        with open(image_path, 'rb') as f:
            image_hash = hashlib.sha256(f.read()).hexdigest()
        
        # Delete the original file (privacy-by-design)
        if os.path.exists(image_path):
            os.remove(image_path)
            logger.debug(f"File deleted: {image_path}")
        
        return image_hash
        
    except Exception as e:
        logger.error(f"Privacy processing failed for {image_path}: {e}")
        # Ensure file is deleted even on error
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except:
                pass
        raise RuntimeError(f"Privacy processing failed: {str(e)}")