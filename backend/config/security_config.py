import os
from typing import List, Dict, Any

class SecurityConfig:
    def __init__(self):
        # JWT Configuration
        self.jwt_secret = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-this")
        self.jwt_algorithm = "HS256"
        self.jwt_expiration = int(os.getenv("JWT_EXPIRATION", "3600"))  # 1 hour
        
        # Rate Limiting
        self.rate_limit_requests = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        self.rate_limit_window = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))  # 1 hour
        
        # File Upload Security
        self.max_file_size = int(os.getenv("MAX_FILE_SIZE", "52428800"))  # 50MB
        self.allowed_file_types = [
            'pdf', 'txt', 'docx', 'dwg', 'dxf', 'rvt', 'rfa', 'dgn', 'skp'
        ]
        
        # Database Security
        self.db_connection_limit = int(os.getenv("DB_CONNECTION_LIMIT", "10"))
        self.db_timeout = int(os.getenv("DB_TIMEOUT", "30"))
        
        # CORS Configuration
        self.allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
        self.allowed_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allowed_headers = ["*"]
        
        # Security Headers
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https:;",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
        
        # IP Blocking
        self.blocked_ips = set()
        self.suspicious_ips = set()
        
        # Logging Configuration
        self.log_security_events = os.getenv("LOG_SECURITY_EVENTS", "true").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # API Security
        self.api_key_required = os.getenv("API_KEY_REQUIRED", "false").lower() == "true"
        self.api_keys = os.getenv("API_KEYS", "").split(",") if os.getenv("API_KEYS") else []
        
        # Session Security
        self.session_timeout = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour
        self.max_failed_attempts = int(os.getenv("MAX_FAILED_ATTEMPTS", "5"))
        self.lockout_duration = int(os.getenv("LOCKOUT_DURATION", "900"))  # 15 minutes
        
        # Encryption
        self.encryption_key = os.getenv("ENCRYPTION_KEY", "your-32-byte-encryption-key-here")
        
        # Backup and Recovery
        self.backup_enabled = os.getenv("BACKUP_ENABLED", "true").lower() == "true"
        self.backup_interval = int(os.getenv("BACKUP_INTERVAL", "86400"))  # 24 hours
        
        # Monitoring
        self.monitoring_enabled = os.getenv("MONITORING_ENABLED", "true").lower() == "true"
        self.alert_threshold = int(os.getenv("ALERT_THRESHOLD", "10"))
        
    def validate_config(self) -> List[str]:
        """Validate security configuration and return warnings"""
        warnings = []
        
        # Check for default values that should be changed
        if self.jwt_secret == "your-super-secret-jwt-key-change-this":
            warnings.append("JWT_SECRET_KEY should be changed from default value")
        
        if self.encryption_key == "your-32-byte-encryption-key-here":
            warnings.append("ENCRYPTION_KEY should be changed from default value")
        
        # Check for weak configurations
        if self.rate_limit_requests > 1000:
            warnings.append("RATE_LIMIT_REQUESTS is very high, consider reducing")
        
        if self.max_file_size > 100 * 1024 * 1024:  # 100MB
            warnings.append("MAX_FILE_SIZE is very large, consider reducing")
        
        return warnings
    
    def get_environment_variables(self) -> Dict[str, str]:
        """Get all required environment variables"""
        return {
            "JWT_SECRET_KEY": "Your JWT secret key (32+ characters)",
            "ENCRYPTION_KEY": "Your encryption key (32 bytes)",
            "OPENAI_API_KEY": "Your OpenAI API key",
            "SUPABASE_JWT_SECRET": "Your Supabase JWT secret",
            "SUPABASE_PROJECT_ID": "Your Supabase project ID",
            "RATE_LIMIT_REQUESTS": "Maximum requests per hour (default: 100)",
            "RATE_LIMIT_WINDOW": "Rate limit window in seconds (default: 3600)",
            "MAX_FILE_SIZE": "Maximum file size in bytes (default: 52428800)",
            "ALLOWED_ORIGINS": "Comma-separated list of allowed origins",
            "LOG_LEVEL": "Logging level (default: INFO)",
            "API_KEY_REQUIRED": "Require API key for all requests (default: false)",
            "API_KEYS": "Comma-separated list of valid API keys",
            "MAX_FAILED_ATTEMPTS": "Maximum failed login attempts (default: 5)",
            "LOCKOUT_DURATION": "Account lockout duration in seconds (default: 900)",
            "BACKUP_ENABLED": "Enable automatic backups (default: true)",
            "MONITORING_ENABLED": "Enable security monitoring (default: true)"
        }
    
    def get_security_checklist(self) -> Dict[str, List[str]]:
        """Get security checklist for deployment"""
        return {
            "Environment Variables": [
                "Change JWT_SECRET_KEY from default",
                "Change ENCRYPTION_KEY from default",
                "Set OPENAI_API_KEY",
                "Set SUPABASE_JWT_SECRET",
                "Set SUPABASE_PROJECT_ID",
                "Configure ALLOWED_ORIGINS for production"
            ],
            "Server Security": [
                "Use HTTPS in production",
                "Configure firewall rules",
                "Set up SSL/TLS certificates",
                "Enable server-side logging",
                "Configure backup strategy"
            ],
            "Application Security": [
                "Enable rate limiting",
                "Configure file upload restrictions",
                "Set up monitoring and alerting",
                "Enable security event logging",
                "Configure CORS properly"
            ],
            "Database Security": [
                "Use secure database connections",
                "Enable database logging",
                "Set up database backups",
                "Configure connection pooling",
                "Enable SQL injection protection"
            ],
            "Monitoring": [
                "Set up security monitoring",
                "Configure alert thresholds",
                "Enable audit logging",
                "Set up intrusion detection",
                "Monitor for suspicious activity"
            ]
        }

# Global security config instance
security_config = SecurityConfig()