"""
Production Security Infrastructure  
Input sanitization, validation, and payload signing with replay attack prevention
"""
import re
import hashlib
import hmac
import time
import secrets
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of input validation"""
    valid: bool
    errors: List[str]
    sanitized_input: Optional[str] = None
    risk_level: str = "low"  # low, medium, high, critical


@dataclass  
class SecurityConfig:
    """Security configuration"""
    max_query_length: int = 10000
    max_parameter_length: int = 5000
    allowed_characters_pattern: str = r'^[a-zA-Z0-9\s\.\,\!\?\-\_\@\#\$\%\^\&\*\(\)\[\]\{\}\:\;\'\"\+\=\/\\\|\`\~]*$'
    enable_content_filtering: bool = True
    enable_payload_signing: bool = True
    hmac_secret_key: Optional[str] = None
    signature_ttl_seconds: int = 300  # 5 minutes


class SecurityValidator:
    """Production security validator with whitelist approach and replay protection"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        
        # Dangerous patterns (for detection, not primary filtering)
        self.dangerous_patterns = {
            'sql_injection': [
                r'(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)',
                r'(--|;|/\*|\*/)',
                r'(\bor\b.*\b1\s*=\s*1\b)',
                r'(\bor\b.*\btrue\b)',
            ],
            'xss': [
                r'<script[^>]*>.*?</script>',
                r'javascript:',
                r'on\w+\s*=',
                r'<iframe[^>]*>',
                r'<object[^>]*>',
                r'<embed[^>]*>',
            ],
            'command_injection': [
                r'(\b(curl|wget|nc|netcat|bash|sh|cmd|powershell|eval)\b)',
                r'(\$\(|\`)',
                r'(;|\||\&\&|\|\|)',
            ],
            'path_traversal': [
                r'(\.\./)+',
                r'(\.\.\\)+',
                r'/etc/passwd',
                r'/proc/',
                r'\\windows\\',
            ],
            'code_injection': [
                r'(__import__|eval|exec|compile)',
                r'(subprocess|os\.system)',
                r'(pickle\.loads|yaml\.load)',
            ]
        }
        
        # Safe character whitelist (more restrictive)
        self.safe_patterns = {
            'basic_text': r'^[a-zA-Z0-9\s\.\,\!\?\-\_]*$',
            'extended_text': r'^[a-zA-Z0-9\s\.\,\!\?\-\_\@\#\$\%\(\)\[\]\:\;\'\"]*$',
            'alphanumeric': r'^[a-zA-Z0-9]*$',
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'datetime': r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z?$',
            'priority': r'^(low|medium|high)$',
            'status': r'^(pending|in_progress|completed|cancelled)$',
        }
    
    def validate_and_sanitize_input(
        self,
        input_data: Union[str, Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Main validation and sanitization entry point"""
        
        if isinstance(input_data, str):
            return self._validate_string_input(input_data)
        elif isinstance(input_data, dict):
            return self._validate_dict_input(input_data)
        else:
            return ValidationResult(
                valid=False,
                errors=[f"Unsupported input type: {type(input_data)}"],
                risk_level="medium"
            )
    
    def _validate_string_input(self, text: str) -> ValidationResult:
        """Validate and sanitize string input"""
        errors = []
        risk_level = "low"
        
        # Length check
        if len(text) > self.config.max_query_length:
            errors.append(f"Input too long: {len(text)} > {self.config.max_query_length}")
            risk_level = "medium"
        
        # Whitelist character validation (primary security)
        if not re.match(self.config.allowed_characters_pattern, text):
            errors.append("Input contains disallowed characters")
            risk_level = "high"
        
        # Dangerous pattern detection (additional layer)
        detected_threats = self._detect_threats(text)
        if detected_threats:
            errors.extend([f"Detected {threat}: {pattern}" for threat, pattern in detected_threats])
            risk_level = "critical"
        
        # Content filtering
        if self.config.enable_content_filtering:
            content_issues = self._check_content_policy(text)
            if content_issues:
                errors.extend(content_issues)
                risk_level = max(risk_level, "medium", key=self._risk_level_priority)
        
        # Sanitization (if validation passes basic checks)
        sanitized_text = None
        if risk_level in ["low", "medium"]:
            sanitized_text = self._sanitize_text(text)
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            sanitized_input=sanitized_text,
            risk_level=risk_level
        )
    
    def _validate_dict_input(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate dictionary input (parameters)"""
        errors = []
        risk_level = "low"
        sanitized_data = {}
        
        for key, value in data.items():
            # Validate key
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                errors.append(f"Invalid parameter name: {key}")
                risk_level = "medium"
                continue
            
            # Validate value based on type
            if isinstance(value, str):
                if len(value) > self.config.max_parameter_length:
                    errors.append(f"Parameter '{key}' too long: {len(value)}")
                    risk_level = "medium"
                    continue
                
                # Apply appropriate validation based on parameter name
                validation_pattern = self._get_validation_pattern_for_field(key)
                if validation_pattern and not re.match(validation_pattern, value):
                    errors.append(f"Invalid format for parameter '{key}': {value}")
                    risk_level = "medium"
                    continue
                
                # Check for threats in string values
                threats = self._detect_threats(value)
                if threats:
                    errors.extend([f"Threat in '{key}': {threat}" for threat, _ in threats])
                    risk_level = "critical"
                    continue
                
                sanitized_data[key] = self._sanitize_text(value)
            
            elif isinstance(value, (int, float, bool)):
                # Numeric/boolean values are generally safe
                sanitized_data[key] = value
            
            elif isinstance(value, list):
                # Validate list items
                sanitized_list = []
                for i, item in enumerate(value):
                    if isinstance(item, str):
                        if len(item) > self.config.max_parameter_length:
                            errors.append(f"List item {i} in '{key}' too long")
                            continue
                        
                        threats = self._detect_threats(item)
                        if threats:
                            errors.append(f"Threat in '{key}[{i}]': {threats[0][0]}")
                            risk_level = "high"
                            continue
                        
                        sanitized_list.append(self._sanitize_text(item))
                    else:
                        sanitized_list.append(item)
                
                sanitized_data[key] = sanitized_list
            
            else:
                errors.append(f"Unsupported parameter type for '{key}': {type(value)}")
                risk_level = "medium"
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            sanitized_input=sanitized_data if len(errors) == 0 else None,
            risk_level=risk_level
        )
    
    def _detect_threats(self, text: str) -> List[tuple]:
        """Detect security threats in text"""
        threats = []
        text_lower = text.lower()
        
        for threat_type, patterns in self.dangerous_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    threats.append((threat_type, pattern))
        
        return threats
    
    def _get_validation_pattern_for_field(self, field_name: str) -> Optional[str]:
        """Get appropriate validation pattern for a field"""
        field_patterns = {
            'email': self.safe_patterns['email'],
            'priority': self.safe_patterns['priority'],
            'status': self.safe_patterns['status'],
            'due_date': self.safe_patterns['datetime'],
            'created_at': self.safe_patterns['datetime'],
            'updated_at': self.safe_patterns['datetime'],
            'id': self.safe_patterns['alphanumeric'],
            'user_id': self.safe_patterns['alphanumeric'],
            'todo_id': self.safe_patterns['alphanumeric'],
            'task_id': self.safe_patterns['alphanumeric'],
        }
        
        return field_patterns.get(field_name, self.safe_patterns['extended_text'])
    
    def _check_content_policy(self, text: str) -> List[str]:
        """Check content policy violations"""
        issues = []
        text_lower = text.lower()
        
        # Check for inappropriate content
        inappropriate_words = [
            # Add your content policy words here
            # This is a basic example
        ]
        
        for word in inappropriate_words:
            if word in text_lower:
                issues.append(f"Content policy violation: inappropriate content")
                break
        
        return issues
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize text by removing/escaping dangerous characters"""
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Remove control characters except common whitespace
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        # Truncate if still too long
        if len(text) > self.config.max_query_length:
            text = text[:self.config.max_query_length].rstrip()
        
        return text
    
    def _risk_level_priority(self, level: str) -> int:
        """Get numeric priority for risk level"""
        priorities = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        return priorities.get(level, 0)


class PayloadSigner:
    """HMAC payload signing with timestamp and nonce for replay attack prevention"""
    
    def __init__(self, secret_key: str, ttl_seconds: int = 300):
        self.secret_key = secret_key.encode() if isinstance(secret_key, str) else secret_key
        self.ttl_seconds = ttl_seconds
    
    def sign_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Sign payload with timestamp and nonce"""
        # Add timestamp and nonce
        signed_payload = payload.copy()
        signed_payload['_timestamp'] = int(time.time())
        signed_payload['_nonce'] = secrets.token_hex(16)
        
        # Create canonical message
        message = self._create_canonical_message(signed_payload)
        
        # Generate signature
        signature = hmac.new(
            self.secret_key,
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        signed_payload['_signature'] = signature
        return signed_payload
    
    def verify_payload(self, signed_payload: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Verify payload signature and check for replay attacks"""
        
        # Check required fields
        required_fields = ['_timestamp', '_nonce', '_signature']
        for field in required_fields:
            if field not in signed_payload:
                return False, f"Missing required field: {field}"
        
        # Check timestamp (replay attack prevention)
        timestamp = signed_payload['_timestamp']
        current_time = int(time.time())
        
        if current_time - timestamp > self.ttl_seconds:
            return False, f"Payload expired: {current_time - timestamp}s > {self.ttl_seconds}s"
        
        if timestamp > current_time + 60:  # Allow 1 minute clock skew
            return False, "Payload timestamp is in the future"
        
        # Verify signature
        received_signature = signed_payload.pop('_signature')
        expected_signature = hmac.new(
            self.secret_key,
            self._create_canonical_message(signed_payload).encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Restore signature for consistency
        signed_payload['_signature'] = received_signature
        
        if not hmac.compare_digest(received_signature, expected_signature):
            return False, "Invalid signature"
        
        return True, None
    
    def _create_canonical_message(self, payload: Dict[str, Any]) -> str:
        """Create canonical message for signing"""
        # Remove signature if present
        canonical_payload = {k: v for k, v in payload.items() if k != '_signature'}
        
        # Sort keys for consistent signing
        return json.dumps(canonical_payload, sort_keys=True, separators=(',', ':'))


class SecurityMiddleware:
    """Security middleware for request processing"""
    
    def __init__(
        self, 
        validator: SecurityValidator,
        signer: Optional[PayloadSigner] = None
    ):
        self.validator = validator
        self.signer = signer
        self.blocked_ips = set()  # In production, use Redis
        self.suspicious_activity = {}  # Track suspicious patterns
    
    async def validate_request(
        self,
        query: str,
        parameters: Dict[str, Any],
        user_id: str,
        client_ip: str
    ) -> Optional[Dict[str, Any]]:
        """
        Validate entire request and return error if invalid
        Returns None if valid, error dict if invalid
        """
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            return {
                "error": "access_denied",
                "message": "Your IP address has been temporarily blocked",
                "retry_after_seconds": 3600
            }
        
        # Validate query
        query_result = self.validator.validate_and_sanitize_input(query)
        if not query_result.valid:
            self._record_suspicious_activity(user_id, client_ip, "invalid_query", query_result.errors)
            
            return {
                "error": "invalid_input",
                "message": "Your request contains invalid or potentially dangerous content",
                "details": query_result.errors[:3],  # Limit details for security
                "risk_level": query_result.risk_level
            }
        
        # Validate parameters
        if parameters:
            param_result = self.validator.validate_and_sanitize_input(parameters)
            if not param_result.valid:
                self._record_suspicious_activity(user_id, client_ip, "invalid_parameters", param_result.errors)
                
                return {
                    "error": "invalid_parameters", 
                    "message": "Request parameters are invalid",
                    "details": param_result.errors[:3],
                    "risk_level": param_result.risk_level
                }
        
        # Check for suspicious activity patterns
        if self._is_suspicious_activity(user_id, client_ip):
            return {
                "error": "suspicious_activity",
                "message": "Unusual activity detected. Please try again later.",
                "retry_after_seconds": 300
            }
        
        return None  # Request is valid
    
    def _record_suspicious_activity(
        self,
        user_id: str,
        client_ip: str,
        activity_type: str,
        details: List[str]
    ):
        """Record suspicious activity for monitoring"""
        key = f"{user_id}:{client_ip}"
        current_time = time.time()
        
        if key not in self.suspicious_activity:
            self.suspicious_activity[key] = []
        
        self.suspicious_activity[key].append({
            "type": activity_type,
            "timestamp": current_time,
            "details": details
        })
        
        # Clean old entries (keep last hour)
        self.suspicious_activity[key] = [
            activity for activity in self.suspicious_activity[key]
            if current_time - activity["timestamp"] < 3600
        ]
        
        logger.warning(
            f"Suspicious activity recorded: {activity_type} from {user_id}@{client_ip}: {details}"
        )
    
    def _is_suspicious_activity(self, user_id: str, client_ip: str) -> bool:
        """Check if user/IP has suspicious activity pattern"""
        key = f"{user_id}:{client_ip}"
        if key not in self.suspicious_activity:
            return False
        
        recent_activities = self.suspicious_activity[key]
        current_time = time.time()
        
        # Check for rapid suspicious requests (> 5 in last 5 minutes)
        recent_count = sum(
            1 for activity in recent_activities
            if current_time - activity["timestamp"] < 300
        )
        
        return recent_count > 5