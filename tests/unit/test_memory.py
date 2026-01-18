"""
Unit tests for Memory System.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta


class TestMemorySystem:
    """Test suite for the Memory System."""
    
    @pytest.fixture
    def memory_system(self):
        """Create a Memory System instance for testing."""
        from app.core.memory import MemorySystem
        return MemorySystem()
    
    @pytest.fixture
    def sample_memory(self):
        """Sample memory item."""
        return {
            "content": "User prefers Python for backend development",
            "memory_type": "semantic",
            "importance": "high",
            "tags": ["preferences", "programming"]
        }
    
    @pytest.mark.asyncio
    async def test_store_memory(self, memory_system, sample_memory):
        """Test storing a memory item."""
        memory_id = await memory_system.store(sample_memory)
        
        assert memory_id is not None
        assert isinstance(memory_id, (int, str))
    
    @pytest.mark.asyncio
    async def test_retrieve_memory(self, memory_system, sample_memory):
        """Test retrieving a stored memory."""
        memory_id = await memory_system.store(sample_memory)
        retrieved = await memory_system.retrieve(memory_id)
        
        assert retrieved is not None
        assert retrieved['content'] == sample_memory['content']
    
    @pytest.mark.asyncio
    async def test_search_memory(self, memory_system):
        """Test searching memories by query."""
        # Store multiple memories
        await memory_system.store({
            "content": "User likes Python",
            "memory_type": "semantic",
            "importance": "medium"
        })
        await memory_system.store({
            "content": "User prefers dark theme",
            "memory_type": "semantic",
            "importance": "low"
        })
        
        results = await memory_system.search("Python programming")
        
        assert len(results) > 0
        assert any("Python" in r['content'] for r in results)
    
    @pytest.mark.asyncio
    async def test_update_memory(self, memory_system, sample_memory):
        """Test updating an existing memory."""
        memory_id = await memory_system.store(sample_memory)
        
        updates = {"importance": "critical"}
        await memory_system.update(memory_id, updates)
        
        updated = await memory_system.retrieve(memory_id)
        assert updated['importance'] == "critical"
    
    @pytest.mark.asyncio
    async def test_delete_memory(self, memory_system, sample_memory):
        """Test deleting a memory."""
        memory_id = await memory_system.store(sample_memory)
        await memory_system.delete(memory_id)
        
        retrieved = await memory_system.retrieve(memory_id)
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_memory_consolidation(self, memory_system):
        """Test consolidating related memories."""
        mem1_id = await memory_system.store({
            "content": "User completed project A",
            "memory_type": "episodic"
        })
        mem2_id = await memory_system.store({
            "content": "User completed project B",
            "memory_type": "episodic"
        })
        
        consolidated = await memory_system.consolidate([mem1_id, mem2_id])
        
        assert consolidated is not None
        assert "completed" in consolidated['content'].lower()
    
    def test_memory_importance_scoring(self, memory_system):
        """Test calculating memory importance."""
        memory = {
            "content": "Critical system error occurred",
            "access_count": 10,
            "created_at": datetime.now() - timedelta(hours=1)
        }
        
        score = memory_system.calculate_importance(memory)
        assert score > 0.7
    
    @pytest.mark.asyncio
    async def test_short_term_to_long_term(self, memory_system):
        """Test promoting short-term memory to long-term."""
        memory_id = await memory_system.store({
            "content": "Important information",
            "memory_type": "short_term",
            "importance": "high"
        })
        
        await memory_system.promote_to_long_term(memory_id)
        
        updated = await memory_system.retrieve(memory_id)
        assert updated['memory_type'] == "long_term"
    
    @pytest.mark.asyncio
    async def test_memory_decay(self, memory_system):
        """Test memory decay over time."""
        old_memory_id = await memory_system.store({
            "content": "Old information",
            "memory_type": "short_term",
            "created_at": datetime.now() - timedelta(days=30)
        })
        
        await memory_system.apply_decay()
        
        retrieved = await memory_system.retrieve(old_memory_id)
        # Should be deleted or have reduced importance
        assert retrieved is None or retrieved['importance'] == "low"
    
    @pytest.mark.asyncio
    async def test_semantic_search(self, memory_system):
        """Test semantic similarity search."""
        await memory_system.store({
            "content": "The cat sat on the mat",
            "memory_type": "semantic"
        })
        await memory_system.store({
            "content": "The dog played in the yard",
            "memory_type": "semantic"
        })
        
        results = await memory_system.search("feline on carpet", method="semantic")
        
        assert len(results) > 0
        # First result should be about cat
        assert "cat" in results[0]['content'].lower()
    
    @pytest.mark.asyncio
    async def test_filter_by_type(self, memory_system):
        """Test filtering memories by type."""
        await memory_system.store({"content": "Event A", "memory_type": "episodic"})
        await memory_system.store({"content": "Fact B", "memory_type": "semantic"})
        await memory_system.store({"content": "Event C", "memory_type": "episodic"})
        
        episodic = await memory_system.filter(memory_type="episodic")
        
        assert len(episodic) == 2
        assert all(m['memory_type'] == "episodic" for m in episodic)
    
    @pytest.mark.asyncio
    async def test_filter_by_tags(self, memory_system):
        """Test filtering memories by tags."""
        await memory_system.store({
            "content": "Python code",
            "tags": ["python", "code"]
        })
        await memory_system.store({
            "content": "JavaScript code",
            "tags": ["javascript", "code"]
        })
        
        python_memories = await memory_system.filter(tags=["python"])
        
        assert len(python_memories) >= 1
        assert any("Python" in m['content'] for m in python_memories)
    
    def test_memory_access_tracking(self, memory_system):
        """Test tracking memory access count."""
        memory = {
            "id": 1,
            "content": "Test",
            "access_count": 0
        }
        
        memory_system.track_access(memory)
        assert memory['access_count'] == 1
        
        memory_system.track_access(memory)
        assert memory['access_count'] == 2
    
    @pytest.mark.asyncio
    async def test_related_memories(self, memory_system):
        """Test finding related memories."""
        mem1_id = await memory_system.store({
            "content": "User likes Python",
            "tags": ["python", "programming"]
        })
        mem2_id = await memory_system.store({
            "content": "User knows Django",
            "tags": ["python", "framework"]
        })
        
        related = await memory_system.find_related(mem1_id)
        
        assert len(related) > 0
        assert any("Django" in r['content'] for r in related)
    
    @pytest.mark.asyncio
    async def test_memory_statistics(self, memory_system):
        """Test getting memory statistics."""
        await memory_system.store({"content": "A", "memory_type": "semantic"})
        await memory_system.store({"content": "B", "memory_type": "episodic"})
        await memory_system.store({"content": "C", "memory_type": "semantic"})
        
        stats = await memory_system.get_statistics()
        
        assert stats['total'] >= 3
        assert stats['by_type']['semantic'] >= 2
        assert stats['by_type']['episodic'] >= 1
    
    @pytest.mark.asyncio
    async def test_memory_export(self, memory_system):
        """Test exporting memories."""
        await memory_system.store({"content": "Memory 1"})
        await memory_system.store({"content": "Memory 2"})
        
        exported = await memory_system.export(format="json")
        
        assert exported is not None
        assert len(exported) >= 2
    
    @pytest.mark.asyncio
    async def test_memory_import(self, memory_system):
        """Test importing memories."""
        import_data = [
            {"content": "Imported 1", "memory_type": "semantic"},
            {"content": "Imported 2", "memory_type": "episodic"}
        ]
        
        count = await memory_system.import_memories(import_data)
        
        assert count == 2
        
        stats = await memory_system.get_statistics()
        assert stats['total'] >= 2
    
    @pytest.mark.parametrize("importance,expected_retention", [
        ("critical", True),
        ("high", True),
        ("medium", True),
        ("low", False)
    ])
    @pytest.mark.asyncio
    async def test_retention_policy(self, memory_system, importance, expected_retention):
        """Test memory retention based on importance."""
        memory_id = await memory_system.store({
            "content": "Test memory",
            "importance": importance,
            "created_at": datetime.now() - timedelta(days=90)
        })
        
        await memory_system.apply_retention_policy()
        
        retrieved = await memory_system.retrieve(memory_id)
        
        if expected_retention:
            assert retrieved is not None
        else:
            assert retrieved is None or retrieved['archived']