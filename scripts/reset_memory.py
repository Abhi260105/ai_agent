#!/usr/bin/env python3
"""
Advanced memory reset script
Safely resets memory with backup and selective clearing options
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import json

sys.path.insert(0, str(Path(__file__).parent.parent))


def reset_all_memory(conn, verbose: bool = False):
    """Reset all memory data"""
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM memory")
    deleted = cursor.rowcount
    
    conn.commit()
    
    if verbose:
        print(f"✓ Deleted {deleted} memory records")
    
    return deleted


def reset_by_user(conn, user_id: int, verbose: bool = False):
    """Reset memory for specific user"""
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM memory WHERE user_id = ?", (user_id,))
    deleted = cursor.rowcount
    
    conn.commit()
    
    if verbose:
        print(f"✓ Deleted {deleted} memory records for user {user_id}")
    
    return deleted


def reset_by_type(conn, context_type: str, verbose: bool = False):
    """Reset memory of specific type"""
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM memory WHERE context_type = ?", (context_type,))
    deleted = cursor.rowcount
    
    conn.commit()
    
    if verbose:
        print(f"✓ Deleted {deleted} '{context_type}' memory records")
    
    return deleted


def reset_old_memory(conn, days: int, verbose: bool = False):
    """Reset memory older than specified days"""
    cursor = conn.cursor()
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    cursor.execute(
        "DELETE FROM memory WHERE created_at < ?",
        (cutoff_date.isoformat(),)
    )
    deleted = cursor.rowcount
    
    conn.commit()
    
    if verbose:
        print(f"✓ Deleted {deleted} memory records older than {days} days")
    
    return deleted


def backup_memory(conn, backup_path: str, verbose: bool = False):
    """Backup memory data before reset"""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, user_id, context_type, content, metadata, created_at, updated_at
        FROM memory
        ORDER BY created_at DESC
    """)
    
    records = []
    for row in cursor.fetchall():
        records.append({
            "id": row[0],
            "user_id": row[1],
            "context_type": row[2],
            "content": row[3],
            "metadata": row[4],
            "created_at": row[5],
            "updated_at": row[6]
        })
    
    with open(backup_path, 'w') as f:
        json.dump({
            "backup_date": datetime.now().isoformat(),
            "record_count": len(records),
            "records": records
        }, f, indent=2)
    
    if verbose:
        print(f"✓ Backed up {len(records)} records to {backup_path}")
    
    return len(records)


def get_memory_stats(conn) -> dict:
    """Get memory statistics"""
    cursor = conn.cursor()
    
    # Total count
    cursor.execute("SELECT COUNT(*) FROM memory")
    total = cursor.fetchone()[0]
    
    # By type
    cursor.execute("""
        SELECT context_type, COUNT(*) 
        FROM memory 
        GROUP BY context_type
    """)
    by_type = dict(cursor.fetchall())
    
    # By user
    cursor.execute("""
        SELECT user_id, COUNT(*) 
        FROM memory 
        GROUP BY user_id
    """)
    by_user = dict(cursor.fetchall())
    
    # Date range
    cursor.execute("""
        SELECT MIN(created_at), MAX(created_at)
        FROM memory
    """)
    date_range = cursor.fetchone()
    
    return {
        "total": total,
        "by_type": by_type,
        "by_user": by_user,
        "oldest": date_range[0],
        "newest": date_range[1]
    }


def print_stats(stats: dict):
    """Print memory statistics"""
    print("\nMemory Statistics:")
    print("=" * 60)
    print(f"Total Records: {stats['total']}")
    
    if stats['by_type']:
        print("\nBy Type:")
        for ctx_type, count in stats['by_type'].items():
            print(f"  {ctx_type}: {count}")
    
    if stats['by_user']:
        print("\nBy User:")
        for user_id, count in stats['by_user'].items():
            print(f"  User {user_id}: {count}")
    
    if stats['oldest'] and stats['newest']:
        print(f"\nDate Range:")
        print(f"  Oldest: {stats['oldest']}")
        print(f"  Newest: {stats['newest']}")
    
    print("=" * 60)


def confirm_reset(stats: dict) -> bool:
    """Ask user to confirm reset operation"""
    print_stats(stats)
    print(f"\n⚠️  WARNING: This will delete {stats['total']} memory records!")
    
    response = input("\nContinue with reset? (yes/no): ").strip().lower()
    
    return response == 'yes'


def main():
    parser = argparse.ArgumentParser(
        description="Advanced memory reset with backup and selective clearing"
    )
    parser.add_argument(
        '--db-path',
        default='data/planner.db',
        help='Path to database file'
    )
    parser.add_argument(
        '--user-id',
        type=int,
        help='Reset memory for specific user only'
    )
    parser.add_argument(
        '--type',
        help='Reset memory of specific type only'
    )
    parser.add_argument(
        '--older-than',
        type=int,
        metavar='DAYS',
        help='Reset memory older than N days'
    )
    parser.add_argument(
        '--backup',
        action='store_true',
        help='Backup before reset'
    )
    parser.add_argument(
        '--backup-path',
        help='Custom backup file path'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation prompt'
    )
    parser.add_argument(
        '--stats-only',
        action='store_true',
        help='Show statistics without resetting'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Memory Reset Script")
    print("=" * 60)
    
    # Check database exists
    if not os.path.exists(args.db_path):
        print(f"✗ Database not found: {args.db_path}")
        sys.exit(1)
    
    try:
        import sqlite3
        conn = sqlite3.connect(args.db_path)
        
        # Get current stats
        stats = get_memory_stats(conn)
        
        # Show stats and exit if requested
        if args.stats_only:
            print_stats(stats)
            sys.exit(0)
        
        # Backup if requested
        if args.backup:
            backup_path = args.backup_path or f"memory_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            backup_memory(conn, backup_path, args.verbose)
        
        # Confirm unless forced
        if not args.force:
            if not confirm_reset(stats):
                print("\nReset cancelled.")
                sys.exit(0)
        
        # Perform reset
        deleted = 0
        
        if args.user_id:
            deleted = reset_by_user(conn, args.user_id, args.verbose)
        elif args.type:
            deleted = reset_by_type(conn, args.type, args.verbose)
        elif args.older_than:
            deleted = reset_old_memory(conn, args.older_than, args.verbose)
        else:
            deleted = reset_all_memory(conn, args.verbose)
        
        print(f"\n✓ Successfully deleted {deleted} memory records")
        
        # Show new stats
        if args.verbose:
            new_stats = get_memory_stats(conn)
            print(f"\nRemaining records: {new_stats['total']}")
        
        conn.close()
        
    except Exception as e:
        print(f"\n✗ Error during reset: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
