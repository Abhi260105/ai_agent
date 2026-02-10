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
    
    def check_memory_usage(self) -> bool:
        """Check system memory usage"""
        self.log("Checking memory usage...")
        
        try:
            memory = psutil.virtual_memory()
            
            self.log(f"Memory usage: {memory.percent}%", "INFO")
            
            if memory.percent > 90:
                self.add_warning(f"High memory usage: {memory.percent}%")
            
            self.add_check(
                "Memory Usage",
                memory.percent < 95,
                f"{memory.percent}%"
            )
            return True
            
        except Exception as e:
            self.add_check("Memory Usage", False, str(e))
            return False
    
    def check_disk_space(self) -> bool:
        """Check disk space"""
        self.log("Checking disk space...")
        
        try:
            db_dir = os.path.dirname(os.path.abspath(self.db_path))
            disk = psutil.disk_usage(db_dir)
            
            self.log(f"Disk usage: {disk.percent}%", "INFO")
            
            if disk.percent > 90:
                self.add_warning(f"Low disk space: {disk.percent}% used")
            
            self.add_check(
                "Disk Space",
                disk.percent < 95,
                f"{disk.percent}% used"
            )
            return True
            
        except Exception as e:
            self.add_check("Disk Space", False, str(e))
            return False
    
    def check_data_freshness(self) -> bool:
        """Check if data is recent"""
        self.log("Checking data freshness...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT MAX(created_at) FROM memory
            """)
            
            latest = cursor.fetchone()[0]
            conn.close()
            
            if latest:
                latest_dt = datetime.fromisoformat(latest)
                age_days = (datetime.now() - latest_dt).days
                
                self.log(f"Latest memory: {age_days} days old", "INFO")
                
                if age_days > 30:
                    self.add_warning(f"No recent data (last: {age_days} days ago)")
                
                self.add_check(
                    "Data Freshness",
                    True,
                    f"Latest: {age_days} days ago"
                )
            else:
                self.add_check("Data Freshness", True, "No data")
            
            return True
            
        except Exception as e:
            self.add_check("Data Freshness", False, str(e))
            return False
    
    def check_backup_status(self) -> bool:
        """Check backup file status"""
        self.log("Checking backup status...")
        
        try:
            backup_dir = os.path.dirname(self.db_path)
            backup_files = [
                f for f in os.listdir(backup_dir)
                if f.startswith(os.path.basename(self.db_path)) and 'backup' in f
            ]
            
            if backup_files:
                latest_backup = max(backup_files)
                self.log(f"Latest backup: {latest_backup}", "INFO")
                self.add_check("Backup Status", True, f"Found {len(backup_files)} backups")
            else:
                self.add_warning("No backup files found")
                self.add_check("Backup Status", True, "No backups")
            
            return True
            
        except Exception as e:
            self.add_check("Backup Status", False, str(e))
            return False
    
    def run_all_checks(self) -> bool:
        """Run all health checks"""
        print("\n" + "=" * 60)
        print("SYSTEM HEALTH CHECK")
        print("=" * 60 + "\n")
        
        checks = [
            self.check_database_connectivity,
            self.check_database_schema,
            self.check_database_size,
            self.check_memory_usage,
            self.check_disk_space,
            self.check_data_freshness,
            self.check_backup_status
        ]
        
        for check in checks:
            check()
        
        return len(self.errors) == 0
    
    def print_summary(self):
        """Print health check summary"""
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for c in self.checks if c['status'])
        total = len(self.checks)
        
        print(f"\nChecks: {passed}/{total} passed")
        
        if self.warnings:
            print(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")
        
        if self.errors:
            print(f"\nErrors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  ✗ {error}")
        
        if not self.errors and not self.warnings:
            print("\n✓ System health: EXCELLENT")
        elif not self.errors:
            print("\n⚠ System health: GOOD (with warnings)")
        else:
            print("\n✗ System health: POOR (action required)")
        
        print("\n" + "=" * 60)
    
    def export_report(self, filepath: str):
        """Export health check report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "checks": self.checks,
            "warnings": self.warnings,
            "errors": self.errors,
            "summary": {
                "total_checks": len(self.checks),
                "passed": sum(1 for c in self.checks if c['status']),
                "warnings": len(self.warnings),
                "errors": len(self.errors)
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n✓ Report exported to: {filepath}")


def main():
    parser = argparse.ArgumentParser(
        description="System health check tool"
    )
    parser.add_argument(
        '--db-path',
        default='data/planner.db',
        help='Path to database file'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--export',
        help='Export report to JSON file'
    )
    
    args = parser.parse_args()
    
    checker = HealthCheck(args.db_path, args.verbose)
    
    success = checker.run_all_checks()
    checker.print_summary()
    
    if args.export:
        checker.export_report(args.export)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
