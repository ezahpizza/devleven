"""Webhook security utilities for HMAC verification."""
import hmac
import hashlib
import logging

logger = logging.getLogger(__name__)


def verify_hmac_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify HMAC signature from ElevenLabs webhook.
    
    Args:
        payload: Raw request body as bytes
        signature: Signature from ElevenLabs-Signature header
        secret: Shared secret from ElevenLabs console
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    try:
        # Compute HMAC-SHA256 signature
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures (constant-time comparison)
        is_valid = hmac.compare_digest(expected_signature, signature)
        
        if not is_valid:
            logger.warning("[Webhook Security] Invalid HMAC signature")
        
        return is_valid
    
    except Exception as e:
        logger.error(f"[Webhook Security] Error verifying signature: {e}")
        return False
