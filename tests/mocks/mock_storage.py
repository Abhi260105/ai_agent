"""
Mock storage implementations for testing
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import copy
import threading


class MockStorage:
    """Mock storage backend for testing"""
    
    def __init__(self, persistent: bool = False):
        """
        Initialize mock storage
        
        Args:
            persistent: If True, data persists across resets (for testing)
        """
        self.persistent = persistent
        self._data: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._operations_log: List[Dict[str, Any]] = []
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value by key"""
        with self._lock:
            self._log_operation("get", {"key": key})
            return copy.deepcopy(self._data.get(key, default))
    
    def set(self, key: str, value: Any) -> bool:
        """Set value for key"""
        with self._lock:
            self._log_operation("set", {"key": key, "value_type": type(value).__name__})
            self._data[key] = copy.deepcopy(value)
            return True
    
    def delete(self, key: str) -> bool:
        """Delete key"""
        with self._lock:
            self._log_operation("delete", {"key": key})
            if key in self._data:
                del self._data[key]
                return True
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        with self._lock:
            self._log_operation("exists", {"key": key})
            return key in self._data
    
    def keys(self, pattern: str = "*") -> List[str]:
        """Get all keys matching pattern"""
        with self._lock:
            self._log_operation("keys", {"pattern": pattern})
            
            if pattern == "*":
                return list(self._data.keys())
            
            # Simple pattern matching (only supports * wildcard)
            import re
            regex_pattern = pattern.replace("*", ".*")
            regex = re.compile(regex_pattern)
            
            return [k for k in self._data.keys() if regex.match(k)]
    
    def clear(self):
        """Clear all data"""
        with self._lock:
            self._log_operation("clear", {})
            if not self.persistent:
                self._data.clear()
    
    def get_all(self) -> Dict[str, Any]:
        """Get all data (for testing)"""
        with self._lock:
            return copy.deepcopy(self._data)
    
    def get_operation_count(self) -> int:
        """Get total operation count"""
        return len(self._operations_log)
    
    def get_operation_stats(self) -> Dict[str, int]:
        """Get operation statistics"""
        stats = {}
        for op in self._operations_log:
            op_type = op["operation"]
            stats[op_type] = stats.get(op_type, 0) + 1
        return stats
    
    def reset_stats(self):
        """Reset operation tracking"""
        self._operations_log.clear()
    
    def _log_operation(self, operation: str, params: Dict[str, Any]):
        """Log an operation for testing"""
        self._operations_log.append({
            "operation": operation,
            "params": params,
            "timestamp": datetime.now().isoformat()
        })


class MockDatabase:
    """Mock database for testing"""
    
    def __init__(self):
        """Initialize mock database"""
        self._tables: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = threading.Lock()
        self._query_log: List[Dict[str, Any]] = []
        self._auto_increment: Dict[str, int] = {}
    
    def create_table(self, table_name: str, schema: Dict[str, str] = None):
        """Create a table"""
        with self._lock:
            if table_name not in self._tables:
                self._tables[table_name] = []
                self._auto_increment[table_name] = 1
                self._log_query("CREATE_TABLE", {"table": table_name, "schema": schema})
    
    def insert(
        self,
        table_name: str,
        data: Dict[str, Any],
        auto_id: bool = True
    ) -> Dict[str, Any]:
        """Insert a row"""
        with self._lock:
            if table_name not in self._tables:
                self.create_table(table_name)
            
            row = copy.deepcopy(data)
            
            if auto_id and "id" not in row:
                row["id"] = self._auto_increment[table_name]
                self._auto_increment[table_name] += 1
            
            row["_created_at"] = datetime.now().isoformat()
            
            self._tables[table_name].append(row)
            self._log_query("INSERT", {"table": table_name, "row_id": row.get("id")})
            
            return copy.deepcopy(row)
    
    def select(
        self,
        table_name: str,
        where: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Select rows"""
        with self._lock:
            if table_name not in self._tables:
                return []
            
            rows = copy.deepcopy(self._tables[table_name])
            
            # Apply filters
            if where:
                rows = [
                    row for row in rows
                    if all(row.get(k) == v for k, v in where.items())
                ]
            
            # Apply ordering
            if order_by:
                reverse = order_by.startswith("-")
                field = order_by.lstrip("-")
                rows.sort(key=lambda x: x.get(field, ""), reverse=reverse)
            
            # Apply limit
            if limit:
                rows = rows[:limit]
            
            self._log_query("SELECT", {
                "table": table_name,
                "where": where,
                "limit": limit,
                "result_count": len(rows)
            })
            
            return rows
    
    def update(
        self,
        table_name: str,
        where: Dict[str, Any],
        updates: Dict[str, Any]
    ) -> int:
        """Update rows"""
        with self._lock:
            if table_name not in self._tables:
                return 0
            
            count = 0
            for row in self._tables[table_name]:
                if all(row.get(k) == v for k, v in where.items()):
                    row.update(updates)
                    row["_updated_at"] = datetime.now().isoformat()
                    count += 1
            
            self._log_query("UPDATE", {
                "table": table_name,
                "where": where,
                "updated_count": count
            })
            
            return count
    
    def delete(
        self,
        table_name: str,
        where: Dict[str, Any]
    ) -> int:
        """Delete rows"""
        with self._lock:
            if table_name not in self._tables:
                return 0
            
            original_count = len(self._tables[table_name])
            
            self._tables[table_name] = [
                row for row in self._tables[table_name]
                if not all(row.get(k) == v for k, v in where.items())
            ]
            
            deleted = original_count - len(self._tables[table_name])
            
            self._log_query("DELETE", {
                "table": table_name,
                "where": where,
                "deleted_count": deleted
            })
            
            return deleted
    
    def count(
        self,
        table_name: str,
        where: Optional[Dict[str, Any]] = None
    ) -> int:
        """Count rows"""
        return len(self.select(table_name, where=where))
    
    def drop_table(self, table_name: str):
        """Drop a table"""
        with self._lock:
            if table_name in self._tables:
                del self._tables[table_name]
                del self._auto_increment[table_name]
                self._log_query("DROP_TABLE", {"table": table_name})
    
    def clear_all(self):
        """Clear all tables"""
        with self._lock:
            self._tables.clear()
            self._auto_increment.clear()
            self._log_query("CLEAR_ALL", {})
    
    def get_query_count(self) -> int:
        """Get total query count"""
        return len(self._query_log)
    
    def get_query_stats(self) -> Dict[str, int]:
        """Get query statistics"""
        stats = {}
        for query in self._query_log:
            query_type = query["type"]
            stats[query_type] = stats.get(query_type, 0) + 1
        return stats
    
    def reset_stats(self):
        """Reset query tracking"""
        self._query_log.clear()
    
    def _log_query(self, query_type: str, params: Dict[str, Any]):
        """Log a query for testing"""
        self._query_log.append({
            "type": query_type,
            "params": params,
            "timestamp": datetime.now().isoformat()
        })


class MockCache:
    """Mock cache implementation"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        """
        Initialize mock cache
        
        Args:
            max_size: Maximum number of items
            ttl_seconds: Time-to-live for items
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                
                # Check TTL
                age = (datetime.now() - entry["timestamp"]).total_seconds()
                if age < self.ttl_seconds:
                    self._hits += 1
                    return copy.deepcopy(entry["value"])
                else:
                    # Expired
                    del self._cache[key]
            
            self._misses += 1
            return None
    
    def set(self, key: str, value: Any):
        """Set value in cache"""
        with self._lock:
            # Implement LRU eviction if needed
            if len(self._cache) >= self.max_size and key not in self._cache:
                # Remove oldest
                oldest_key = min(
                    self._cache.keys(),
                    key=lambda k: self._cache[k]["timestamp"]
                )
                del self._cache[oldest_key]
            
            self._cache[key] = {
                "value": copy.deepcopy(value),
                "timestamp": datetime.now()
            }
    
    def delete(self, key: str) -> bool:
        """Delete from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self):
        """Clear cache"""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0
        
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "size": len(self._cache),
            "max_size": self.max_size
        }
    
    def reset_stats(self):
        """Reset statistics"""
        self._hits = 0
        self._misses = 0
