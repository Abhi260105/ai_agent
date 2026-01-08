"""
Database initialization script for memory and knowledge management system.
Run this script to create the SQLite database and vector store directory structure.

Usage: python init_database.py
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime


def create_directory_structure():
    """Create necessary directories for the application."""
    directories = [
        'data',
        'vector_store',
        'vector_store/memory_embeddings',
        'vector_store/knowledge_embeddings',
        'vector_store/indexes'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")


def create_database():
    """Create SQLite database with memory and knowledge tables."""
    db_path = 'data/memory.db'
    
    # Connect to database (creates file if doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create memories table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL,
        memory_type TEXT NOT NULL CHECK(memory_type IN ('short_term', 'long_term', 'episodic', 'semantic')),
        importance TEXT NOT NULL CHECK(importance IN ('low', 'medium', 'high', 'critical')),
        embedding_id TEXT,
        metadata TEXT DEFAULT '{}',
        tags TEXT DEFAULT '[]',
        access_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_accessed TIMESTAMP,
        related_memories TEXT DEFAULT '[]'
    )
    ''')
    
    # Create knowledge table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS knowledge (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        category TEXT NOT NULL CHECK(category IN ('fact', 'concept', 'procedure', 'relation', 'event', 'entity')),
        confidence TEXT NOT NULL CHECK(confidence IN ('very_low', 'low', 'medium', 'high', 'very_high')),
        source TEXT NOT NULL CHECK(source IN ('user_input', 'document', 'web_search', 'inference', 'external_api')),
        source_url TEXT,
        embedding_id TEXT,
        metadata TEXT DEFAULT '{}',
        tags TEXT DEFAULT '[]',
        relationships TEXT DEFAULT '{}',
        verified INTEGER DEFAULT 0,
        access_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_accessed TIMESTAMP
    )
    ''')
    
    # Create indexes for better query performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge(category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_source ON knowledge(source)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_verified ON knowledge(verified)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_created ON knowledge(created_at)')
    
    # Create vector embeddings metadata table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS embeddings_metadata (
        id TEXT PRIMARY KEY,
        entity_type TEXT NOT NULL CHECK(entity_type IN ('memory', 'knowledge')),
        entity_id INTEGER NOT NULL,
        vector_dimensions INTEGER NOT NULL,
        model_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    print(f"✓ Created database: {db_path}")
    
    # Display table info
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"✓ Tables created: {[table[0] for table in tables]}")
    
    conn.close()


def create_vector_store_config():
    """Create configuration file for vector store."""
    config = {
        "vector_store": {
            "type": "faiss",
            "dimensions": 768,
            "metric": "cosine",
            "index_type": "IVF",
            "nlist": 100
        },
        "embedding_model": {
            "name": "sentence-transformers/all-mpnet-base-v2",
            "dimensions": 768,
            "max_length": 512
        },
        "paths": {
            "memory_embeddings": "vector_store/memory_embeddings",
            "knowledge_embeddings": "vector_store/knowledge_embeddings",
            "indexes": "vector_store/indexes"
        }
    }
    
    import json
    config_path = 'vector_store/config.json'
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✓ Created vector store config: {config_path}")


def create_readme():
    """Create README files for documentation."""
    
    # Main data README
    data_readme = """# Data Directory

This directory contains the SQLite database for the memory and knowledge management system.

## Files
- `memory.db`: SQLite database containing memories and knowledge items

## Tables
- `memories`: Stores user memories with embeddings
- `knowledge`: Stores knowledge graph items with relationships
- `embeddings_metadata`: Tracks vector embedding metadata

## Backup
Regular backups are recommended. Use:
```bash
sqlite3 data/memory.db ".backup 'data/memory_backup.db'"
```
"""
    
    with open('data/README.md', 'w') as f:
        f.write(data_readme)
    
    # Vector store README
    vector_readme = """# Vector Store Directory

This directory contains vector embeddings and FAISS indexes for semantic search.

## Structure
- `memory_embeddings/`: Vector embeddings for memory items
- `knowledge_embeddings/`: Vector embeddings for knowledge items
- `indexes/`: FAISS indexes for fast similarity search
- `config.json`: Configuration for embedding models and vector store

## Models
Default embedding model: sentence-transformers/all-mpnet-base-v2 (768 dimensions)

## Indexes
FAISS indexes are automatically created and updated when items are added.
"""
    
    with open('vector_store/README.md', 'w') as f:
        f.write(vector_readme)
    
    print("✓ Created README files")


def insert_sample_data(sample=False):
    """Insert sample data for testing (optional)."""
    if not sample:
        return
    
    conn = sqlite3.connect('data/memory.db')
    cursor = conn.cursor()
    
    # Sample memories
    memories = [
        ("User prefers Python for backend development", "semantic", "high", '{"context": "programming"}', '["python", "backend"]'),
        ("Had a great meeting with the team yesterday", "episodic", "medium", '{"date": "2025-01-06"}', '["meeting", "team"]'),
        ("Need to finish the project report by Friday", "short_term", "high", '{"deadline": "2025-01-10"}', '["task", "deadline"]')
    ]
    
    for content, mem_type, importance, metadata, tags in memories:
        cursor.execute('''
        INSERT INTO memories (content, memory_type, importance, metadata, tags)
        VALUES (?, ?, ?, ?, ?)
        ''', (content, mem_type, importance, metadata, tags))
    
    # Sample knowledge
    knowledge_items = [
        ("Python", "Python is a high-level programming language", "concept", "very_high", "user_input", '{"category": "programming"}', '["python", "programming"]'),
        ("FastAPI", "FastAPI is a modern web framework for building APIs", "concept", "high", "user_input", '{"version": "0.100+"}', '["fastapi", "api", "python"]'),
        ("REST API", "REST is an architectural style for distributed systems", "concept", "high", "user_input", '{}', '["api", "architecture"]')
    ]
    
    for title, content, category, confidence, source, metadata, tags in knowledge_items:
        cursor.execute('''
        INSERT INTO knowledge (title, content, category, confidence, source, metadata, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, content, category, confidence, source, metadata, tags))
    
    conn.commit()
    conn.close()
    
    print("✓ Inserted sample data")


def main():
    """Main initialization function."""
    print("=== Initializing Memory & Knowledge Database System ===\n")
    
    try:
        # Create directory structure
        create_directory_structure()
        print()
        
        # Create database
        create_database()
        print()
        
        # Create vector store config
        create_vector_store_config()
        print()
        
        # Create documentation
        create_readme()
        print()
        
        # Ask about sample data
        response = input("Would you like to insert sample data? (y/n): ").lower()
        if response == 'y':
            insert_sample_data(sample=True)
            print()
        
        print("=== Initialization Complete! ===")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Configure your embedding model in vector_store/config.json")
        print("3. Start your application: uvicorn app.main:app --reload")
        
    except Exception as e:
        print(f"\n✗ Error during initialization: {e}")
        raise


if __name__ == "__main__":
    main()