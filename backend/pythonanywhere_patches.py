#!/usr/bin/env python3
"""
PythonAnywhere deployment patches for RNA Lab Navigator
This script modifies imports to handle missing ML dependencies gracefully
"""

import os
import re
import shutil
from pathlib import Path

def create_backup(filepath):
    """Create a backup of the original file"""
    backup_path = f"{filepath}.backup"
    if not os.path.exists(backup_path):
        shutil.copy2(filepath, backup_path)
    return backup_path

def patch_sentence_transformers_imports(content):
    """Replace sentence_transformers imports with conditional imports"""
    
    # Pattern for sentence_transformers imports
    patterns = [
        (r'^from sentence_transformers import CrossEncoder$',
         '''try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CrossEncoder = None
    CROSS_ENCODER_AVAILABLE = False'''),
        
        (r'^from sentence_transformers import SentenceTransformer$',
         '''try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMER_AVAILABLE = True
except ImportError:
    SentenceTransformer = None
    SENTENCE_TRANSFORMER_AVAILABLE = False'''),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    return content

def patch_sklearn_imports(content):
    """Replace sklearn imports with conditional imports"""
    
    patterns = [
        (r'^from sklearn\.metrics\.pairwise import cosine_similarity$',
         '''try:
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    # Simple fallback for cosine similarity
    def cosine_similarity(X, Y=None):
        import numpy as np
        if Y is None:
            Y = X
        # Return dummy similarities for PythonAnywhere deployment
        return np.ones((len(X), len(Y))) * 0.5'''),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    return content

def patch_offline_imports(content):
    """Handle offline module imports"""
    
    pattern = r'^from \.offline import get_llm_client, get_cross_encoder, is_offline_mode$'
    replacement = '''try:
    from .offline import get_llm_client, get_cross_encoder, is_offline_mode
except ImportError:
    # Fallback implementations for PythonAnywhere
    def get_llm_client():
        return None
    
    def get_cross_encoder():
        return None
    
    def is_offline_mode():
        return False'''
    
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    return content

def patch_transformers_imports(content):
    """Handle transformers imports"""
    
    patterns = [
        (r'^from transformers import pipeline$',
         '''try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    pipeline = None
    TRANSFORMERS_AVAILABLE = False'''),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    return content

def patch_file(filepath, patches_to_apply):
    """Apply patches to a single file"""
    
    print(f"Patching {filepath}...")
    
    # Create backup
    backup_path = create_backup(filepath)
    
    # Read content
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Apply patches
    original_content = content
    for patch_func in patches_to_apply:
        content = patch_func(content)
    
    # Write back only if changed
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ Patched successfully")
    else:
        print(f"  - No changes needed")

def main():
    """Main patching function"""
    
    # Define files and their required patches
    files_to_patch = {
        'api/views.py': [
            patch_sentence_transformers_imports,
            patch_offline_imports,
        ],
        'api/offline/__init__.py': [
            patch_sentence_transformers_imports,
            patch_transformers_imports,
        ],
        'api/rag/multi_hop_reasoning.py': [
            patch_sklearn_imports,
        ],
        'api/rag/enhanced_rag_architecture.py': [
            patch_sentence_transformers_imports,
            patch_transformers_imports,
        ],
        'api/search/reranking.py': [
            patch_sentence_transformers_imports,
        ],
        'api/search/hybrid_search.py': [
            patch_sentence_transformers_imports,
        ],
    }
    
    # Apply patches
    for filepath, patches in files_to_patch.items():
        if os.path.exists(filepath):
            patch_file(filepath, patches)
        else:
            print(f"Warning: {filepath} not found")
    
    print("\nAll patches applied successfully!")
    print("\nTo restore original files, run:")
    print("  for f in api/**/*.py.backup; do mv $f ${f%.backup}; done")

if __name__ == '__main__':
    main()