"""
Storage Service - Database Operations
Provides SQLite CRUD operations with vector store integration
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import json
import sqlite3
from contextlib import contextmanager

from app.config import config
from app.utils.logger import get_logger

logger = get_logger("services.storage")


class StorageService:
    """
    Database and storage operations
    
    Features:
    - SQLite operations (CRUD)
    - Transaction management
    - Query optimization
    - Data migration
    - Backup and restore
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(config.storage.db_path)
        self.logger = logger
        
        # Ensure database directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._initialize_database()
        
        self.logger.info("Storage service initialized", db_path=self.db_path)
    
    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dicts
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error("Transaction failed", error=str(e))
            raise
        finally:
            conn.close()
    
    def _initialize_database(self):
        """Create database schema if not exists"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tasks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    user_goal TEXT NOT NULL,
                    plan_id TEXT,
                    status TEXT NOT NULL,
                    started_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    duration_seconds REAL,
                    success_rate REAL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Steps table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS steps (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    step_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    duration_ms REAL,
                    retry_count INTEGER DEFAULT 0,
                    error_message TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                )
            """)
            
            # Tool usage table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tool_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    duration_ms REAL,
                    error_type TEXT,
                    step_id TEXT,
                    task_id TEXT,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                )
            """)
            
            # Evaluations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    step_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    confidence REAL,
                    error_type TEXT,
                    retry_recommended BOOLEAN,
                    replan_recommended BOOLEAN,
                    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                )
            """)
            
            # Retries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS retries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    step_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    attempt_number INTEGER NOT NULL,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    backoff_seconds REAL,
                    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                )
            """)
            
            # Learned patterns table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learned_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,
                    pattern_data TEXT NOT NULL,
                    confidence REAL DEFAULT 0.5,
                    usage_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    last_used TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_status 
                ON tasks(status)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_steps_task_id 
                ON steps(task_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tool_usage_tool 
                ON tool_usage(tool_name, action)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_evaluations_task 
                ON evaluations(task_id)
            """)
            
            self.logger.info("Database schema initialized")
    
    # =========================================================================
    # TASK OPERATIONS
    # =========================================================================
    
    def create_task(self, task_data: Dict[str, Any]) -> str:
        """Create new task record"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            task_id = task_data.get("id", f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            cursor.execute("""
                INSERT INTO tasks (
                    id, user_goal, plan_id, status, 
                    started_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                task_id,
                task_data["user_goal"],
                task_data.get("plan_id"),
                task_data.get("status", "initializing"),
                task_data.get("started_at", datetime.now()),
                json.dumps(task_data.get("metadata", {}))
            ))
            
            self.logger.info("Task created", task_id=task_id)
            return task_id
    
    def update_task(self, task_id: str, updates: Dict[str, Any]):
        """Update task record"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Build update query dynamically
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                if key == "metadata":
                    value = json.dumps(value)
                set_clauses.append(f"{key} = ?")
                values.append(value)
            
            values.append(task_id)
            
            query = f"""
                UPDATE tasks 
                SET {', '.join(set_clauses)}
                WHERE id = ?
            """
            
            cursor.execute(query, values)
            self.logger.debug("Task updated", task_id=task_id)
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            
            if row:
                task = dict(row)
                if task.get("metadata"):
                    task["metadata"] = json.loads(task["metadata"])
                return task
            return None
    
    def list_tasks(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List tasks with optional filtering"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM tasks"
            params = []
            
            if status:
                query += " WHERE status = ?"
                params.append(status)
            
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            tasks = []
            for row in rows:
                task = dict(row)
                if task.get("metadata"):
                    task["metadata"] = json.loads(task["metadata"])
                tasks.append(task)
            
            return tasks
    
    # =========================================================================
    # STEP OPERATIONS
    # =========================================================================
    
    def create_step(self, step_data: Dict[str, Any]) -> int:
        """Create step record"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO steps (
                    id, task_id, step_id, action, tool_name,
                    status, started_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                step_data["task_id"],
                step_data["step_id"],
                step_data["action"],
                step_data["tool_name"],
                step_data.get("status", "running"),
                step_data.get("started_at", datetime.now()),
                json.dumps(step_data.get("metadata", {}))
            ))
            
            return cursor.lastrowid
    
    def update_step(self, step_exec_id: str, updates: Dict[str, Any]):
        """Update step record"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                if key == "metadata":
                    value = json.dumps(value)
                set_clauses.append(f"{key} = ?")
                values.append(value)
            
            values.append(step_exec_id)
            
            query = f"""
                UPDATE steps 
                SET {', '.join(set_clauses)}
                WHERE id = ?
            """
            
            cursor.execute(query, values)
    
    def get_task_steps(self, task_id: str) -> List[Dict[str, Any]]:
        """Get all steps for a task"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM steps 
                WHERE task_id = ?
                ORDER BY created_at ASC
            """, (task_id,))
            
            rows = cursor.fetchall()
            steps = []
            for row in rows:
                step = dict(row)
                if step.get("metadata"):
                    step["metadata"] = json.loads(step["metadata"])
                steps.append(step)
            
            return steps
    
    # =========================================================================
    # TOOL USAGE TRACKING
    # =========================================================================
    
    def log_tool_usage(self, usage_data: Dict[str, Any]):
        """Log tool usage"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO tool_usage (
                    tool_name, action, success, duration_ms,
                    error_type, step_id, task_id, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                usage_data["tool_name"],
                usage_data["action"],
                usage_data["success"],
                usage_data.get("duration_ms"),
                usage_data.get("error_type"),
                usage_data.get("step_id"),
                usage_data.get("task_id"),
                json.dumps(usage_data.get("metadata", {}))
            ))
    
    def get_tool_statistics(
        self,
        tool_name: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get tool usage statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    tool_name,
                    COUNT(*) as total_calls,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_calls,
                    AVG(duration_ms) as avg_duration_ms,
                    COUNT(DISTINCT action) as unique_actions
                FROM tool_usage
                WHERE executed_at >= datetime('now', '-' || ? || ' days')
            """
            
            params = [days]
            
            if tool_name:
                query += " AND tool_name = ?"
                params.append(tool_name)
            
            query += " GROUP BY tool_name"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            stats = {}
            for row in rows:
                row_dict = dict(row)
                tool = row_dict["tool_name"]
                stats[tool] = {
                    "total_calls": row_dict["total_calls"],
                    "successful_calls": row_dict["successful_calls"],
                    "success_rate": (
                        row_dict["successful_calls"] / row_dict["total_calls"] * 100
                        if row_dict["total_calls"] > 0 else 0
                    ),
                    "avg_duration_ms": row_dict["avg_duration_ms"],
                    "unique_actions": row_dict["unique_actions"]
                }
            
            return stats
    
    # =========================================================================
    # LEARNED PATTERNS
    # =========================================================================
    
    def save_pattern(self, pattern_data: Dict[str, Any]) -> int:
        """Save learned pattern"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO learned_patterns (
                    pattern_type, pattern_data, confidence, metadata
                ) VALUES (?, ?, ?, ?)
            """, (
                pattern_data["pattern_type"],
                json.dumps(pattern_data["pattern_data"]),
                pattern_data.get("confidence", 0.5),
                json.dumps(pattern_data.get("metadata", {}))
            ))
            
            return cursor.lastrowid
    
    def get_patterns(
        self,
        pattern_type: Optional[str] = None,
        min_confidence: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Get learned patterns"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT * FROM learned_patterns
                WHERE confidence >= ?
            """
            params = [min_confidence]
            
            if pattern_type:
                query += " AND pattern_type = ?"
                params.append(pattern_type)
            
            query += " ORDER BY confidence DESC, usage_count DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            patterns = []
            for row in rows:
                pattern = dict(row)
                pattern["pattern_data"] = json.loads(pattern["pattern_data"])
                if pattern.get("metadata"):
                    pattern["metadata"] = json.loads(pattern["metadata"])
                patterns.append(pattern)
            
            return patterns
    
    # =========================================================================
    # CLEANUP & MAINTENANCE
    # =========================================================================
    
    def cleanup_old_data(self, days: int = 90):
        """Delete data older than specified days"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cutoff = datetime.now() - timedelta(days=days)
            
            # Delete old tasks and related data
            cursor.execute("""
                DELETE FROM tasks
                WHERE created_at < ?
            """, (cutoff,))
            
            deleted_count = cursor.rowcount
            
            self.logger.info(
                "Cleaned up old data",
                days=days,
                deleted_tasks=deleted_count
            )
            
            return deleted_count
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Count records in each table
            tables = ["tasks", "steps", "tool_usage", "evaluations", "retries", "learned_patterns"]
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]
            
            # Database file size
            db_size = Path(self.db_path).stat().st_size
            stats["database_size_mb"] = db_size / (1024 * 1024)
            
            return stats


# Global storage service instance
storage_service = StorageService()


if __name__ == "__main__":
    """Test storage service"""
    print("💾 Testing Storage Service...")
    
    # Create test task
    task_id = storage_service.create_task({
        "user_goal": "Test goal",
        "status": "running"
    })
    print(f"\n✅ Task created: {task_id}")
    
    # Get task
    task = storage_service.get_task(task_id)
    print(f"   Goal: {task['user_goal']}")
    print(f"   Status: {task['status']}")
    
    # Get database stats
    stats = storage_service.get_database_stats()
    print(f"\n📊 Database stats:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ Storage service test complete")