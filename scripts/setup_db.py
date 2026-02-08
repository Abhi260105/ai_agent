#!/usr/bin/env python3
"""
Enhanced database setup script
Sets up database schema, indexes, and initial data
"""

import sys
import os
import argparse
from pathlib import Path
import json
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def create_database_schema(db_path: str, verbose: bool = False):
    """
    Create database schema with all required tables
    
    Args:
        db_path: Path to database file
        verbose: Print detailed output
    """
    import sqlite3
    
    if verbose:
        print(f"Creating database at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Memory/Context table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            context_type TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata JSON,
            embedding BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    # Plans table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date DATE NOT NULL,
            plan_content TEXT NOT NULL,
            metadata JSON,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    # Tasks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plan_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'pending',
            due_date TIMESTAMP,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (plan_id) REFERENCES plans(id) ON DELETE SET NULL
        )
    """)
    
    # Preferences table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            preference_key TEXT NOT NULL,
            preference_value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, preference_key)
        )
    """)
    
    # Integrations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            integration_type TEXT NOT NULL,
            credentials JSON,
            config JSON,
            status TEXT DEFAULT 'active',
            last_sync TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    # Audit log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            entity_type TEXT,
            entity_id INTEGER,
            details JSON,
            ip_address TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    
    if verbose:
        print("✓ Created database schema")
    
    return conn


def create_indexes(conn, verbose: bool = False):
    """Create database indexes for performance"""
    cursor = conn.cursor()
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_memory_user_id ON memory(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_memory_context_type ON memory(context_type)",
        "CREATE INDEX IF NOT EXISTS idx_memory_created_at ON memory(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_plans_user_id ON plans(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_plans_date ON plans(date)",
        "CREATE INDEX IF NOT EXISTS idx_plans_status ON plans(status)",
        "CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_tasks_plan_id ON tasks(plan_id)",
        "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)",
        "CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)",
        "CREATE INDEX IF NOT EXISTS idx_integrations_user_id ON integrations(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at)"
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)
    
    conn.commit()
    
    if verbose:
        print(f"✓ Created {len(indexes)} indexes")


def create_triggers(conn, verbose: bool = False):
    """Create database triggers for automatic updates"""
    cursor = conn.cursor()
    
    # Update timestamps trigger
    tables = ['users', 'memory', 'plans', 'tasks', 'preferences', 'integrations']
    
    for table in tables:
        cursor.execute(f"""
            CREATE TRIGGER IF NOT EXISTS update_{table}_timestamp
            AFTER UPDATE ON {table}
            FOR EACH ROW
            BEGIN
                UPDATE {table} SET updated_at = CURRENT_TIMESTAMP
                WHERE id = NEW.id;
            END
        """)
    
    conn.commit()
    
    if verbose:
        print(f"✓ Created triggers for {len(tables)} tables")


def insert_seed_data(conn, verbose: bool = False):
    """Insert initial seed data"""
    cursor = conn.cursor()
    
    # Create default user
    cursor.execute("""
        INSERT OR IGNORE INTO users (username, email)
        VALUES ('default_user', 'user@example.com')
    """)
    
    user_id = cursor.lastrowid or 1
    
    # Insert default preferences
    default_prefs = [
        ('timezone', 'UTC'),
        ('date_format', 'YYYY-MM-DD'),
        ('time_format', '24h'),
        ('notification_email', 'true'),
        ('theme', 'light')
    ]
    
    for key, value in default_prefs:
        cursor.execute("""
            INSERT OR IGNORE INTO preferences (user_id, preference_key, preference_value)
            VALUES (?, ?, ?)
        """, (user_id, key, value))
    
    conn.commit()
    
    if verbose:
        print(f"✓ Inserted seed data (user_id: {user_id})")
    
    return user_id


def verify_setup(conn, verbose: bool = False) -> bool:
    """Verify database setup is correct"""
    cursor = conn.cursor()
    
    # Check tables exist
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        ORDER BY name
    """)
    
    tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = [
        'users', 'memory', 'plans', 'tasks', 
        'preferences', 'integrations', 'audit_log'
    ]
    
    missing_tables = set(expected_tables) - set(tables)
    
    if missing_tables:
        print(f"✗ Missing tables: {missing_tables}")
        return False
    
    if verbose:
        print(f"✓ All {len(expected_tables)} tables present")
    
    # Check indexes
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='index' AND name LIKE 'idx_%'
    """)
    
    indexes = [row[0] for row in cursor.fetchall()]
    
    if verbose:
        print(f"✓ {len(indexes)} indexes created")
    
    return True


def backup_existing_db(db_path: str, verbose: bool = False):
    """Backup existing database before setup"""
    if os.path.exists(db_path):
        import shutil
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{db_path}.backup_{timestamp}"
        
        shutil.copy2(db_path, backup_path)
        
        if verbose:
            print(f"✓ Backed up existing database to: {backup_path}")
        
        return backup_path
    
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Setup database with enhanced schema and features"
    )
    parser.add_argument(
        '--db-path',
        default='data/planner.db',
        help='Path to database file (default: data/planner.db)'
    )
    parser.add_argument(
        '--fresh',
        action='store_true',
        help='Create fresh database (removes existing)'
    )
    parser.add_argument(
        '--no-seed',
        action='store_true',
        help='Skip seed data insertion'
    )
    parser.add_argument(
        '--backup',
        action='store_true',
        help='Backup existing database before setup'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Database Setup Script")
    print("=" * 60)
    
    # Create data directory if needed
    db_dir = os.path.dirname(args.db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
        if args.verbose:
            print(f"✓ Created directory: {db_dir}")
    
    # Backup if requested
    if args.backup and os.path.exists(args.db_path):
        backup_existing_db(args.db_path, args.verbose)
    
    # Remove existing if fresh start
    if args.fresh and os.path.exists(args.db_path):
        os.remove(args.db_path)
        if args.verbose:
            print(f"✓ Removed existing database")
    
    try:
        # Create schema
        conn = create_database_schema(args.db_path, args.verbose)
        
        # Create indexes
        create_indexes(conn, args.verbose)
        
        # Create triggers
        create_triggers(conn, args.verbose)
        
        # Insert seed data
        if not args.no_seed:
            insert_seed_data(conn, args.verbose)
        
        # Verify setup
        if verify_setup(conn, args.verbose):
            print("\n✓ Database setup completed successfully!")
        else:
            print("\n✗ Database setup completed with warnings")
            sys.exit(1)
        
        conn.close()
        
    except Exception as e:
        print(f"\n✗ Error during setup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
