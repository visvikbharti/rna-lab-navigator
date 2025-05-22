"""
Simplified PII detection and redaction system for RNA Lab Navigator demo.
This is a mock version for demonstration purposes.
"""

import re
import os
import logging
from typing import Dict, List, Tuple, Set, Optional, Any

# Configure logging
logger = logging.getLogger(__name__)

# Set global flag for spaCy availability
SPACY_AVAILABLE = False
nlp = None

# Define PII patterns for regex-based detection
PII_PATTERNS = {
    # Email addresses
    "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    
    # Phone numbers (various formats)
    "PHONE": r'(\+\d{1,3}\s?)?(\()?\d{3}(\))?[\s.-]?\d{3}[\s.-]?\d{4}',
    
    # IP Addresses
    "IP_ADDRESS": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
}

class PIIDetector:
    """
    Simplified class for detecting and redacting PII from text.
    """
    
    def __init__(self, strict_mode: bool = True, redact_names: bool = True):
        """
        Initialize the PII detector.
        
        Args:
            strict_mode: Whether to use stricter detection rules
            redact_names: Whether to redact detected person names
        """
        self.strict_mode = strict_mode
        self.redact_names = redact_names
        self.nlp = nlp
    
    def detect_pii(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect PII in text using regex patterns.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of PII entities with text, position, and type
        """
        pii_entities = []
        
        # Add regex-based detections
        for entity_type, pattern in PII_PATTERNS.items():
            for match in re.finditer(pattern, text):
                pii_entities.append({
                    "text": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                    "type": entity_type,
                    "method": "regex"
                })
        
        return pii_entities
    
    def redact_pii(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Detect and redact PII from text.
        
        Args:
            text: Text to redact
            
        Returns:
            Tuple of (redacted_text, list_of_redactions)
        """
        entities = self.detect_pii(text)
        redacted_text = text
        
        # Sort entities by start position in reverse order (to preserve indices)
        sorted_entities = sorted(entities, key=lambda x: x["start"], reverse=True)
        
        for entity in sorted_entities:
            redaction_label = f"[{entity['type']}]"
            redacted_text = (
                redacted_text[:entity["start"]] + 
                redaction_label + 
                redacted_text[entity["end"]:]
            )
            
        return redacted_text, entities
    
    def redact_document(self, doc_text: str, metadata: Dict[str, Any] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Redact a document, including text and metadata.
        
        Args:
            doc_text: Document text to redact
            metadata: Document metadata to redact
            
        Returns:
            Tuple of (redacted_text, redacted_metadata)
        """
        # Redact document text
        redacted_text, entities = self.redact_pii(doc_text)
        
        # Redact metadata if provided
        redacted_metadata = {}
        if metadata:
            for key, value in metadata.items():
                if isinstance(value, str):
                    redacted_value, _ = self.redact_pii(value)
                    redacted_metadata[key] = redacted_value
                else:
                    redacted_metadata[key] = value
        
        return redacted_text, redacted_metadata
    
    def scan_document(self, doc_text: str) -> Dict[str, Any]:
        """
        Scan a document for PII without redacting.
        
        Args:
            doc_text: Document text to scan
            
        Returns:
            Dictionary with scan results
        """
        entities = self.detect_pii(doc_text)
        
        # Count entities by type
        entity_counts = {}
        for entity in entities:
            entity_type = entity["type"]
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
            
        # Determine risk level
        risk_level = "low"
        if len(entities) > 10:
            risk_level = "high"
        elif len(entities) > 0:
            risk_level = "medium"
            
        return {
            "has_pii": len(entities) > 0,
            "pii_count": len(entities),
            "pii_types": entity_counts,
            "risk_level": risk_level,
            "entities": entities
        }


# Singleton instance for easy access
_default_detector = None

def get_detector(strict_mode: bool = True, redact_names: bool = True) -> PIIDetector:
    """Get the default PII detector instance"""
    global _default_detector
    if _default_detector is None:
        _default_detector = PIIDetector(strict_mode, redact_names)
    return _default_detector