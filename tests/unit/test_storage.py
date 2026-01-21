"""
Unit tests for Storage Service.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import sqlite3


class TestStorageService:
    """Test suite for Storage Service."""
    
    @pytest.fixture
    def storage_service(self):
        """Create a Storage Service instance for testing."""
        from app.services.storage_service import StorageService
        
        # Use temporary database for testing
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        service = StorageService(db_path=temp_db.name)
        
        yield service
        
        # Cleanup
        if os.path.exists(temp_db.name):
            os.remove(temp_db.name)
    
    def test_storage_initialization(self, storage_service):
        """Test storage service initializes correctly."""
        assert storage_service is not None
        assert hasattr(storage_service, 'save')
        assert hasattr(storage_service, 'load')
        assert hasattr(storage_service, 'delete')
    
    @pytest.mark.asyncio
    async def test_save_data(self, storage_service):
        """Test saving data to storage."""
        data = {
            "id": "item_001",
            "content": "Test data",
            "metadata": {"type": "test"}
        }
        
        result = await storage_service.save("test_collection", data)
        
        assert result['status'] == 'success'
        assert 'id' in result
    
    @pytest.mark.asyncio
    async def test_load_data(self, storage_service):
        """Test loading data from storage."""
        # First save some data
        data = {
            "id": "item_001",
            "content": "Test data"
        }
        await storage_service.save("test_collection", data)
        
        # Then load it
        result = await storage_service.load("test_collection", "item_001")
        
        assert result is not None
        assert result['id'] == "item_001"
        assert result['content'] == "Test data"
    
    @pytest.mark.asyncio
    async def test_update_data(self, storage_service):
        """Test updating existing data."""
        # Save initial data
        data = {"id": "item_001", "content": "Original"}
        await storage_service.save("test_collection", data)
        
        # Update it
        updated_data = {"id": "item_001", "content": "Updated"}
        result = await storage_service.update("test_collection", "item_001", updated_data)
        
        assert result['status'] == 'success'
        
        # Verify update
        loaded = await storage_service.load("test_collection", "item_001")
        assert loaded['content'] == "Updated"
    
    @pytest.mark.asyncio
    async def test_delete_data(self, storage_service):
        """Test deleting data from storage."""
        # Save data
        data = {"id": "item_001", "content": "Test"}
        await storage_service.save("test_collection", data)
        
        # Delete it
        result = await storage_service.delete("test_collection", "item_001")
        
        assert result['status'] == 'success'
        
        # Verify deletion
        loaded = await storage_service.load("test_collection", "item_001")
        assert loaded is None
    
    @pytest.mark.asyncio
    async def test_list_items(self, storage_service):
        """Test listing items in a collection."""
        # Save multiple items
        for i in range(5):
            data = {"id": f"item_{i:03d}", "content": f"Content {i}"}
            await storage_service.save("test_collection", data)
        
        # List items
        items = await storage_service.list("test_collection")
        
        assert len(items) == 5
    
    @pytest.mark.asyncio
    async def test_query_data(self, storage_service):
        """Test querying data with filters."""
        # Save test data
        items = [
            {"id": "1", "type": "A", "value": 10},
            {"id": "2", "type": "B", "value": 20},
            {"id": "3", "type": "A", "value": 30}
        ]
        
        for item in items:
            await storage_service.save("test_collection", item)
        
        # Query for type A
        results = await storage_service.query("test_collection", {"type": "A"})
        
        assert len(results) == 2
        assert all(r['type'] == 'A' for r in results)
    
    @pytest.mark.asyncio
    async def test_bulk_save(self, storage_service):
        """Test bulk save operation."""
        items = [
            {"id": f"item_{i}", "content": f"Content {i}"}
            for i in range(10)
        ]
        
        result = await storage_service.bulk_save("test_collection", items)
        
        assert result['status'] == 'success'
        assert result['count'] == 10
    
    @pytest.mark.asyncio
    async def test_bulk_delete(self, storage_service):
        """Test bulk delete operation."""
        # Save items
        for i in range(5):
            await storage_service.save("test_collection", {"id": f"item_{i}"})
        
        # Bulk delete
        ids = ["item_0", "item_1", "item_2"]
        result = await storage_service.bulk_delete("test_collection", ids)
        
        assert result['status'] == 'success'
        assert result['deleted_count'] == 3
    
    @pytest.mark.asyncio
    async def test_transaction_commit(self, storage_service):
        """Test transaction commit."""
        async with storage_service.transaction() as txn:
            await txn.save("test_collection", {"id": "1", "content": "Test 1"})
            await txn.save("test_collection", {"id": "2", "content": "Test 2"})
            # Transaction commits automatically
        
        # Verify both items were saved
        item1 = await storage_service.load("test_collection", "1")
        item2 = await storage_service.load("test_collection", "2")
        
        assert item1 is not None
        assert item2 is not None
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, storage_service):
        """Test transaction rollback."""
        try:
            async with storage_service.transaction() as txn:
                await txn.save("test_collection", {"id": "1", "content": "Test"})
                raise Exception("Force rollback")
        except Exception:
            pass
        
        # Verify item was not saved due to rollback
        item = await storage_service.load("test_collection", "1")
        assert item is None
    
    @pytest.mark.asyncio
    async def test_pagination(self, storage_service):
        """Test paginated queries."""
        # Save 25 items
        for i in range(25):
            await storage_service.save("test_collection", {"id": f"item_{i:03d}"})
        
        # Get first page
        page1 = await storage_service.list("test_collection", limit=10, offset=0)
        assert len(page1) == 10
        
        # Get second page
        page2 = await storage_service.list("test_collection", limit=10, offset=10)
        assert len(page2) == 10
        
        # Verify different items
        assert page1[0]['id'] != page2[0]['id']
    
    @pytest.mark.asyncio
    async def test_sorting(self, storage_service):
        """Test sorting query results."""
        items = [
            {"id": "1", "value": 30},
            {"id": "2", "value": 10},
            {"id": "3", "value": 20}
        ]
        
        for item in items:
            await storage_service.save("test_collection", item)
        
        # Sort ascending
        results = await storage_service.list("test_collection", sort_by="value", sort_order="asc")
        
        assert results[0]['value'] == 10
        assert results[1]['value'] == 20
        assert results[2]['value'] == 30
    
    @pytest.mark.asyncio
    async def test_count_items(self, storage_service):
        """Test counting items in collection."""
        for i in range(7):
            await storage_service.save("test_collection", {"id": f"item_{i}"})
        
        count = await storage_service.count("test_collection")
        
        assert count == 7
    
    @pytest.mark.asyncio
    async def test_exists_check(self, storage_service):
        """Test checking if item exists."""
        await storage_service.save("test_collection", {"id": "item_001"})
        
        exists = await storage_service.exists("test_collection", "item_001")
        assert exists is True
        
        not_exists = await storage_service.exists("test_collection", "item_999")
        assert not_exists is False
    
    @pytest.mark.asyncio
    async def test_clear_collection(self, storage_service):
        """Test clearing an entire collection."""
        # Add items
        for i in range(5):
            await storage_service.save("test_collection", {"id": f"item_{i}"})
        
        # Clear collection
        result = await storage_service.clear("test_collection")
        
        assert result['status'] == 'success'
        
        # Verify collection is empty
        count = await storage_service.count("test_collection")
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_backup_database(self, storage_service):
        """Test database backup."""
        # Add some data
        await storage_service.save("test_collection", {"id": "1", "content": "Test"})
        
        # Create backup
        backup_path = await storage_service.backup()
        
        assert os.path.exists(backup_path)
        
        # Cleanup backup
        if os.path.exists(backup_path):
            os.remove(backup_path)
    
    @pytest.mark.asyncio
    async def test_restore_database(self, storage_service):
        """Test database restore."""
        # Save original data
        await storage_service.save("test_collection", {"id": "1", "content": "Original"})
        
        # Create backup
        backup_path = await storage_service.backup()
        
        # Modify data
        await storage_service.update("test_collection", "1", {"id": "1", "content": "Modified"})
        
        # Restore from backup
        await storage_service.restore(backup_path)
        
        # Verify restored
        item = await storage_service.load("test_collection", "1")
        assert item['content'] == "Original"
        
        # Cleanup
        if os.path.exists(backup_path):
            os.remove(backup_path)
    
    @pytest.mark.asyncio
    async def test_concurrent_access(self, storage_service):
        """Test concurrent access to storage."""
        import asyncio
        
        async def save_item(i):
            await storage_service.save("test_collection", {"id": f"item_{i}", "value": i})
        
        # Save 10 items concurrently
        tasks = [save_item(i) for i in range(10)]
        await asyncio.gather(*tasks)
        
        count = await storage_service.count("test_collection")
        assert count == 10
    
    @pytest.mark.asyncio
    async def test_index_creation(self, storage_service):
        """Test creating indexes for performance."""
        result = await storage_service.create_index("test_collection", "value")
        
        assert result['status'] == 'success'
    
    @pytest.mark.asyncio
    async def test_full_text_search(self, storage_service):
        """Test full-text search capability."""
        items = [
            {"id": "1", "content": "Python programming tutorial"},
            {"id": "2", "content": "JavaScript web development"},
            {"id": "3", "content": "Python data science guide"}
        ]
        
        for item in items:
            await storage_service.save("test_collection", item)
        
        # Search for Python
        results = await storage_service.search("test_collection", "Python")
        
        assert len(results) == 2
        assert all('Python' in r['content'] for r in results)
    
    @pytest.mark.asyncio
    async def test_vacuum_database(self, storage_service):
        """Test database vacuum operation."""
        # Add and delete items to create fragmentation
        for i in range(100):
            await storage_service.save("test_collection", {"id": f"item_{i}"})
        
        for i in range(50):
            await storage_service.delete("test_collection", f"item_{i}")
        
        # Vacuum
        result = await storage_service.vacuum()
        
        assert result['status'] == 'success'
    
    @pytest.mark.parametrize("data_type,value", [
        ("string", "test string"),
        ("integer", 12345),
        ("float", 123.45),
        ("boolean", True),
        ("list", [1, 2, 3]),
        ("dict", {"key": "value"})
    ])
    @pytest.mark.asyncio
    async def test_data_type_handling(self, storage_service, data_type, value):
        """Test handling of different data types."""
        data = {"id": "test", "value": value}
        
        await storage_service.save("test_collection", data)
        loaded = await storage_service.load("test_collection", "test")
        
        assert loaded['value'] == value
        assert type(loaded['value']) == type(value)