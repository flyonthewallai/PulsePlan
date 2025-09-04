import pytest
from app.security.encryption import encryption_service

def test_encryption_health_check():
    """Test encryption service health check"""
    assert encryption_service.health_check() == True

def test_token_encryption_decryption():
    """Test token encryption and decryption"""
    user_id = "test-user-123"
    original_token = "test-access-token-12345"
    
    # Encrypt token
    encrypted_token = encryption_service.encrypt_token(original_token, user_id)
    
    # Verify encrypted format
    assert encrypted_token != original_token
    assert encrypted_token.startswith("v1:")
    
    # Decrypt token
    decrypted_token = encryption_service.decrypt_token(encrypted_token, user_id)
    
    # Verify decryption
    assert decrypted_token == original_token

def test_encryption_with_different_users():
    """Test that different users get different encrypted values"""
    token = "same-token"
    user1 = "user-1"
    user2 = "user-2"
    
    encrypted1 = encryption_service.encrypt_token(token, user1)
    encrypted2 = encryption_service.encrypt_token(token, user2)
    
    # Same token encrypted for different users should be different
    assert encrypted1 != encrypted2
    
    # But both should decrypt correctly for their respective users
    assert encryption_service.decrypt_token(encrypted1, user1) == token
    assert encryption_service.decrypt_token(encrypted2, user2) == token

def test_encryption_empty_token():
    """Test encryption with empty token"""
    user_id = "test-user"
    
    # Empty tokens should pass through unchanged
    assert encryption_service.encrypt_token("", user_id) == ""
    assert encryption_service.decrypt_token("", user_id) == ""

def test_key_derivation():
    """Test user key derivation"""
    user_id = "test-user"
    
    # Same user should get same key
    key1 = encryption_service.derive_user_key(user_id)
    key2 = encryption_service.derive_user_key(user_id)
    assert key1 == key2
    
    # Different users should get different keys
    key3 = encryption_service.derive_user_key("different-user")
    assert key1 != key3