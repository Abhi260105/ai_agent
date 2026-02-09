#!/usr/bin/env python3
"""
Data migration script
Handles database schema migrations and data transformations
"""

import sys
import os
import argparse
from pathlib import Path
import sqlite3
from datetime import datetime
import json

sys.path.insert(0, str(Path(__file__).parent.parent))


class Migration:
    """Base migration class"""
    
    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()
    
    def execute(self):
        """Execute the migration"""
        raise NotImplementedError
    
    def rollback(self):
        """Rollback the migration"""
        raise NotImplementedError


class AddEmbeddingsMigration(Migration):
    """Add embeddings support to memory table"""
    
    def execute(self):
        print("Adding embedding column to memory table...")
        
        # Check if column already exists
        self.cursor.execute("PRAGMA table_info(memory)")
        columns = [row[1] for row in self.cursor.fetchall()]
        
        if 'embedding' not in columns:
            self.cursor.execute("""
                ALTER TABLE memory 
                ADD COLUMN embedding BLOB
            """)
            self.conn.commit()
            print("✓ Added embedding column")
        else:
            print("⊘ Embedding column already exists")
    
    def rollback(self):
        print("Cannot rollback ALTER TABLE ADD COLUMN in SQLite")


class AddTagsMigration(Migration):
    """Add tags system"""
    
    def execute(self):
        print("Creating tags table...")
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_tags (
                memory_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (memory_id, tag_id),
                FOREIGN KEY (memory_id) REFERENCES memory(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        """)
        
        self.conn.commit()
        print("✓ Created tags tables")
    
    def rollback(self):
        print("Dropping tags tables...")
        self.cursor.execute("DROP TABLE IF EXISTS memory_tags")
        self.cursor.execute("DROP TABLE IF EXISTS tags")
        self.conn.commit()
        print("✓ Rolled back tags migration")


class MigrateContextTypesMigration(Migration):
    """Migrate old context types to new schema"""
    
    OLD_TO_NEW = {
        'email': 'communication',
        'calendar': 'schedule',
        'note': 'knowledge',
    }
    
    def execute(self):
        print("Migrating context types...")
        
        for old_type, new_type in self.OLD_TO_NEW.items():
            self.cursor.execute("""
                UPDATE memory 
                SET context_type = ?
                WHERE context_type = ?
            """, (new_type, old_type))
            
            updated = self.cursor.rowcount
            if updated > 0:
                print(f"✓ Migrated {updated} records: {old_type} -> {new_type}")
        
        self.conn.commit()
    
    def rollback(self):
        print("Rolling back context type migration...")
        
        for old_type, new_type in self.OLD_TO_NEW.items():
            self.cursor.execute("""
                UPDATE memory 
                SET context_type = ?
                WHERE context_type = ?
            """, (old_type, new_type))
        
        self.conn.commit()
        print("✓ Rolled back context types")


class MigrationManager:
    """Manages database migrations"""
    
    MIGRATIONS = {
        '001_add_embeddings': AddEmbeddingsMigration,
        '002_add_tags': AddTagsMigration,
        '003_migrate_context_types': MigrateContextTypesMigration,
    }
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._ensure_migration_table()
    
    def _ensure_migration_table(self):
        """Create migrations tracking table"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
    
    def get_applied_migrations(self):
        """Get list of applied migrations"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM migrations ORDER BY id")
        return [row[0] for row in cursor.fetchall()]
    
    def get_pending_migrations(self):
        """Get list of pending migrations"""
        applied = set(self.get_applied_migrations())
        all_migrations = set(self.MIGRATIONS.keys())
        return sorted(all_migrations - applied)
    
    def apply_migration(self, name: str):
        """Apply a specific migration"""
        if name not in self.MIGRATIONS:
            raise ValueError(f"Unknown migration: {name}")
        
        print(f"\nApplying migration: {name}")
        print("-" * 60)
        
        migration_class = self.MIGRATIONS[name]
        migration = migration_class(self.conn)
        
        try:
            migration.execute()
            
            # Record migration
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO migrations (name) VALUES (?)
            """, (name,))
            self.conn.commit()
            
            print(f"✓ Migration {name} applied successfully")
            return True
            
        except Exception as e:
            print(f"✗ Migration {name} failed: {e}")
            self.conn.rollback()
            return False
    
    def rollback_migration(self, name: str):
        """Rollback a specific migration"""
        if name not in self.MIGRATIONS:
            raise ValueError(f"Unknown migration: {name}")
        
        print(f"\nRolling back migration: {name}")
        print("-" * 60)
        
        migration_class = self.MIGRATIONS[name]
        migration = migration_class(self.conn)
        
        try:
            migration.rollback()
            
            # Remove migration record
            cursor = self.conn.cursor()
            cursor.execute("""
                DELETE FROM migrations WHERE name = ?
            """, (name,))
            self.conn.commit()
            
            print(f"✓ Migration {name} rolled back successfully")
            return True
            
        except Exception as e:
            print(f"✗ Rollback of {name} failed: {e}")
            self.conn.rollback()
            return False
    
    def migrate_all(self):
        """Apply all pending migrations"""
        pending = self.get_pending_migrations()
        
        if not pending:
            print("✓ No pending migrations")
            return True
        
        print(f"Found {len(pending)} pending migrations")
        
        for name in pending:
            if not self.apply_migration(name):
                print(f"\n✗ Migration stopped at: {name}")
                return False
        
        print(f"\n✓ All {len(pending)} migrations applied successfully")
        return True
    
    def status(self):
        """Show migration status"""
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()
        
        print("\nMigration Status")
        print("=" * 60)
        
        print(f"\nApplied ({len(applied)}):")
        for name in applied:
            print(f"  ✓ {name}")
        
        print(f"\nPending ({len(pending)}):")
        for name in pending:
            print(f"  ○ {name}")
        
        print("\n" + "=" * 60)
    
    def close(self):
        """Close database connection"""
        self.conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Database migration tool"
    )
    parser.add_argument(
        '--db-path',
        default='data/planner.db',
        help='Path to database file'
    )
    parser.add_argument(
        'command',
        choices=['status', 'migrate', 'rollback', 'list'],
        help='Migration command'
    )
    parser.add_argument(
        '--migration',
        help='Specific migration name (for rollback)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Database Migration Tool")
    print("=" * 60)
    
    if not os.path.exists(args.db_path):
        print(f"✗ Database not found: {args.db_path}")
        sys.exit(1)
    
    manager = MigrationManager(args.db_path)
    
    try:
        if args.command == 'status':
            manager.status()
        
        elif args.command == 'list':
            print("\nAvailable migrations:")
            for name in sorted(manager.MIGRATIONS.keys()):
                print(f"  - {name}")
        
        elif args.command == 'migrate':
            success = manager.migrate_all()
            sys.exit(0 if success else 1)
        
        elif args.command == 'rollback':
            if not args.migration:
                print("✗ --migration required for rollback")
                sys.exit(1)
            
            success = manager.rollback_migration(args.migration)
            sys.exit(0 if success else 1)
    
    finally:
        manager.close()


if __name__ == "__main__":
    main()
