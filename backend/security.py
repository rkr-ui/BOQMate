import os
import hashlib
import hmac
import time
import re
import json
from typing import Dict, Any, Optional
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from datetime import datetime, timedelta
import ipaddress
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityManager:
    def __init__(self):
        self.secret_key = os.getenv("SECURITY_SECRET_KEY", "your-super-secret-key-change-this")
        self.rate_limit_requests = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        self.rate_limit_window = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))  # 1 hour
        self.request_history = {}
        self.blocked_ips = set()
        self.suspicious_patterns = [
            r"<script.*?>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"union\s+select",
            r"drop\s+table",
            r"delete\s+from",
            r"insert\s+into",
            r"update\s+set",
            r"exec\s*\(",
            r"eval\s*\(",
            r"document\.cookie",
            r"localStorage",
            r"sessionStorage",
            r"\.\.\/",
            r"\.\.\\",
            r"\/etc\/passwd",
            r"\/proc\/",
            r"\/sys\/",
            r"\/dev\/",
            r"\.\.\/\.\.\/",
            r"union.*select",
            r"or\s+1\s*=\s*1",
            r"or\s+true",
            r"and\s+1\s*=\s*1",
            r"and\s+true",
            r"';.*--",
            r"';.*#",
            r"';.*\/\*",
            r"';.*\*\/",
            r"';.*\/\/",
            r"';.*\n",
            r"';.*\r",
            r"';.*\t",
            r"';.*\x00",
            r"';.*\x0a",
            r"';.*\x0d",
            r"';.*\x09",
            r"';.*\x20",
            r"';.*\x7f",
            r"';.*\xff",
            r"';.*\x80",
            r"';.*\x81",
            r"';.*\x82",
            r"';.*\x83",
            r"';.*\x84",
            r"';.*\x85",
            r"';.*\x86",
            r"';.*\x87",
            r"';.*\x88",
            r"';.*\x89",
            r"';.*\x8a",
            r"';.*\x8b",
            r"';.*\x8c",
            r"';.*\x8d",
            r"';.*\x8e",
            r"';.*\x8f",
            r"';.*\x90",
            r"';.*\x91",
            r"';.*\x92",
            r"';.*\x93",
            r"';.*\x94",
            r"';.*\x95",
            r"';.*\x96",
            r"';.*\x97",
            r"';.*\x98",
            r"';.*\x99",
            r"';.*\x9a",
            r"';.*\x9b",
            r"';.*\x9c",
            r"';.*\x9d",
            r"';.*\x9e",
            r"';.*\x9f",
            r"';.*\xa0",
            r"';.*\xa1",
            r"';.*\xa2",
            r"';.*\xa3",
            r"';.*\xa4",
            r"';.*\xa5",
            r"';.*\xa6",
            r"';.*\xa7",
            r"';.*\xa8",
            r"';.*\xa9",
            r"';.*\xaa",
            r"';.*\xab",
            r"';.*\xac",
            r"';.*\xad",
            r"';.*\xae",
            r"';.*\xaf",
            r"';.*\xb0",
            r"';.*\xb1",
            r"';.*\xb2",
            r"';.*\xb3",
            r"';.*\xb4",
            r"';.*\xb5",
            r"';.*\xb6",
            r"';.*\xb7",
            r"';.*\xb8",
            r"';.*\xb9",
            r"';.*\xba",
            r"';.*\xbb",
            r"';.*\xbc",
            r"';.*\xbd",
            r"';.*\xbe",
            r"';.*\xbf",
            r"';.*\xc0",
            r"';.*\xc1",
            r"';.*\xc2",
            r"';.*\xc3",
            r"';.*\xc4",
            r"';.*\xc5",
            r"';.*\xc6",
            r"';.*\xc7",
            r"';.*\xc8",
            r"';.*\xc9",
            r"';.*\xca",
            r"';.*\xcb",
            r"';.*\xcc",
            r"';.*\xcd",
            r"';.*\xce",
            r"';.*\xcf",
            r"';.*\xd0",
            r"';.*\xd1",
            r"';.*\xd2",
            r"';.*\xd3",
            r"';.*\xd4",
            r"';.*\xd5",
            r"';.*\xd6",
            r"';.*\xd7",
            r"';.*\xd8",
            r"';.*\xd9",
            r"';.*\xda",
            r"';.*\xdb",
            r"';.*\xdc",
            r"';.*\xdd",
            r"';.*\xde",
            r"';.*\xdf",
            r"';.*\xe0",
            r"';.*\xe1",
            r"';.*\xe2",
            r"';.*\xe3",
            r"';.*\xe4",
            r"';.*\xe5",
            r"';.*\xe6",
            r"';.*\xe7",
            r"';.*\xe8",
            r"';.*\xe9",
            r"';.*\xea",
            r"';.*\xeb",
            r"';.*\xec",
            r"';.*\xed",
            r"';.*\xee",
            r"';.*\xef",
            r"';.*\xf0",
            r"';.*\xf1",
            r"';.*\xf2",
            r"';.*\xf3",
            r"';.*\xf4",
            r"';.*\xf5",
            r"';.*\xf6",
            r"';.*\xf7",
            r"';.*\xf8",
            r"';.*\xf9",
            r"';.*\xfa",
            r"';.*\xfb",
            r"';.*\xfc",
            r"';.*\xfd",
            r"';.*\xfe",
            r"';.*\xff"
        ]
        
    def get_client_ip(self, request: Request) -> str:
        """Get real client IP address"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked"""
        return ip in self.blocked_ips
    
    def block_ip(self, ip: str, reason: str = "Suspicious activity"):
        """Block an IP address"""
        self.blocked_ips.add(ip)
        logger.warning(f"IP {ip} blocked: {reason}")
    
    def check_rate_limit(self, ip: str) -> bool:
        """Check rate limiting for IP"""
        current_time = time.time()
        
        if ip not in self.request_history:
            self.request_history[ip] = []
        
        # Remove old requests outside the window
        self.request_history[ip] = [
            req_time for req_time in self.request_history[ip]
            if current_time - req_time < self.rate_limit_window
        ]
        
        # Check if too many requests
        if len(self.request_history[ip]) >= self.rate_limit_requests:
            self.block_ip(ip, "Rate limit exceeded")
            return False
        
        # Add current request
        self.request_history[ip].append(current_time)
        return True
    
    def validate_input(self, data: Any) -> bool:
        """Validate input data for malicious content"""
        if isinstance(data, str):
            return self._validate_string(data)
        elif isinstance(data, dict):
            return all(self.validate_input(v) for v in data.values())
        elif isinstance(data, list):
            return all(self.validate_input(item) for item in data)
        return True
    
    def _validate_string(self, text: str) -> bool:
        """Validate string for malicious patterns"""
        text_lower = text.lower()
        
        # Check for suspicious patterns
        for pattern in self.suspicious_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return False
        
        # Check for null bytes and control characters
        if '\x00' in text or any(ord(c) < 32 and c not in '\t\n\r' for c in text):
            return False
        
        # Check for overly long strings
        if len(text) > 10000:  # 10KB limit
            return False
        
        return True
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal"""
        # Remove path traversal attempts
        filename = re.sub(r'\.\./', '', filename)
        filename = re.sub(r'\.\.\\', '', filename)
        filename = re.sub(r'[<>:"|?*]', '', filename)
        
        # Limit length
        if len(filename) > 255:
            filename = filename[:255]
        
        return filename
    
    def validate_file_type(self, filename: str, allowed_extensions: list) -> bool:
        """Validate file type"""
        if not filename:
            return False
        
        file_extension = filename.lower().split('.')[-1]
        return file_extension in allowed_extensions
    
    def generate_secure_token(self, user_id: str, expires_in: int = 3600) -> str:
        """Generate secure JWT token"""
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(seconds=expires_in),
            "iat": datetime.utcnow(),
            "iss": "BOQMate",
            "aud": "BOQMate-Users"
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
    
    def hash_password(self, password: str) -> str:
        """Hash password securely"""
        salt = os.urandom(32)
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return salt.hex() + hash_obj.hex()
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            salt = bytes.fromhex(hashed_password[:64])
            stored_hash = bytes.fromhex(hashed_password[64:])
            hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
            return hmac.compare_digest(hash_obj, stored_hash)
        except Exception:
            return False
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security events"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "details": details
        }
        logger.warning(f"SECURITY EVENT: {json.dumps(log_entry)}")

# Global security manager instance
security_manager = SecurityManager()