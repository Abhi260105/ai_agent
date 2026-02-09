#!/usr/bin/env python3
"""
Knowledge import script
Import knowledge base data from various sources
"""

import sys
import os
import argparse
from pathlib import Path
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))


def import_from_json(conn, filepath: str, user_id: int):
    """Import knowledge from JSON file"""
    print(f"Importing from JSON: {filepath}")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    cursor = conn.cursor()
    imported = 0
    
    # Handle different JSON structures
    if 'records' in data:
        records = data['records']
    elif isinstance(data, list):
        records = data
    else:
        print("✗ Unsupported JSON structure")
        return 0
    
    for record in records:
        cursor.execute("""
            INSERT INTO memory (user_id, context_type, content, metadata)
            VALUES (?, ?, ?, ?)
        """, (
            user_id,
            record.get('context_type', 'knowledge'),
            record.get('content', ''),
            json.dumps(record.get('metadata', {}))
        ))
        imported += 1
    
    conn.commit()
    print(f"✓ Imported {imported} records")
    return imported


def import_from_text_file(conn, filepath: str, user_id: int, context_type: str):
    """Import knowledge from plain text file"""
    print(f"Importing from text file: {filepath}")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO memory (user_id, context_type, content, metadata)
        VALUES (?, ?, ?, ?)
    """, (
        user_id,
        context_type,
        content,
        json.dumps({
            'source': os.path.basename(filepath),
            'imported_at': datetime.now().isoformat()
        })
    ))
    
    conn.commit()
    print(f"✓ Imported 1 record from text file")
    return 1


def import_from_directory(conn, dirpath: str, user_id: int):
    """Import all knowledge files from a directory"""
    print(f"Importing from directory: {dirpath}")
    
    imported = 0
    
    for filename in os.listdir(dirpath):
        filepath = os.path.join(dirpath, filename)
        
        if not os.path.isfile(filepath):
            continue
        
        ext = os.path.splitext(filename)[1].lower()
        
        try:
            if ext == '.json':
                imported += import_from_json(conn, filepath, user_id)
            elif ext in ['.txt', '.md']:
                imported += import_from_text_file(
                    conn, filepath, user_id, 
                    context_type='knowledge'
                )
        except Exception as e:
            print(f"✗ Failed to import {filename}: {e}")
    
    print(f"\n✓ Total imported: {imported} records")
    return imported


def import_from_csv(conn, filepath: str, user_id: int):
    """Import knowledge from CSV file"""
    import csv
    
    print(f"Importing from CSV: {filepath}")
    
    cursor = conn.cursor()
    imported = 0
    
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            cursor.execute("""
                INSERT INTO memory (user_id, context_type, content, metadata)
                VALUES (?, ?, ?, ?)
            """, (
                user_id,
                row.get('context_type', 'knowledge'),
                row.get('content', ''),
                json.dumps({'source': 'csv', 'row_data': row})
            ))
            imported += 1
    
    conn.commit()
    print(f"✓ Imported {imported} records from CSV")
    return imported


def import_sample_knowledge(conn, user_id: int):
    """Import sample knowledge base"""
    print("Importing sample knowledge...")
    
    samples = [
        {
            'type': 'productivity_tip',
            'content': 'Use the 2-minute rule: If a task takes less than 2 minutes, do it immediately.'
        },
        {
            'type': 'productivity_tip',
            'content': 'Time-block your calendar to ensure deep work sessions are protected.'
        },
        {
            'type': 'preference',
            'content': 'Prefer morning slots for creative work and afternoon for meetings.'
        },
        {
            'type': 'routine',
            'content': 'Daily standup at 9:30 AM with the team.'
        },
        {
            'type': 'routine',
            'content': 'Weekly 1:1 with manager every Friday at 2 PM.'
        }
    ]
    
    cursor = conn.cursor()
    
    for sample in samples:
        cursor.execute("""
            INSERT INTO memory (user_id, context_type, content, metadata)
            VALUES (?, ?, ?, ?)
        """, (
            user_id,
            sample['type'],
            sample['content'],
            json.dumps({'source': 'sample', 'imported_at': datetime.now().isoformat()})
        ))
    
    conn.commit()
    print(f"✓ Imported {len(samples)} sample knowledge items")
    return len(samples)


def validate_import_file(filepath: str) -> bool:
    """Validate import file exists and is readable"""
    if not os.path.exists(filepath):
        print(f"✗ File not found: {filepath}")
        return False
    
    if not os.access(filepath, os.R_OK):
        print(f"✗ File not readable: {filepath}")
        return False
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Import knowledge base data from various sources"
    )
    parser.add_argument(
        '--db-path',
        default='data/planner.db',
        help='Path to database file'
    )
    parser.add_argument(
        '--input', '-i',
        help='Input file or directory path'
    )
    parser.add_argument(
        '--user-id',
        type=int,
        default=1,
        help='User ID for imported knowledge'
    )
    parser.add_argument(
        '--format', '-f',
        choices=['json', 'csv', 'text', 'directory', 'auto'],
        default='auto',
        help='Input format'
    )
    parser.add_argument(
        '--context-type',
        default='knowledge',
        help='Context type for imported data'
    )
    parser.add_argument(
        '--sample',
        action='store_true',
        help='Import sample knowledge base'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Knowledge Import Tool")
    print("=" * 60)
    
    if not os.path.exists(args.db_path):
        print(f"✗ Database not found: {args.db_path}")
        sys.exit(1)
    
    try:
        conn = sqlite3.connect(args.db_path)
        
        if args.sample:
            import_sample_knowledge(conn, args.user_id)
        elif args.input:
            if not validate_import_file(args.input):
                sys.exit(1)
            
            # Auto-detect format
            if args.format == 'auto':
                if os.path.isdir(args.input):
                    args.format = 'directory'
                else:
                    ext = os.path.splitext(args.input)[1].lower()
                    if ext == '.json':
                        args.format = 'json'
                    elif ext == '.csv':
                        args.format = 'csv'
                    else:
                        args.format = 'text'
            
            # Import based on format
            if args.format == 'json':
                import_from_json(conn, args.input, args.user_id)
            elif args.format == 'csv':
                import_from_csv(conn, args.input, args.user_id)
            elif args.format == 'text':
                import_from_text_file(conn, args.input, args.user_id, args.context_type)
            elif args.format == 'directory':
                import_from_directory(conn, args.input, args.user_id)
        else:
            print("✗ No input specified. Use --input or --sample")
            sys.exit(1)
        
        conn.close()
        print("\n✓ Import completed successfully")
        
    except Exception as e:
        print(f"\n✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
