import sqlite3
import threading
import logging
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
import hashlib
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class SecureDatabase:
    def __init__(self, db_path: str = "boqmate.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._connection_pool = {}
        self.max_connections = 10
        
        # Initialize database with secure schema
        self._init_database()
    
    def _init_database(self):
        """Initialize database with secure schema"""
        with self._get_connection() as conn:
            # Create files table with proper constraints
            conn.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id TEXT PRIMARY KEY CHECK(length(id) = 36),
                    user_id TEXT NOT NULL CHECK(length(user_id) > 0),
                    filename TEXT NOT NULL CHECK(length(filename) > 0 AND length(filename) <= 255),
                    filepath TEXT NOT NULL CHECK(length(filepath) > 0),
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    boq_data TEXT,
                    file_hash TEXT,
                    file_size INTEGER CHECK(file_size > 0 AND file_size <= 52428800),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create users table for additional security
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY CHECK(length(id) = 36),
                    email TEXT UNIQUE NOT NULL CHECK(length(email) > 0 AND email LIKE '%_@_%'),
                    password_hash TEXT NOT NULL CHECK(length(password_hash) = 96),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    failed_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP
                )
            """)
            
            # Create security logs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS security_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT NOT NULL,
                    ip_address TEXT,
                    user_id TEXT,
                    details TEXT,
                    severity TEXT DEFAULT 'INFO'
                )
            """)
            
            # Create indexes for performance and security
            conn.execute("CREATE INDEX IF NOT EXISTS idx_files_user_id ON files(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_files_uploaded_at ON files(uploaded_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_security_logs_timestamp ON security_logs(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_security_logs_ip ON security_logs(ip_address)")
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get a database connection with proper error handling"""
        thread_id = threading.get_ident()
        
        if thread_id not in self._connection_pool:
            if len(self._connection_pool) >= self.max_connections:
                # Remove oldest connection
                oldest_thread = min(self._connection_pool.keys())
                self._connection_pool[oldest_thread].close()
                del self._connection_pool[oldest_thread]
            
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON")
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode = WAL")
            # Set busy timeout
            conn.execute("PRAGMA busy_timeout = 30000")
            
            self._connection_pool[thread_id] = conn
        
        try:
            yield self._connection_pool[thread_id]
        except Exception as e:
            logger.error(f"Database error: {e}")
            raise
    
    def _sanitize_sql(self, sql: str) -> str:
        """Sanitize SQL to prevent injection"""
        # Remove any potential SQL injection patterns
        dangerous_patterns = [
            "DROP TABLE",
            "DELETE FROM",
            "INSERT INTO",
            "UPDATE SET",
            "ALTER TABLE",
            "CREATE TABLE",
            "TRUNCATE",
            "EXEC",
            "EXECUTE",
            "UNION",
            "OR 1=1",
            "OR TRUE",
            "AND 1=1",
            "AND TRUE"
        ]
        
        sql_upper = sql.upper()
        for pattern in dangerous_patterns:
            if pattern in sql_upper:
                raise ValueError(f"Dangerous SQL pattern detected: {pattern}")
        
        return sql
    
    def execute_query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a secure query"""
        with self._lock:
            sanitized_sql = self._sanitize_sql(sql)
            
            with self._get_connection() as conn:
                cursor = conn.execute(sanitized_sql, params)
                results = []
                for row in cursor.fetchall():
                    results.append(dict(row))
                return results
    
    def execute_update(self, sql: str, params: tuple = ()) -> int:
        """Execute a secure update"""
        with self._lock:
            sanitized_sql = self._sanitize_sql(sql)
            
            with self._get_connection() as conn:
                cursor = conn.execute(sanitized_sql, params)
                conn.commit()
                return cursor.rowcount
    
    def insert_file(self, file_id: str, user_id: str, filename: str, filepath: str, file_hash: str = None, file_size: int = None) -> bool:
        """Insert a file record securely"""
        try:
            sql = """
                INSERT INTO files (id, user_id, filename, filepath, file_hash, file_size)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            self.execute_update(sql, (file_id, user_id, filename, filepath, file_hash, file_size))
            return True
        except Exception as e:
            logger.error(f"Error inserting file: {e}")
            return False
    
    def update_file_boq(self, file_id: str, boq_data: str) -> bool:
        """Update BOQ data for a file"""
        try:
            sql = """
                UPDATE files 
                SET boq_data = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            self.execute_update(sql, (boq_data, file_id))
            return True
        except Exception as e:
            logger.error(f"Error updating BOQ data: {e}")
            return False
    
    def get_user_files(self, user_id: str) -> List[Dict[str, Any]]:
        """Get files for a specific user"""
        try:
            sql = """
                SELECT id, filename, uploaded_at, boq_data, file_size
                FROM files 
                WHERE user_id = ? 
                ORDER BY uploaded_at DESC
            """
            return self.execute_query(sql, (user_id,))
        except Exception as e:
            logger.error(f"Error getting user files: {e}")
            return []
    
    def get_file_by_id(self, file_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific file by ID (user-specific)"""
        try:
            sql = """
                SELECT filepath, filename, boq_data
                FROM files 
                WHERE id = ? AND user_id = ?
            """
            results = self.execute_query(sql, (file_id, user_id))
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Error getting file by ID: {e}")
            return None
    
    def log_security_event(self, event_type: str, ip_address: str = None, user_id: str = None, details: str = None, severity: str = "INFO"):
        """Log security events"""
        try:
            sql = """
                INSERT INTO security_logs (event_type, ip_address, user_id, details, severity)
                VALUES (?, ?, ?, ?, ?)
            """
            self.execute_update(sql, (event_type, ip_address, user_id, details, severity))
        except Exception as e:
            logger.error(f"Error logging security event: {e}")
    
    def cleanup_old_logs(self, days: int = 30):
        """Clean up old security logs"""
        try:
            sql = """
                DELETE FROM security_logs 
                WHERE timestamp < datetime('now', '-{} days')
            """.format(days)
            self.execute_update(sql)
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")
    
    def get_file_hash(self, file_content: bytes) -> str:
        """Generate secure hash for file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    def verify_file_integrity(self, file_id: str, expected_hash: str) -> bool:
        """Verify file integrity using hash"""
        try:
            sql = "SELECT file_hash FROM files WHERE id = ?"
            results = self.execute_query(sql, (file_id,))
            if results:
                stored_hash = results[0].get('file_hash')
                return stored_hash == expected_hash
            return False
        except Exception as e:
            logger.error(f"Error verifying file integrity: {e}")
            return False

# Global database instance
db = SecureDatabase()