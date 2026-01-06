"""
Memory Manager - Agent Memory System
Manages short-term, long-term, episodic, and semantic memory
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json
import numpy as np

from app.services.storage_service import storage_service
from app.services.embedding_service import embedding_service
from app.schemas.memory_schema import (
    MemoryRecord,
    TaskExecutionMemory,
    ToolUsageMemory,
    FailureMemory,
    SuccessPatternMemory,
    MemoryQuery
)
from app.utils.logger import get_logger

logger = get_logger("agent.memory")


class MemoryManager:
    """
    Complete memory system for the agent
    
    Memory Types:
    - Short-term: Current session (RAM)
    - Long-term: Persistent storage (DB + Vector)
    - Episodic: Task execution histories
    - Semantic: Learned patterns and facts
    - Working: Active context during execution
    """
    
    def __init__(self):
        self.logger = logger
        self.storage = storage_service
        self.embeddings = embedding_service
        
        # Short-term memory (current session)
        self.short_term: Dict[str, Any] = {
            "current_task": None,
            "recent_steps": [],
            "active_context": {},
            "session_start": datetime.now()
        }
        
        # Working memory (active task context)
        self.working_memory: Dict[str, Any] = {}
        
        # Vector store for semantic search
        self.vector_store_path = Path("data/vector_store")
        self.vector_store_path.mkdir(parents=True, exist_ok=True)
        
        self._initialize_vector_store()
        
        self.logger.info("Memory manager initialized")
    
    def _initialize_vector_store(self):
        """Initialize FAISS vector store"""
        try:
            import faiss
            
            self.faiss_index_path = self.vector_store_path / "faiss_index.bin"
            self.doc_store_path = self.vector_store_path / "document_store.json"
            
            # Load or create FAISS index
            if self.faiss_index_path.exists():
                self.faiss_index = faiss.read_index(str(self.faiss_index_path))
                self.logger.info("Loaded existing FAISS index")
            else:
                # Create new index
                dimension = self.embeddings.dimension
                self.faiss_index = faiss.IndexFlatL2(dimension)
                self.logger.info("Created new FAISS index", dimension=dimension)
            
            # Load or create document store
            if self.doc_store_path.exists():
                with open(self.doc_store_path, 'r') as f:
                    self.doc_store = json.load(f)
            else:
                self.doc_store = {"documents": [], "metadata": []}
                self._save_doc_store()
            
            self.has_vector_store = True
            
        except ImportError:
            self.logger.warning("FAISS not installed, semantic search disabled")
            self.logger.info("Install with: pip install faiss-cpu")
            self.has_vector_store = False
            self.faiss_index = None
            self.doc_store = None
    
    def _save_doc_store(self):
        """Save document store to disk"""
        if self.doc_store:
            with open(self.doc_store_path, 'w') as f:
                json.dump(self.doc_store, f)
    
    def _save_vector_index(self):
        """Save FAISS index to disk"""
        if self.faiss_index and self.has_vector_store:
            import faiss
            faiss.write_index(self.faiss_index, str(self.faiss_index_path))
    
    # =========================================================================
    # SHORT-TERM MEMORY
    # =========================================================================
    
    def set_current_task(self, task_id: str, goal: str):
        """Set current task in short-term memory"""
        self.short_term["current_task"] = {
            "task_id": task_id,
            "goal": goal,
            "started_at": datetime.now()
        }
        self.logger.debug("Current task set", task_id=task_id)
    
    def add_recent_step(self, step_data: Dict[str, Any]):
        """Add step to recent history"""
        self.short_term["recent_steps"].append({
            **step_data,
            "timestamp": datetime.now()
        })
        
        # Keep only last 10 steps
        if len(self.short_term["recent_steps"]) > 10:
            self.short_term["recent_steps"] = self.short_term["recent_steps"][-10:]
    
    def get_recent_steps(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent steps from short-term memory"""
        return self.short_term["recent_steps"][-limit:]
    
    def update_working_memory(self, key: str, value: Any):
        """Update working memory"""
        self.working_memory[key] = value
    
    def get_working_memory(self, key: str) -> Optional[Any]:
        """Get from working memory"""
        return self.working_memory.get(key)
    
    def clear_working_memory(self):
        """Clear working memory"""
        self.working_memory.clear()
    
    # =========================================================================
    # LONG-TERM MEMORY (Episodic)
    # =========================================================================
    
    def store_task_memory(self, task_data: Dict[str, Any]):
        """
        Store task execution in long-term memory
        
        Args:
            task_data: Task execution data
        """
        # Store in database
        task_id = self.storage.create_task(task_data)
        
        # Create memory record
        memory = TaskExecutionMemory(
            content={
                "goal": task_data["user_goal"],
                "plan_id": task_data.get("plan_id"),
                "steps_completed": task_data.get("steps_completed", []),
                "steps_failed": task_data.get("steps_failed", []),
                "total_duration_seconds": task_data.get("duration_seconds", 0),
                "success": task_data.get("status") == "completed",
                "outcome": task_data.get("outcome", "")
            },
            tags=self._extract_tags(task_data["user_goal"])
        )
        
        # Add to vector store for semantic search
        if self.has_vector_store:
            self._add_to_vector_store(
                text=task_data["user_goal"],
                memory_record=memory,
                memory_type="task"
            )
        
        self.logger.info("Task memory stored", task_id=task_id)
        return task_id
    
    def store_failure_memory(self, failure_data: Dict[str, Any]):
        """Store failure for learning"""
        memory = FailureMemory(
            content={
                "step_id": failure_data["step_id"],
                "tool_name": failure_data["tool_name"],
                "error_type": failure_data["error_type"],
                "error_message": failure_data["error_message"],
                "attempted_action": failure_data["action"],
                "resolution": failure_data.get("resolution", ""),
                "preventable": failure_data.get("preventable", False)
            },
            tags=["failure", failure_data["tool_name"], failure_data["error_type"]]
        )
        
        # Add to vector store
        if self.has_vector_store:
            failure_text = f"Failed: {failure_data['action']} - {failure_data['error_message']}"
            self._add_to_vector_store(failure_text, memory, "failure")
        
        self.logger.info("Failure memory stored", step_id=failure_data["step_id"])
    
    def store_success_pattern(self, pattern_data: Dict[str, Any]):
        """Store successful pattern"""
        memory = SuccessPatternMemory(
            content={
                "goal_type": pattern_data["goal_type"],
                "approach": pattern_data["approach"],
                "tools_used": pattern_data["tools_used"],
                "key_steps": pattern_data["key_steps"],
                "success_rate": pattern_data.get("success_rate", 1.0)
            },
            tags=["success", pattern_data["goal_type"]]
        )
        
        # Store in database as learned pattern
        self.storage.save_pattern({
            "pattern_type": "success_pattern",
            "pattern_data": pattern_data,
            "confidence": pattern_data.get("success_rate", 1.0)
        })
        
        # Add to vector store
        if self.has_vector_store:
            pattern_text = f"Success: {pattern_data['goal_type']} using {', '.join(pattern_data['tools_used'])}"
            self._add_to_vector_store(pattern_text, memory, "success")
        
        self.logger.info("Success pattern stored", goal_type=pattern_data["goal_type"])
    
    # =========================================================================
    # SEMANTIC MEMORY (Retrieval)
    # =========================================================================
    
    def retrieve_similar_tasks(
        self,
        query: str,
        limit: int = 5,
        min_similarity: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve similar past tasks using semantic search
        
        Args:
            query: Query text
            limit: Maximum results
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of similar task memories
        """
        if not self.has_vector_store:
            self.logger.warning("Vector store not available")
            return []
        
        try:
            # Generate query embedding
            query_emb = self.embeddings.embed(query)
            
            # Search FAISS index
            query_emb_2d = np.array([query_emb])
            distances, indices = self.faiss_index.search(query_emb_2d, limit * 2)
            
            # Filter by similarity and collect results
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx == -1:  # FAISS returns -1 for empty slots
                    continue
                
                # Convert L2 distance to similarity
                similarity = 1 / (1 + dist)
                
                if similarity < min_similarity:
                    continue
                
                # Get document from store
                if idx < len(self.doc_store["documents"]):
                    doc = self.doc_store["documents"][idx]
                    metadata = self.doc_store["metadata"][idx]
                    
                    results.append({
                        "text": doc,
                        "similarity": float(similarity),
                        "memory_type": metadata.get("memory_type"),
                        "timestamp": metadata.get("timestamp")
                    })
            
            # Sort by similarity
            results.sort(key=lambda x: x["similarity"], reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            self.logger.error(f"Semantic search failed: {e}")
            return []
    
    def retrieve_failures_by_type(
        self,
        error_type: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve past failures of specific type"""
        # Query from vector store
        query = f"failure {error_type}"
        similar = self.retrieve_similar_tasks(query, limit=limit)
        
        # Filter for failures only
        failures = [s for s in similar if s.get("memory_type") == "failure"]
        
        return failures
    
    def retrieve_success_patterns(
        self,
        goal_type: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve successful patterns for goal type"""
        # Get from database
        patterns = self.storage.get_patterns(
            pattern_type="success_pattern",
            min_confidence=0.5
        )
        
        # Filter by goal type
        matching = [
            p for p in patterns
            if goal_type.lower() in p["pattern_data"].get("goal_type", "").lower()
        ]
        
        return matching[:limit]
    
    def _add_to_vector_store(
        self,
        text: str,
        memory_record: MemoryRecord,
        memory_type: str
    ):
        """Add memory to vector store"""
        if not self.has_vector_store:
            return
        
        try:
            # Generate embedding
            embedding = self.embeddings.embed(text)
            
            # Add to FAISS index
            embedding_2d = np.array([embedding])
            self.faiss_index.add(embedding_2d)
            
            # Add to document store
            self.doc_store["documents"].append(text)
            self.doc_store["metadata"].append({
                "memory_type": memory_type,
                "memory_id": memory_record.id,
                "timestamp": datetime.now().isoformat(),
                "tags": memory_record.tags
            })
            
            # Save periodically (every 10 additions)
            if len(self.doc_store["documents"]) % 10 == 0:
                self._save_doc_store()
                self._save_vector_index()
            
        except Exception as e:
            self.logger.error(f"Failed to add to vector store: {e}")
    
    def _extract_tags(self, text: str) -> List[str]:
        """Extract tags from text"""
        # Simple keyword extraction
        keywords = ["email", "calendar", "meeting", "file", "search", "schedule"]
        tags = [kw for kw in keywords if kw in text.lower()]
        return tags if tags else ["general"]
    
    # =========================================================================
    # MEMORY CONSOLIDATION
    # =========================================================================
    
    def consolidate_memories(self):
        """
        Consolidate short-term memories to long-term
        Called at end of session or periodically
        """
        self.logger.info("Consolidating memories")
        
        # Save recent steps as episodic memory
        for step in self.short_term["recent_steps"]:
            # Already saved during execution
            pass
        
        # Update memory statistics
        # Decay old memory relevance
        # Merge similar memories
        
        # Save vector store
        if self.has_vector_store:
            self._save_doc_store()
            self._save_vector_index()
        
        self.logger.info("Memory consolidation complete")
    
    def cleanup_old_memories(self, days: int = 90):
        """Remove memories older than specified days"""
        self.storage.cleanup_old_data(days=days)
        self.logger.info("Old memories cleaned up", days=days)
    
    # =========================================================================
    # STATISTICS
    # =========================================================================
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        stats = {
            "short_term": {
                "recent_steps": len(self.short_term["recent_steps"]),
                "session_duration_minutes": (
                    datetime.now() - self.short_term["session_start"]
                ).total_seconds() / 60
            },
            "working_memory": {
                "active_keys": len(self.working_memory)
            },
            "long_term": self.storage.get_database_stats(),
            "vector_store": {
                "enabled": self.has_vector_store,
                "documents": len(self.doc_store["documents"]) if self.doc_store else 0
            }
        }
        
        if self.has_vector_store and self.faiss_index:
            stats["vector_store"]["index_size"] = self.faiss_index.ntotal
        
        return stats


# Global memory manager instance
memory_manager = MemoryManager()


if __name__ == "__main__":
    """Test memory manager"""
    print("🧠 Testing Memory Manager...")
    
    # Test short-term memory
    print("\n📝 Testing short-term memory...")
    memory_manager.set_current_task("task_1", "Test goal")
    memory_manager.add_recent_step({
        "step_id": "step_1",
        "action": "test_action",
        "status": "success"
    })
    recent = memory_manager.get_recent_steps(limit=5)
    print(f"   Recent steps: {len(recent)}")
    
    # Test task memory storage
    print("\n💾 Testing task memory storage...")
    task_id = memory_manager.store_task_memory({
        "user_goal": "Send email to team about meeting",
        "status": "completed",
        "steps_completed": ["step_1", "step_2"],
        "duration_seconds": 10.5
    })
    print(f"   Task stored: {task_id}")
    
    # Test semantic search
    print("\n🔍 Testing semantic search...")
    similar = memory_manager.retrieve_similar_tasks(
        query="email task",
        limit=3
    )
    print(f"   Similar tasks found: {len(similar)}")
    
    # Test memory stats
    print("\n📊 Memory statistics:")
    stats = memory_manager.get_memory_stats()
    print(f"   Short-term steps: {stats['short_term']['recent_steps']}")
    print(f"   Long-term tasks: {stats['long_term'].get('tasks_count', 0)}")
    print(f"   Vector store docs: {stats['vector_store']['documents']}")
    
    print("\n✅ Memory manager test complete")