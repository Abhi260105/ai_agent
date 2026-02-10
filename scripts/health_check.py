#!/usr/bin/env python3
"""
System health check script
Monitors system health and reports issues
"""

import sys
import os
import argparse
from pathlib import Path
import sqlite3
from datetime import datetime, timedelta
import json
import psutil

sys.path.insert(0, str(Path(__file__).parent.parent))


class HealthCheck:
    """System health checker"""
    
    def __init__(self, db_path: str, verbose: bool = False):
        self.db_path = db_path
        self.verbose = verbose
        self.checks = []
        self.warnings = []
        self.errors = []
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message"""
        if self.verbose or level != "INFO":
            prefix = {
                "INFO": "ℹ",
                "WARN": "⚠",
                "ERROR": "✗",
                "SUCCESS": "✓"
            }.get(level, "·")
            
            print(f"{prefix} {message}")
    
    def add_check(self, name: str, status: bool, message: str = ""):
        """Add a check result"""
        self.checks.append({
            "name": name,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        if not status:
            self.errors.append(f"{name}: {message}")
    
    def add_warning(self, message: str):
        """Add a warning"""
        self.warnings.append(message)
        self.log(message, "WARN")
    
    def check_database_connectivity(self) -> bool:
        """Check database connectivity"""
        self.log("Checking database connectivity...")
        
        try:
            if not os.path.exists(self.db_path):
                self.add_check(
                    "Database File",
                    False,
                    f"Database file not found: {self.db_path}"
                )
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            
            self.add_check("Database Connectivity", True)
            self.log("Database connectivity OK", "SUCCESS")
            return True
            
        except Exception as e:
            self.add_check("Database Connectivity", False, str(e))
            self.log(f"Database connectivity failed: {e}", "ERROR")
            return False
    
    def check_database_schema(self) -> bool:
        """Check database schema integrity"""
        self.log("Checking database schema...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check required tables
            required_tables = [
                'users', 'memory', 'plans', 'tasks', 
                'preferences', 'integrations'
            ]
            
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table'
            """)
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            missing = set(required_tables) - set(existing_tables)
            
            if missing:
                self.add_check(
                    "Database Schema",
                    False,
                    f"Missing tables: {', '.join(missing)}"
                )
                conn.close()
                return False
            
            self.add_check("Database Schema", True)
            self.log("Database schema OK", "SUCCESS")
            conn.close()
            return True
            
        except Exception as e:
            self.add_check("Database Schema", False, str(e))
            self.log(f"Schema check failed: {e}", "ERROR")
            return False
    
    def check_database_size(self) -> bool:
        """Check database size and health"""
        self.log("Checking database size...")
        
        try:
            size_bytes = os.path.getsize(self.db_path)
            size_mb = size_bytes / 1024 / 1024
            
            self.log(f"Database size: {size_mb:.2f} MB", "INFO")
            
            # Warn if database is large
            if size_mb > 1000:  # 1GB
                self.add_warning(f"Database size is large: {size_mb:.2f} MB")
            
            self.add_check("Database Size", True, f"{size_mb:.2f} MB")
            return True
            
        except Exception as e:
            self.add_check("Database Size", False, str(e))
            return False