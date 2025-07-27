#!/usr/bin/env python3
"""
BOQMate Local Development Server
Simple startup script for local development without Docker
"""

import os
import sys
import uvicorn
from pathlib import Path

def setup_environment():
    """Set up environment variables for local development"""
    env_vars = {
        "JWT_SECRET_KEY": "dev-jwt-secret-key-change-in-production",
        "ENCRYPTION_KEY": "dev-encryption-key-change-in-production",
        "SECURITY_SECRET_KEY": "dev-security-key-change-in-production",
        "OPENAI_API_KEY": "your-openai-api-key-here",
        "SUPABASE_JWT_SECRET": "your-supabase-jwt-secret-here",
        "SUPABASE_PROJECT_ID": "your-supabase-project-id-here",
        "RATE_LIMIT_REQUESTS": "100",
        "RATE_LIMIT_WINDOW": "3600",
        "MAX_FILE_SIZE": "52428800",
        "ALLOWED_ORIGINS": "http://localhost:3000",
        "LOG_SECURITY_EVENTS": "true",
        "MONITORING_ENABLED": "true",
        "API_KEY_REQUIRED": "false",
        "MAX_FAILED_ATTEMPTS": "5",
        "LOCKOUT_DURATION": "900",
        "DB_CONNECTION_LIMIT": "10",
        "DB_TIMEOUT": "30",
        "ALERT_THRESHOLD": "10",
        "MONITORING_INTERVAL": "300"
    }
    
    for key, value in env_vars.items():
        if key not in os.environ:
            os.environ[key] = value
            print(f"Set {key} to default value")

def create_directories():
    """Create necessary directories"""
    directories = ["uploads", "logs"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"Created directory: {directory}")

def main():
    """Start the local development server"""
    print("🚀 Starting BOQMate Local Development Server")
    print("=" * 50)
    
    # Set up environment
    setup_environment()
    
    # Create directories
    create_directories()
    
    print("\n⚠️  IMPORTANT: Set your API keys in the environment variables!")
    print("   - OPENAI_API_KEY: Your OpenAI API key")
    print("   - SUPABASE_JWT_SECRET: Your Supabase JWT secret")
    print("   - SUPABASE_PROJECT_ID: Your Supabase project ID")
    print("\n🔒 Security Note: Using default security keys for development only!")
    print("   Change these for production deployment.")
    
    print("\n🌐 Starting server on http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("💚 Health Check: http://localhost:8000/health")
    
    try:
        # Import and run the FastAPI app
        from main import app
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except ImportError as e:
        print(f"❌ Error importing application: {e}")
        print("Make sure all dependencies are installed:")
        print("pip install fastapi uvicorn python-multipart python-jose requests openai PyPDF2 python-docx ezdxf openpyxl cryptography bcrypt passlib")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 