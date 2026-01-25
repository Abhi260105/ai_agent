"""
Memory Generation Module
Handles memory creation, storage, and retrieval for the application.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from dataclasses import dataclass, asdict
from enum import Enum


class MemoryType(Enum):
    """Types of memories that can be generated."""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


@dataclass
class Memory:
    """Represents a single memory entry."""
    id: str
    content: str
    memory_type: MemoryType
    timestamp: datetime
    metadata: Dict[str, Any]
    importance: float  # 0.0 to 1.0
    tags: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert memory to dictionary format."""
        return {
            'id': self.id,
            'content': self.content,
            'memory_type': self.memory_type.value,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
            'importance': self.importance,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Memory':
        """Create memory from dictionary."""
        return cls(
            id=data['id'],
            content=data['content'],
            memory_type=MemoryType(data['memory_type']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            metadata=data.get('metadata', {}),
            importance=data.get('importance', 0.5),
            tags=data.get('tags', [])
        )


class MemoryGenerator:
    """Generates and manages memories."""
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or "memories.json"
        self.memories: Dict[str, Memory] = {}
        self._load_memories()
    
    def generate_memory(
        self,
        content: str,
        memory_type: MemoryType,
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Memory:
        """
        Generate a new memory entry.
        
        Args:
            content: The memory content
            memory_type: Type of memory
            importance: Importance score (0.0 to 1.0)
            tags: Optional tags for categorization
            metadata: Additional metadata
            
        Returns:
            Generated Memory object
        """
        memory_id = self._generate_id()
        
        memory = Memory(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            timestamp=datetime.now(),
            metadata=metadata or {},
            importance=max(0.0, min(1.0, importance)),
            tags=tags or []
        )
        
        self.memories[memory_id] = memory
        self._save_memories()
        
        return memory
    
    def retrieve_memories(
        self,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[List[str]] = None,
        min_importance: float = 0.0,
        limit: Optional[int] = None
    ) -> List[Memory]:
        """
        Retrieve memories based on filters.
        
        Args:
            memory_type: Filter by memory type
            tags: Filter by tags (any match)
            min_importance: Minimum importance threshold
            limit: Maximum number of results
            
        Returns:
            List of matching memories
        """
        results = []
        
        for memory in self.memories.values():
            # Apply filters
            if memory_type and memory.memory_type != memory_type:
                continue
            
            if tags and not any(tag in memory.tags for tag in tags):
                continue
            
            if memory.importance < min_importance:
                continue
            
            results.append(memory)
        
        # Sort by importance and timestamp
        results.sort(key=lambda m: (m.importance, m.timestamp), reverse=True)
        
        if limit:
            results = results[:limit]
        
        return results
    
    def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        importance: Optional[float] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update an existing memory.
        
        Args:
            memory_id: ID of memory to update
            content: New content (optional)
            importance: New importance (optional)
            tags: New tags (optional)
            metadata: New metadata (optional)
            
        Returns:
            True if update successful, False otherwise
        """
        if memory_id not in self.memories:
            return False
        
        memory = self.memories[memory_id]
        
        if content is not None:
            memory.content = content
        
        if importance is not None:
            memory.importance = max(0.0, min(1.0, importance))
        
        if tags is not None:
            memory.tags = tags
        
        if metadata is not None:
            memory.metadata.update(metadata)
        
        self._save_memories()
        return True
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        if memory_id in self.memories:
            del self.memories[memory_id]
            self._save_memories()
            return True
        return False
    
    def consolidate_memories(self, threshold: float = 0.3) -> int:
        """
        Remove low-importance memories below threshold.
        
        Args:
            threshold: Importance threshold
            
        Returns:
            Number of memories removed
        """
        to_remove = [
            mid for mid, mem in self.memories.items()
            if mem.importance < threshold
        ]
        
        for mid in to_remove:
            del self.memories[mid]
        
        if to_remove:
            self._save_memories()
        
        return len(to_remove)
    
    def _generate_id(self) -> str:
        """Generate unique memory ID."""
        timestamp = datetime.now().timestamp()
        return f"mem_{int(timestamp * 1000000)}"
    
    def _load_memories(self):
        """Load memories from storage."""
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                self.memories = {
                    mid: Memory.from_dict(mdata)
                    for mid, mdata in data.items()
                }
        except FileNotFoundError:
            self.memories = {}
    
    def _save_memories(self):
        """Save memories to storage."""
        data = {
            mid: mem.to_dict()
            for mid, mem in self.memories.items()
        }
        
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get memory statistics."""
        if not self.memories:
            return {
                'total': 0,
                'by_type': {},
                'avg_importance': 0.0
            }
        
        by_type = {}
        total_importance = 0.0
        
        for mem in self.memories.values():
            mem_type = mem.memory_type.value
            by_type[mem_type] = by_type.get(mem_type, 0) + 1
            total_importance += mem.importance
        
        return {
            'total': len(self.memories),
            'by_type': by_type,
            'avg_importance': total_importance / len(self.memories)
        }


# Example usage
if __name__ == "__main__":
    # Initialize memory generator
    gen = MemoryGenerator()
    
    # Generate some memories
    gen.generate_memory(
        "User prefers dark mode",
        MemoryType.LONG_TERM,
        importance=0.8,
        tags=["preference", "ui"]
    )
    
    gen.generate_memory(
        "Completed tutorial at 2pm",
        MemoryType.EPISODIC,
        importance=0.5,
        tags=["tutorial", "event"]
    )
    
    # Retrieve memories
    prefs = gen.retrieve_memories(tags=["preference"])
    print(f"Found {len(prefs)} preference memories")
    
    # Get statistics
    stats = gen.get_statistics()
    print(f"Total memories: {stats['total']}")
    print(f"By type: {stats['by_type']}")