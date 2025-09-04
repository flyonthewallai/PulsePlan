import os
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from app.config.settings import settings
from typing import Optional, Union
import logging
import base64

logger = logging.getLogger(__name__)

class EncryptionService:
    """
    Enhanced encryption service supporting both AES-256-GCM (matching Node.js) and KMS
    Phase 1: Local AES-256-GCM encryption
    Phase 2+: AWS KMS integration
    """
    
    def __init__(self):
        self.master_key = settings.TOKEN_ENCRYPTION_KEY.encode()
        self.key_version = settings.ENCRYPTION_KEY_VERSION
        self.use_kms = settings.USE_KMS
        
        if not self.master_key:
            raise ValueError("TOKEN_ENCRYPTION_KEY must be configured")
        
        if self.use_kms:
            self._init_kms()
        else:
            logger.info("Local AES-256-GCM encryption service initialized")
    
    def _init_kms(self):
        """Initialize KMS client (Phase 2+ implementation)"""
        try:
            if not all([settings.AWS_REGION, settings.KMS_KEY_ID]):
                raise ValueError("KMS configuration incomplete")
            
            # TODO: Initialize boto3 KMS client in Phase 2
            logger.info("KMS encryption service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize KMS: {e}")
            raise
    
    def derive_user_key(self, user_id: str, version: Optional[int] = None) -> bytes:
        """
        Derive user-specific encryption key using PBKDF2 (matching Node.js pattern)
        """
        version = version or self.key_version
        salt = f"pulseplan:user:{user_id}:v{version}".encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 32 bytes for AES-256
            salt=salt,
            iterations=100000,  # OWASP recommended
            backend=default_backend()
        )
        
        return kdf.derive(self.master_key)
    
    def encrypt_token(self, token: str, user_id: str) -> str:
        """
        Encrypt token with user-specific key
        Returns format: "v{version}:{encrypted_data}" or "kms:{encrypted_data}"
        """
        if not token:
            return token
        
        if self.use_kms:
            return self._encrypt_with_kms(token, user_id)
        else:
            return self._encrypt_locally(token, user_id)
    
    def decrypt_token(self, encrypted_token: str, user_id: str) -> str:
        """
        Decrypt token with appropriate method based on prefix
        """
        if not encrypted_token:
            return encrypted_token
        
        if encrypted_token.startswith("kms:"):
            return self._decrypt_with_kms(encrypted_token, user_id)
        elif encrypted_token.startswith("v"):
            return self._decrypt_locally(encrypted_token, user_id)
        else:
            # Legacy format - try local decryption
            return self._decrypt_locally(encrypted_token, user_id)
    
    def _encrypt_locally(self, token: str, user_id: str) -> str:
        """
        Encrypt using AES-256-GCM (matching Node.js pattern exactly)
        Format: "v{version}:{iv_hex}:{auth_tag_hex}:{encrypted_hex}"
        """
        try:
            # Derive user-specific key
            user_key = self.derive_user_key(user_id)
            
            # Generate random IV (16 bytes for GCM)
            iv = os.urandom(16)
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(user_key),
                modes.GCM(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # Encrypt the token
            encrypted_data = encryptor.update(token.encode('utf-8')) + encryptor.finalize()
            
            # Get authentication tag
            auth_tag = encryptor.tag
            
            # Format: v{version}:{iv}:{auth_tag}:{encrypted} (matching Node.js)
            result = f"v{self.key_version}:{iv.hex()}:{auth_tag.hex()}:{encrypted_data.hex()}"
            
            return result
            
        except Exception as e:
            logger.error(f"Local encryption failed: {e}")
            raise ValueError(f"Encryption failed: {e}")
    
    def _decrypt_locally(self, encrypted_token: str, user_id: str) -> str:
        """
        Decrypt using AES-256-GCM (matching Node.js pattern exactly)
        """
        try:
            # Parse the encrypted token format
            if ':' not in encrypted_token:
                raise ValueError("Invalid encrypted token format")
            
            parts = encrypted_token.split(':')
            
            if len(parts) == 4 and parts[0].startswith('v'):
                # New format: v{version}:{iv}:{auth_tag}:{encrypted}
                version_str, iv_hex, auth_tag_hex, encrypted_hex = parts
                version = int(version_str[1:])  # Remove 'v' prefix
            elif len(parts) == 3:
                # Legacy format: {iv}:{auth_tag}:{encrypted}
                iv_hex, auth_tag_hex, encrypted_hex = parts
                version = 1  # Default version
            else:
                raise ValueError("Invalid encrypted token format")
            
            # Convert hex to bytes
            iv = bytes.fromhex(iv_hex)
            auth_tag = bytes.fromhex(auth_tag_hex)
            encrypted_data = bytes.fromhex(encrypted_hex)
            
            # Derive key for the specific version
            user_key = self.derive_user_key(user_id, version)
            
            # Create cipher with authentication tag
            cipher = Cipher(
                algorithms.AES(user_key),
                modes.GCM(iv, auth_tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # Decrypt and verify
            decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
            
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Local decryption failed: {e}")
            raise ValueError("Token decryption failed")
    
    def _encrypt_with_kms(self, token: str, user_id: str) -> str:
        """
        Encrypt using AWS KMS (Phase 2+ implementation)
        """
        if not self.use_kms:
            raise ValueError("KMS encryption not enabled")
        
        # TODO: Implement KMS encryption in Phase 2
        # This will use boto3 KMS client to encrypt with customer-managed key
        raise NotImplementedError(
            "KMS encryption will be implemented in Phase 2. "
            "Set USE_KMS=false for Phase 1."
        )
    
    def _decrypt_with_kms(self, encrypted_token: str, user_id: str) -> str:
        """
        Decrypt using AWS KMS (Phase 2+ implementation)
        """
        if not self.use_kms:
            raise ValueError("KMS decryption not enabled")
        
        # TODO: Implement KMS decryption in Phase 2
        raise NotImplementedError(
            "KMS decryption will be implemented in Phase 2. "
            "Existing KMS tokens need migration."
        )
    
    def rotate_key_version(self, new_version: int):
        """Update key version for key rotation"""
        self.key_version = new_version
        logger.info(f"Encryption key version updated to v{new_version}")
    
    def health_check(self) -> bool:
        """Test encryption/decryption functionality"""
        try:
            test_user = "health-check-user"
            test_token = "test-token-123-health-check"
            
            # Test encryption/decryption cycle
            encrypted = self.encrypt_token(test_token, test_user)
            decrypted = self.decrypt_token(encrypted, test_user)
            
            return decrypted == test_token
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

# Global encryption service instance
encryption_service = EncryptionService()