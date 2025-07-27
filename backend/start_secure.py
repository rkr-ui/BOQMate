#!/usr/bin/env python3
"""
BOQMate Secure Startup Script
Validates security configuration and starts the application securely
"""

import os
import sys
import logging
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SecureStartup:
    def __init__(self):
        self.required_env_vars = [
            "JWT_SECRET_KEY",
            "ENCRYPTION_KEY",
            "OPENAI_API_KEY"
        ]
        
        self.recommended_env_vars = [
            "SUPABASE_JWT_SECRET",
            "SUPABASE_PROJECT_ID",
            "ALLOWED_ORIGINS",
            "RATE_LIMIT_REQUESTS",
            "MAX_FILE_SIZE"
        ]
        
        self.security_warnings = []
        self.security_errors = []
    
    def check_environment_variables(self) -> bool:
        """Check if required environment variables are set"""
        logger.info("Checking environment variables...")
        
        missing_required = []
        missing_recommended = []
        
        # Check required variables
        for var in self.required_env_vars:
            if not os.getenv(var):
                missing_required.append(var)
            elif self._is_default_value(var, os.getenv(var)):
                self.security_warnings.append(f"{var} is using default value - CHANGE THIS!")
        
        # Check recommended variables
        for var in self.recommended_env_vars:
            if not os.getenv(var):
                missing_recommended.append(var)
        
        # Report results
        if missing_required:
            self.security_errors.extend([f"Missing required environment variable: {var}" for var in missing_required])
            return False
        
        if missing_recommended:
            self.security_warnings.extend([f"Missing recommended environment variable: {var}" for var in missing_recommended])
        
        logger.info("Environment variables check completed")
        return True
    
    def _is_default_value(self, var: str, value: str) -> bool:
        """Check if environment variable is using default value"""
        default_values = {
            "JWT_SECRET_KEY": "your-super-secret-jwt-key-change-this",
            "ENCRYPTION_KEY": "your-32-byte-encryption-key-here",
            "SECURITY_SECRET_KEY": "your-super-secret-key-change-this"
        }
        return value == default_values.get(var, "")
    
    def check_file_permissions(self) -> bool:
        """Check file permissions for security"""
        logger.info("Checking file permissions...")
        
        critical_files = [
            "boqmate.db",
            "uploads/",
            ".env"
        ]
        
        for file_path in critical_files:
            path = Path(file_path)
            if path.exists():
                # Check if files are readable by others
                if path.stat().st_mode & 0o077:
                    self.security_warnings.append(f"File {file_path} has loose permissions")
        
        logger.info("File permissions check completed")
        return True
    
    def check_dependencies(self) -> bool:
        """Check if all security dependencies are installed"""
        logger.info("Checking security dependencies...")
        
        required_packages = [
            "cryptography",
            "bcrypt",
            "passlib",
            "python-jose[cryptography]"
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace("[cryptography]", ""))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            self.security_errors.extend([f"Missing security package: {pkg}" for pkg in missing_packages])
            return False
        
        logger.info("Dependencies check completed")
        return True
    
    def validate_security_config(self) -> bool:
        """Validate security configuration"""
        logger.info("Validating security configuration...")
        
        # Check rate limiting
        rate_limit = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        if rate_limit > 1000:
            self.security_warnings.append("Rate limit is very high - consider reducing")
        
        # Check file size limits
        max_file_size = int(os.getenv("MAX_FILE_SIZE", "52428800"))
        if max_file_size > 100 * 1024 * 1024:  # 100MB
            self.security_warnings.append("File size limit is very large - consider reducing")
        
        # Check CORS configuration
        allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
        if "*" in allowed_origins:
            self.security_warnings.append("CORS allows all origins - restrict for production")
        
        logger.info("Security configuration validation completed")
        return True
    
    def check_database_security(self) -> bool:
        """Check database security"""
        logger.info("Checking database security...")
        
        db_path = Path("boqmate.db")
        if db_path.exists():
            # Check if database is accessible
            try:
                import sqlite3
                conn = sqlite3.connect(str(db_path))
                conn.execute("SELECT 1")
                conn.close()
                logger.info("Database security check completed")
                return True
            except Exception as e:
                self.security_errors.append(f"Database security check failed: {e}")
                return False
        
        logger.info("Database not found - will be created on first run")
        return True
    
    def start_security_monitor(self):
        """Start security monitoring in background"""
        try:
            logger.info("Starting security monitor...")
            monitor_process = subprocess.Popen([
                sys.executable, "security_monitor.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Give it a moment to start
            time.sleep(2)
            
            if monitor_process.poll() is None:
                logger.info("Security monitor started successfully")
                return monitor_process
            else:
                logger.warning("Security monitor failed to start")
                return None
        except Exception as e:
            logger.error(f"Error starting security monitor: {e}")
            return None
    
    def start_application(self):
        """Start the main application"""
        logger.info("Starting BOQMate application...")
        
        try:
            # Start the FastAPI application
            app_process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", "main:app", 
                "--host", "0.0.0.0", "--port", "8000"
            ])
            
            logger.info("BOQMate application started successfully")
            return app_process
        except Exception as e:
            logger.error(f"Error starting application: {e}")
            return None
    
    def run_security_checks(self) -> bool:
        """Run all security checks"""
        logger.info("Running comprehensive security checks...")
        
        checks = [
            self.check_environment_variables,
            self.check_file_permissions,
            self.check_dependencies,
            self.validate_security_config,
            self.check_database_security
        ]
        
        all_passed = True
        for check in checks:
            if not check():
                all_passed = False
        
        return all_passed
    
    def print_security_report(self):
        """Print security report"""
        print("\n" + "="*60)
        print("🔒 BOQMate Security Report")
        print("="*60)
        
        if self.security_errors:
            print("\n❌ SECURITY ERRORS (MUST FIX):")
            for error in self.security_errors:
                print(f"  • {error}")
        
        if self.security_warnings:
            print("\n⚠️  SECURITY WARNINGS (RECOMMENDED TO FIX):")
            for warning in self.security_warnings:
                print(f"  • {warning}")
        
        if not self.security_errors and not self.security_warnings:
            print("\n✅ All security checks passed!")
        
        print("\n" + "="*60)
    
    def start_secure(self):
        """Start the application with security checks"""
        logger.info("Starting BOQMate with security validation...")
        
        # Run security checks
        if not self.run_security_checks():
            self.print_security_report()
            logger.error("Security checks failed. Please fix the issues above.")
            sys.exit(1)
        
        # Print security report
        self.print_security_report()
        
        # Start security monitor
        monitor_process = self.start_security_monitor()
        
        # Start main application
        app_process = self.start_application()
        
        if not app_process:
            logger.error("Failed to start application")
            if monitor_process:
                monitor_process.terminate()
            sys.exit(1)
        
        logger.info("BOQMate started successfully with security monitoring")
        
        try:
            # Wait for processes
            app_process.wait()
        except KeyboardInterrupt:
            logger.info("Shutting down BOQMate...")
            app_process.terminate()
            if monitor_process:
                monitor_process.terminate()
            logger.info("BOQMate stopped")

def main():
    """Main function"""
    startup = SecureStartup()
    startup.start_secure()

if __name__ == "__main__":
    main()