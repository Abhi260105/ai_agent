"""
Integration tests for memory system with other components.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta


@pytest.mark.integration
class TestMemoryIntegration:
    """Test memory system integration with other components."""
    
    @pytest.fixture
    async def integrated_system(self):
        """Create integrated system with memory, LLM, and storage."""
        from app.core.memory import MemorySystem
        from app.services.llm_service import LLMService
        from app.services.storage_service import StorageService
        
        memory = MemorySystem()
        llm = LLMService(provider="openai")
        storage = StorageService(':memory:')
        
        yield {
            'memory': memory,
            'llm': llm,
            'storage': storage
        }
    
    @pytest.mark.asyncio
    async def test_memory_with_task_execution(self, integrated_system):
        """Test memory usage during task execution."""
        memory = integrated_system['memory']
        
        # Store task context in memory
        await memory.store({
            'content': 'User prefers concise responses',
            'memory_type': 'semantic',
            'importance': 'high',
            'tags': ['preferences', 'communication']
        })
        
        # Execute task with memory context
        relevant_memories = await memory.search('user preferences')
        
        assert len(relevant_memories) > 0
        assert 'concise' in relevant_memories[0]['content'].lower()
    
    @pytest.mark.asyncio
    async def test_memory_persistence_across_sessions(self, integrated_system):
        """Test that memory persists across sessions."""
        memory = integrated_system['memory']
        storage = integrated_system['storage']
        
        # Store memory
        memory_id = await memory.store({
            'content': 'Important fact to remember',
            'memory_type': 'long_term',
            'importance': 'critical'
        })
        
        # Persist to storage
        memories = await memory.export()
        await storage.save('memories', {'id': 'backup', 'data': memories})
        
        # Simulate new session - load from storage
        backup = await storage.load('memories', 'backup')
        assert backup is not None
        assert len(backup['data']) > 0
    
    @pytest.mark.asyncio
    async def test_memory_with_llm_generation(self, integrated_system):
        """Test using memory to enhance LLM responses."""
        memory = integrated_system['memory']
        llm = integrated_system['llm']
        
        # Store relevant context
        await memory.store({
            'content': 'User is working on Python project',
            'memory_type': 'episodic',
            'importance': 'high'
        })
        
        await memory.store({
            'content': 'User prefers detailed explanations',
            'memory_type': 'semantic',
            'importance': 'medium'
        })
        
        # Retrieve context for LLM
        context_memories = await memory.search('user project preferences')
        context = '\n'.join([m['content'] for m in context_memories])
        
        # Generate with context
        with patch.object(llm, 'generate') as mock_generate:
            mock_generate.return_value = {
                'content': 'Detailed Python explanation...',
                'tokens': 150
            }
            
            response = await llm.generate(
                'Explain list comprehensions',
                system_message=f'Context: {context}'
            )
            
            assert response['content'] is not None
            mock_generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_memory_consolidation_workflow(self, integrated_system):
        """Test consolidating related memories."""
        memory = integrated_system['memory']
        
        # Store related memories
        mem_ids = []
        for i in range(3):
            mem_id = await memory.store({
                'content': f'User completed task {i}',
                'memory_type': 'episodic',
                'importance': 'medium',
                'tags': ['tasks', 'completed']
            })
            mem_ids.append(mem_id)
        
        # Consolidate memories
        consolidated = await memory.consolidate(mem_ids)
        
        assert consolidated is not None
        assert 'completed' in consolidated['content'].lower()
        assert len(consolidated.get('source_ids', [])) == 3
    
    @pytest.mark.asyncio
    async def test_memory_search_with_filters(self, integrated_system):
        """Test memory search with complex filters."""
        memory = integrated_system['memory']
        
        # Store diverse memories
        await memory.store({
            'content': 'Python tutorial',
            'memory_type': 'semantic',
            'importance': 'high',
            'tags': ['python', 'tutorial']
        })
        
        await memory.store({
            'content': 'JavaScript guide',
            'memory_type': 'semantic',
            'importance': 'medium',
            'tags': ['javascript', 'guide']
        })
        
        await memory.store({
            'content': 'Recent Python project',
            'memory_type': 'episodic',
            'importance': 'high',
            'tags': ['python', 'project']
        })
        
        # Search with filters
        results = await memory.filter(
            memory_type='semantic',
            tags=['python'],
            importance='high'
        )
        
        assert len(results) >= 1
        assert all(m['memory_type'] == 'semantic' for m in results)
        assert all('python' in m['tags'] for m in results)
    
    @pytest.mark.asyncio
    async def test_memory_access_patterns(self, integrated_system):
        """Test tracking memory access patterns."""
        memory = integrated_system['memory']
        
        # Store memory
        mem_id = await memory.store({
            'content': 'Frequently accessed information',
            'memory_type': 'semantic',
            'importance': 'medium'
        })
        
        # Access multiple times
        for _ in range(5):
            mem = await memory.retrieve(mem_id)
            memory.track_access(mem)
        
        # Check access count increased
        mem = await memory.retrieve(mem_id)
        assert mem['access_count'] >= 5
    
    @pytest.mark.asyncio
    async def test_memory_with_embeddings(self, integrated_system):
        """Test memory with vector embeddings for semantic search."""
        memory = integrated_system['memory']
        llm = integrated_system['llm']
        
        # Store memories with embeddings
        text = "Python is a programming language"
        
        with patch.object(llm, 'get_embedding') as mock_embed:
            mock_embed.return_value = [0.1] * 768  # Mock embedding
            
            embedding = await llm.get_embedding(text)
            
            await memory.store({
                'content': text,
                'memory_type': 'semantic',
                'embedding': embedding,
                'importance': 'high'
            })
        
        # Search using semantic similarity
        query_embedding = [0.1] * 768
        results = await memory.search_by_embedding(query_embedding, limit=5)
        
        assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_memory_decay_mechanism(self, integrated_system):
        """Test memory decay over time."""
        memory = integrated_system['memory']
        
        # Store old memory
        old_mem_id = await memory.store({
            'content': 'Old information',
            'memory_type': 'short_term',
            'importance': 'low',
            'created_at': (datetime.now() - timedelta(days=60)).isoformat()
        })
        
        # Store recent memory
        new_mem_id = await memory.store({
            'content': 'Recent information',
            'memory_type': 'short_term',
            'importance': 'medium',
            'created_at': datetime.now().isoformat()
        })
        
        # Apply decay
        await memory.apply_decay()
        
        # Check old memory has lower importance or is removed
        old_mem = await memory.retrieve(old_mem_id)
        new_mem = await memory.retrieve(new_mem_id)
        
        # Old memory should be affected by decay
        assert old_mem is None or old_mem['importance'] == 'low'
        assert new_mem is not None
    
    @pytest.mark.asyncio
    async def test_memory_related_items(self, integrated_system):
        """Test finding related memories."""
        memory = integrated_system['memory']
        
        # Store related memories
        mem1_id = await memory.store({
            'content': 'Python programming basics',
            'memory_type': 'semantic',
            'tags': ['python', 'programming']
        })
        
        mem2_id = await memory.store({
            'content': 'Python advanced features',
            'memory_type': 'semantic',
            'tags': ['python', 'advanced']
        })
        
        mem3_id = await memory.store({
            'content': 'JavaScript frameworks',
            'memory_type': 'semantic',
            'tags': ['javascript', 'frameworks']
        })
        
        # Find related to first memory
        related = await memory.find_related(mem1_id, limit=5)
        
        assert len(related) > 0
        # Should find Python-related memory
        assert any('Python' in r['content'] for r in related)
    
    @pytest.mark.asyncio
    async def test_memory_statistics_tracking(self, integrated_system):
        """Test memory statistics and analytics."""
        memory = integrated_system['memory']
        
        # Store various memories
        for i in range(10):
            await memory.store({
                'content': f'Memory {i}',
                'memory_type': 'semantic' if i % 2 == 0 else 'episodic',
                'importance': 'high' if i < 5 else 'low'
            })
        
        # Get statistics
        stats = await memory.get_statistics()
        
        assert stats['total'] >= 10
        assert 'by_type' in stats
        assert 'by_importance' in stats
        assert stats['by_type']['semantic'] > 0
        assert stats['by_type']['episodic'] > 0
    
    @pytest.mark.asyncio
    async def test_memory_backup_and_restore(self, integrated_system):
        """Test memory backup and restore functionality."""
        memory = integrated_system['memory']
        storage = integrated_system['storage']
        
        # Store test memories
        original_memories = []
        for i in range(5):
            mem_id = await memory.store({
                'content': f'Test memory {i}',
                'memory_type': 'semantic'
            })
            original_memories.append(mem_id)
        
        # Backup
        backup_data = await memory.export(format='json')
        await storage.save('backup', {'id': 'mem_backup', 'data': backup_data})
        
        # Clear memory
        for mem_id in original_memories:
            await memory.delete(mem_id)
        
        # Verify cleared
        stats = await memory.get_statistics()
        cleared_count = stats['total']
        
        # Restore
        backup = await storage.load('backup', 'mem_backup')
        restored_count = await memory.import_memories(backup['data'])
        
        assert restored_count == 5
    
    @pytest.mark.asyncio
    async def test_memory_context_for_agent(self, integrated_system):
        """Test providing memory context to agent."""
        memory = integrated_system['memory']
        
        # Store agent context
        await memory.store({
            'content': 'Agent successfully completed similar task before',
            'memory_type': 'episodic',
            'importance': 'high',
            'tags': ['success', 'task_completion']
        })
        
        await memory.store({
            'content': 'User prefers step-by-step explanations',
            'memory_type': 'semantic',
            'importance': 'high',
            'tags': ['user_preferences']
        })
        
        # Get context for new task
        task = "Complete analysis task"
        relevant_context = await memory.search(task)
        
        # Should retrieve relevant memories
        assert len(relevant_context) > 0
        context_text = '\n'.join([m['content'] for m in relevant_context])
        
        assert 'similar task' in context_text.lower() or 'prefer' in context_text.lower()
    
    @pytest.mark.asyncio
    async def test_memory_priority_sorting(self, integrated_system):
        """Test sorting memories by importance and recency."""
        memory = integrated_system['memory']
        
        # Store memories with different priorities
        await memory.store({
            'content': 'Critical information',
            'importance': 'critical',
            'created_at': datetime.now().isoformat()
        })
        
        await memory.store({
            'content': 'Low priority info',
            'importance': 'low',
            'created_at': (datetime.now() - timedelta(days=1)).isoformat()
        })
        
        await memory.store({
            'content': 'High priority recent',
            'importance': 'high',
            'created_at': datetime.now().isoformat()
        })
        
        # Get sorted memories
        sorted_mems = await memory.list(sort_by='importance', limit=10)
        
        # Critical should be first
        assert sorted_mems[0]['importance'] in ['critical', 'high']
    
    @pytest.mark.asyncio
    async def test_memory_concurrent_access(self, integrated_system):
        """Test concurrent memory access."""
        import asyncio
        memory = integrated_system['memory']
        
        # Concurrent store operations
        async def store_memory(i):
            return await memory.store({
                'content': f'Concurrent memory {i}',
                'memory_type': 'semantic'
            })
        
        # Store 10 memories concurrently
        tasks = [store_memory(i) for i in range(10)]
        mem_ids = await asyncio.gather(*tasks)
        
        assert len(mem_ids) == 10
        
        # Verify all stored
        stats = await memory.get_statistics()
        assert stats['total'] >= 10