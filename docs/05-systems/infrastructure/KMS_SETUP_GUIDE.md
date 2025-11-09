# AWS KMS Integration Guide

This guide explains how to enable AWS KMS encryption for Canvas tokens and other OAuth credentials in PulsePlan.

## Overview

PulsePlan supports two encryption modes:

1. **Local AES-256-GCM** (Default)
   - Uses PBKDF2 key derivation from master key
   - User-specific encryption keys
   - No external dependencies
   - Suitable for development and small deployments

2. **AWS KMS Envelope Encryption** (Production)
   - Industry-standard key management
   - Automatic key rotation support
   - Audit logging via CloudTrail
   - Compliance-ready (SOC2, HIPAA, etc.)

## Current Implementation Status

✅ **Implemented:**
- Canvas tokens now stored in `oauth_tokens` table
- Encryption service with KMS infrastructure
- Automatic detection of encryption method (KMS vs local)
- Token format versioning for migration support

🔧 **Ready to Enable:**
- Set `USE_KMS=true` in environment
- Configure AWS credentials and KMS key
- All new tokens will use KMS automatically
- Existing tokens continue to work (backward compatible)

## Quick Start - Enable KMS

### 1. AWS Setup

```bash
# Create KMS key for PulsePlan
aws kms create-key \
  --description "PulsePlan token encryption" \
  --key-usage ENCRYPT_DECRYPT \
  --origin AWS_KMS

# Create alias for easier reference
aws kms create-alias \
  --alias-name alias/pulseplan-encryption \
  --target-key-id <KEY_ID_FROM_ABOVE>

# Grant permissions to your application IAM role
aws kms create-grant \
  --key-id alias/pulseplan-encryption \
  --grantee-principal <YOUR_APP_IAM_ROLE_ARN> \
  --operations Encrypt Decrypt GenerateDataKey
```

### 2. Environment Configuration

Add to your `.env` file:

```bash
# Enable KMS encryption
USE_KMS=true

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=<your_access_key>
AWS_SECRET_ACCESS_KEY=<your_secret_key>

# KMS Key (use alias or key ID)
KMS_KEY_ID=alias/pulseplan-encryption

# Keep existing master key for legacy token support
TOKEN_ENCRYPTION_KEY=<your_base64_key>
ENCRYPTION_KEY_VERSION=1
```

### 3. Install AWS SDK

```bash
pip install boto3
```

### 4. Verify Setup

```python
# Test KMS encryption
from app.security.encryption import get_encryption_service

service = get_encryption_service()
test_token = "test-canvas-token-123"
test_user = "user-id-123"

# Encrypt with KMS
encrypted = service.encrypt_token(test_token, test_user)
print(f"Encrypted (KMS): {encrypted[:50]}...")

# Decrypt
decrypted = service.decrypt_token(encrypted, test_user)
assert decrypted == test_token
print("✅ KMS encryption working!")
```

## Data Structure in oauth_tokens

### Without KMS (Current Default)
```json
{
  "user_id": "uuid",
  "provider": "canvas",
  "access_token": "v1:abc123...",
  "metadata": {
    "base_url": "https://canvas.university.edu",
    "status": "ok",
    "encryption_method": "aes256-gcm-v1"
  }
}
```

### With KMS Enabled
```json
{
  "user_id": "uuid",
  "provider": "canvas",
  "access_token": "kms:{...encrypted_package...}",
  "metadata": {
    "base_url": "https://canvas.university.edu",
    "status": "ok",
    "encryption_method": "kms",
    "kms_key_id": "canvas_kms_<user_id>_<random>"
  }
}
```

## Migration Strategy

### Gradual Migration (Recommended)
1. Enable KMS with `USE_KMS=true`
2. New tokens automatically use KMS
3. Existing tokens continue to work (local decryption)
4. Background job can re-encrypt tokens on next use

### Immediate Migration
Run migration script to re-encrypt all tokens:

```python
# scripts/migrate_to_kms.py
from app.services.integrations.canvas_token_service import get_canvas_token_service
from app.config.database.supabase import get_supabase_client

async def migrate_all_tokens():
    """Re-encrypt all Canvas tokens with KMS"""
    supabase = get_supabase_client()
    token_service = get_canvas_token_service()

    # Get all Canvas tokens
    response = supabase.table("oauth_tokens").select("*").eq(
        "provider", "canvas"
    ).execute()

    for token_data in response.data:
        user_id = token_data["user_id"]

        # Decrypt with old method
        old_token = await token_service.retrieve_canvas_token(user_id)

        if old_token and old_token.get("api_token"):
            # Re-store with KMS (will use new encryption)
            metadata = token_data.get("metadata", {})
            await token_service.store_canvas_token(
                user_id=user_id,
                canvas_url=metadata.get("base_url", ""),
                api_token=old_token["api_token"]
            )
            print(f"✅ Migrated token for user {user_id}")
```

## Security Considerations

### KMS Encryption Context
Every KMS encryption includes context for additional security:
```python
encryption_context = {
    'user_id': user_id,
    'service': 'pulseplan',
    'data_type': 'auth_token'
}
```

This prevents tokens from being decrypted for wrong users even if ciphertext is compromised.

### Key Rotation
AWS KMS supports automatic key rotation:

```bash
# Enable automatic rotation (yearly)
aws kms enable-key-rotation \
  --key-id alias/pulseplan-encryption
```

Old tokens remain decryptable - KMS handles version tracking internally.

### IAM Permissions (Least Privilege)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:GenerateDataKey"
      ],
      "Resource": "arn:aws:kms:us-east-1:ACCOUNT:key/KEY_ID",
      "Condition": {
        "StringEquals": {
          "kms:EncryptionContext:service": "pulseplan"
        }
      }
    }
  ]
}
```

## Monitoring & Audit

### CloudTrail Logging
All KMS operations are logged in CloudTrail:
- Who encrypted/decrypted tokens
- When operations occurred
- Encryption context used
- Source IP addresses

### Application Logging
The encryption service logs all operations:
```python
logger.info(f"Canvas token stored successfully for user {user_id} using {encryption_method}")
```

### Metrics to Monitor
- KMS API call volume
- Decryption failures (potential attack)
- Token storage/retrieval latency
- KMS throttling errors

## Troubleshooting

### Error: "KMS access denied"
Check IAM permissions and encryption context match

### Error: "Invalid ciphertext"
Token may be corrupted or encrypted with different key

### Error: "KMS unavailable"
Fallback to local encryption temporarily:
```python
# In encryption.py
if kms_unavailable:
    logger.warning("KMS unavailable, using local encryption")
    return self._encrypt_locally(token, user_id)
```

## Cost Estimation

AWS KMS pricing (us-east-1, 2024):
- $1/month per key
- $0.03 per 10,000 API requests

Example: 10,000 active users, 100 token operations/user/month:
- Keys: $1/month
- API calls: 1M requests = $3/month
- **Total: ~$4/month**

## Next Steps

1. Set up AWS KMS key
2. Configure environment variables
3. Install boto3
4. Test encryption/decryption
5. Enable `USE_KMS=true`
6. Monitor CloudTrail logs
7. (Optional) Run migration script for existing tokens

## Support

For questions about KMS integration:
- Check AWS KMS documentation
- Review CloudTrail logs for errors
- Contact security team for compliance requirements
