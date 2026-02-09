#!/usr/bin/env python3
"""
Memory export script
Export memory data in various formats for backup or analysis
"""

import sys
import os
import argparse
from pathlib import Path
import sqlite3
import json
import csv
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


def export_to_json(conn, output_path: str, filters: dict = None):
    """Export memory to JSON format"""
    cursor = conn.cursor()
    
    # Build query
    query = """
        SELECT id, user_id, context_type, content, metadata, 
               created_at, updated_at
        FROM memory
    """
    
    conditions = []
    params = []
    
    if filters:
        if 'user_id' in filters:
            conditions.append("user_id = ?")
            params.append(filters['user_id'])
        
        if 'context_type' in filters:
            conditions.append("context_type = ?")
            params.append(filters['context_type'])
        
        if 'since' in filters:
            conditions.append("created_at >= ?")
            params.append(filters['since'])
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY created_at DESC"
    
    cursor.execute(query, params)
    
    records = []
    for row in cursor.fetchall():
        records.append({
            "id": row[0],
            "user_id": row[1],
            "context_type": row[2],
            "content": row[3],
            "metadata": json.loads(row[4]) if row[4] else None,
            "created_at": row[5],
            "updated_at": row[6]
        })
    
    export_data = {
        "export_date": datetime.now().isoformat(),
        "record_count": len(records),
        "filters": filters or {},
        "records": records
    }
    
    with open(output_path, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"✓ Exported {len(records)} records to {output_path}")
    return len(records)


def export_to_csv(conn, output_path: str, filters: dict = None):
    """Export memory to CSV format"""
    cursor = conn.cursor()
    
    # Build query (same as JSON)
    query = """
        SELECT id, user_id, context_type, content, metadata, 
               created_at, updated_at
        FROM memory
    """
    
    conditions = []
    params = []
    
    if filters:
        if 'user_id' in filters:
            conditions.append("user_id = ?")
            params.append(filters['user_id'])
        
        if 'context_type' in filters:
            conditions.append("context_type = ?")
            params.append(filters['context_type'])
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    cursor.execute(query, params)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow([
            'id', 'user_id', 'context_type', 'content', 
            'metadata', 'created_at', 'updated_at'
        ])
        
        # Write records
        count = 0
        for row in cursor.fetchall():
            writer.writerow(row)
            count += 1
    
    print(f"✓ Exported {count} records to {output_path}")
    return count


def export_to_markdown(conn, output_path: str, filters: dict = None):
    """Export memory to Markdown format"""
    cursor = conn.cursor()
    
    # Build query
    query = """
        SELECT id, user_id, context_type, content, created_at
        FROM memory
    """
    
    conditions = []
    params = []
    
    if filters:
        if 'user_id' in filters:
            conditions.append("user_id = ?")
            params.append(filters['user_id'])
        
        if 'context_type' in filters:
            conditions.append("context_type = ?")
            params.append(filters['context_type'])
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY created_at DESC"
    
    cursor.execute(query, params)
    
    with open(output_path, 'w') as f:
        # Write header
        f.write("# Memory Export\n\n")
        f.write(f"**Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        if filters:
            f.write("**Filters:**\n")
            for key, value in filters.items():
                f.write(f"- {key}: {value}\n")
            f.write("\n")
        
        f.write("---\n\n")
        
        # Write records
        count = 0
        current_type = None
        
        for row in cursor.fetchall():
            context_type = row[2]
            
            # Add section header for new type
            if context_type != current_type:
                f.write(f"## {context_type.title()}\n\n")
                current_type = context_type
            
            # Write record
            f.write(f"### Record {row[0]}\n\n")
            f.write(f"**Date:** {row[4]}\n\n")
            f.write(f"{row[3]}\n\n")
            f.write("---\n\n")
            
            count += 1
    
    print(f"✓ Exported {count} records to {output_path}")
    return count


def export_plans(conn, output_path: str, format: str = 'json'):
    """Export plans specifically"""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, user_id, date, plan_content, metadata, status, created_at
        FROM plans
        ORDER BY date DESC
    """)
    
    if format == 'json':
        plans = []
        for row in cursor.fetchall():
            plans.append({
                "id": row[0],
                "user_id": row[1],
                "date": row[2],
                "plan_content": row[3],
                "metadata": json.loads(row[4]) if row[4] else None,
                "status": row[5],
                "created_at": row[6]
            })
        
        with open(output_path, 'w') as f:
            json.dump({
                "export_date": datetime.now().isoformat(),
                "plan_count": len(plans),
                "plans": plans
            }, f, indent=2)
        
        print(f"✓ Exported {len(plans)} plans to {output_path}")
        return len(plans)


def main():
    parser = argparse.ArgumentParser(
        description="Export memory data in various formats"
    )
    parser.add_argument(
        '--db-path',
        default='data/planner.db',
        help='Path to database file'
    )
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Output file path'
    )
    parser.add_argument(
        '--format', '-f',
        choices=['json', 'csv', 'markdown'],
        default='json',
        help='Export format'
    )
    parser.add_argument(
        '--user-id',
        type=int,
        help='Filter by user ID'
    )
    parser.add_argument(
        '--type',
        help='Filter by context type'
    )
    parser.add_argument(
        '--since',
        help='Filter by date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--plans-only',
        action='store_true',
        help='Export plans instead of memory'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Memory Export Tool")
    print("=" * 60)
    
    if not os.path.exists(args.db_path):
        print(f"✗ Database not found: {args.db_path}")
        sys.exit(1)
    
    # Build filters
    filters = {}
    if args.user_id:
        filters['user_id'] = args.user_id
    if args.type:
        filters['context_type'] = args.type
    if args.since:
        filters['since'] = args.since
    
    try:
        conn = sqlite3.connect(args.db_path)
        
        if args.plans_only:
            export_plans(conn, args.output, args.format)
        else:
            if args.format == 'json':
                export_to_json(conn, args.output, filters)
            elif args.format == 'csv':
                export_to_csv(conn, args.output, filters)
            elif args.format == 'markdown':
                export_to_markdown(conn, args.output, filters)
        
        conn.close()
        
        print("\n✓ Export completed successfully")
        
    except Exception as e:
        print(f"\n✗ Export failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
