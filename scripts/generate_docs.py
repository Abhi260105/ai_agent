#!/usr/bin/env python3
"""
Auto-documentation generator
Generates documentation from code, database schema, and API endpoints
"""

import sys
import os
import argparse
from pathlib import Path
import sqlite3
import ast
import inspect
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


def generate_database_schema_docs(db_path: str, output_path: str):
    """Generate documentation for database schema"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        ORDER BY name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    with open(output_path, 'w') as f:
        f.write("# Database Schema Documentation\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        
        for table in tables:
            f.write(f"## Table: `{table}`\n\n")
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            f.write("### Columns\n\n")
            f.write("| Column | Type | Nullable | Default | Primary Key |\n")
            f.write("|--------|------|----------|---------|-------------|\n")
            
            for col in columns:
                name = col[1]
                type_ = col[2]
                nullable = "Yes" if col[3] == 0 else "No"
                default = col[4] or "-"
                pk = "Yes" if col[5] == 1 else "No"
                
                f.write(f"| {name} | {type_} | {nullable} | {default} | {pk} |\n")
            
            # Get indexes
            cursor.execute(f"""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND tbl_name='{table}'
            """)
            indexes = cursor.fetchall()
            
            if indexes:
                f.write("\n### Indexes\n\n")
                for idx in indexes:
                    f.write(f"- `{idx[0]}`\n")
            
            f.write("\n---\n\n")
    
    conn.close()
    print(f"✓ Generated database schema docs: {output_path}")


def generate_api_docs(source_dir: str, output_path: str):
    """Generate API documentation from Python source files"""
    
    with open(output_path, 'w') as f:
        f.write("# API Documentation\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        
        # Find all Python files
        for root, dirs, files in os.walk(source_dir):
            for filename in files:
                if filename.endswith('.py') and not filename.startswith('__'):
                    filepath = os.path.join(root, filename)
                    
                    try:
                        with open(filepath, 'r') as src:
                            tree = ast.parse(src.read())
                        
                        # Extract classes and functions
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                f.write(f"## Class: `{node.name}`\n\n")
                                
                                docstring = ast.get_docstring(node)
                                if docstring:
                                    f.write(f"{docstring}\n\n")
                                
                                # Extract methods
                                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                                if methods:
                                    f.write("### Methods\n\n")
                                    for method in methods:
                                        f.write(f"#### `{method.name}`\n\n")
                                        method_doc = ast.get_docstring(method)
                                        if method_doc:
                                            f.write(f"{method_doc}\n\n")
                                
                                f.write("---\n\n")
                    
                    except Exception as e:
                        print(f"Warning: Could not parse {filepath}: {e}")
    
    print(f"✓ Generated API docs: {output_path}")


def generate_configuration_docs(output_path: str):
    """Generate configuration documentation"""
    
    config_template = """# Configuration Guide

Generated: {date}

---

## Environment Variables

### Database Configuration

- `DATABASE_PATH`: Path to SQLite database file
  - Default: `data/planner.db`
  - Example: `/var/lib/planner/db.sqlite`

- `DATABASE_BACKUP_ENABLED`: Enable automatic backups
  - Default: `true`
  - Options: `true`, `false`

### LLM Configuration

- `LLM_PROVIDER`: LLM service provider
  - Default: `openai`
  - Options: `openai`, `anthropic`, `local`

- `LLM_API_KEY`: API key for LLM service
  - Required: Yes (for cloud providers)
  - Example: `sk-...`

- `LLM_MODEL`: Model name to use
  - Default: `gpt-4`
  - Example: `claude-3-opus-20240229`

### Integration Configuration

- `EMAIL_ENABLED`: Enable email integration
  - Default: `false`
  - Options: `true`, `false`

- `CALENDAR_ENABLED`: Enable calendar integration
  - Default: `false`
  - Options: `true`, `false`

### Performance Configuration

- `CACHE_ENABLED`: Enable response caching
  - Default: `true`
  - Options: `true`, `false`

- `CACHE_TTL`: Cache time-to-live in seconds
  - Default: `3600`
  - Example: `7200`

---

## Configuration Files

### `config.json`

Main configuration file in JSON format:

```json
{{
  "database": {{
    "path": "data/planner.db",
    "backup_enabled": true
  }},
  "llm": {{
    "provider": "openai",
    "model": "gpt-4"
  }}
}}
```

---

## Logging Configuration

- `LOG_LEVEL`: Logging level
  - Default: `INFO`
  - Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`

- `LOG_FILE`: Log file path
  - Default: `logs/planner.log`

"""
    
    with open(output_path, 'w') as f:
        f.write(config_template.format(
            date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
    
    print(f"✓ Generated configuration docs: {output_path}")


def generate_readme(output_path: str):
    """Generate main README.md"""
    
    readme = """# Daily Planner AI System

An intelligent daily planning system that integrates with your email, calendar, and tasks to generate optimized daily plans.

## Features

- 🤖 AI-powered daily plan generation
- 📧 Email integration and prioritization
- 📅 Calendar event analysis
- ✅ Task management
- 🧠 Long-term memory and preferences
- 📊 Performance monitoring
- 🔄 Data migration and backup tools

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Setup database
python scripts/setup_db.py

# Import sample knowledge
python scripts/import_knowledge.py --sample
```

### Usage

```python
from src.planner import DailyPlanner

planner = DailyPlanner(user_id=1)
plan = planner.generate_daily_plan(date="2024-01-15")
print(plan)
```

## Documentation

- [Database Schema](docs/database_schema.md)
- [API Documentation](docs/api.md)
- [Configuration Guide](docs/configuration.md)
- [Testing Guide](docs/testing.md)

## Scripts

- `setup_db.py` - Database setup and initialization
- `reset_memory.py` - Memory management and cleanup
- `migrate_data.py` - Database migrations
- `export_memory.py` - Export data for backup
- `import_knowledge.py` - Import knowledge base
- `benchmark.py` - Performance benchmarking
- `health_check.py` - System health monitoring

## Testing

```bash
# Run all tests
./scripts/run_tests.sh

# Run specific test suite
./scripts/run_tests.sh --unit
./scripts/run_tests.sh --integration

# Run with coverage
./scripts/run_tests.sh --coverage
```

## Performance

```bash
# Run benchmarks
python scripts/benchmark.py

# Check system health
python scripts/health_check.py
```

## License

MIT License
"""
    
    with open(output_path, 'w') as f:
        f.write(readme)
    
    print(f"✓ Generated README: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Auto-generate documentation"
    )
    parser.add_argument(
        '--db-path',
        default='data/planner.db',
        help='Path to database file'
    )
    parser.add_argument(
        '--output-dir',
        default='docs',
        help='Output directory for documentation'
    )
    parser.add_argument(
        '--source-dir',
        default='src',
        help='Source code directory'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Generate all documentation'
    )
    parser.add_argument(
        '--schema',
        action='store_true',
        help='Generate database schema docs'
    )
    parser.add_argument(
        '--api',
        action='store_true',
        help='Generate API docs'
    )
    parser.add_argument(
        '--config',
        action='store_true',
        help='Generate configuration docs'
    )
    parser.add_argument(
        '--readme',
        action='store_true',
        help='Generate README'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Documentation Generator")
    print("=" * 60)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    try:
        if args.all or args.schema:
            if os.path.exists(args.db_path):
                generate_database_schema_docs(
                    args.db_path,
                    os.path.join(args.output_dir, 'database_schema.md')
                )
            else:
                print(f"⊘ Skipping schema docs (database not found)")
        
        if args.all or args.api:
            if os.path.exists(args.source_dir):
                generate_api_docs(
                    args.source_dir,
                    os.path.join(args.output_dir, 'api.md')
                )
            else:
                print(f"⊘ Skipping API docs (source directory not found)")
        
        if args.all or args.config:
            generate_configuration_docs(
                os.path.join(args.output_dir, 'configuration.md')
            )
        
        if args.all or args.readme:
            generate_readme('README.md')
        
        print("\n✓ Documentation generation completed")
        
    except Exception as e:
        print(f"\n✗ Documentation generation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
