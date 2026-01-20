"""
Unit tests for File Tool.
"""

import pytest
from unittest.mock import Mock, patch, mock_open, MagicMock
import tempfile
import os


class TestFileTool:
    """Test suite for File Tool."""
    
    @pytest.fixture
    def file_tool(self):
        """Create a FileTool instance for testing."""
        from app.tools.file_tool import FileTool
        return FileTool()
    
    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Test content\nLine 2\nLine 3")
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    def test_file_tool_initialization(self, file_tool):
        """Test file tool initializes correctly."""
        assert file_tool is not None
        assert file_tool.name == "file_tool"
        assert hasattr(file_tool, 'read_file')
        assert hasattr(file_tool, 'write_file')
    
    @pytest.mark.asyncio
    async def test_read_text_file(self, file_tool, temp_file):
        """Test reading a text file."""
        params = {"filepath": temp_file}
        
        result = await file_tool.read_file(params)
        
        assert result['status'] == 'success'
        assert 'Test content' in result['content']
        assert result['lines'] == 3
    
    @pytest.mark.asyncio
    async def test_write_text_file(self, file_tool):
        """Test writing to a text file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
        
        try:
            params = {
                "filepath": temp_path,
                "content": "New content here",
                "mode": "write"
            }
            
            result = await file_tool.write_file(params)
            
            assert result['status'] == 'success'
            
            # Verify content was written
            with open(temp_path, 'r') as f:
                content = f.read()
                assert content == "New content here"
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    @pytest.mark.asyncio
    async def test_append_to_file(self, file_tool, temp_file):
        """Test appending to an existing file."""
        params = {
            "filepath": temp_file,
            "content": "\nAppended line",
            "mode": "append"
        }
        
        result = await file_tool.write_file(params)
        
        assert result['status'] == 'success'
        
        # Verify append
        with open(temp_file, 'r') as f:
            content = f.read()
            assert 'Appended line' in content
    
    @pytest.mark.asyncio
    async def test_read_csv_file(self, file_tool):
        """Test reading a CSV file."""
        csv_content = "name,age,city\nAlice,30,NYC\nBob,25,LA"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name
        
        try:
            params = {"filepath": temp_path, "format": "csv"}
            
            result = await file_tool.read_file(params)
            
            assert result['status'] == 'success'
            assert result['format'] == 'csv'
            assert len(result['rows']) == 2
            assert result['headers'] == ['name', 'age', 'city']
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    @pytest.mark.asyncio
    async def test_read_json_file(self, file_tool):
        """Test reading a JSON file."""
        json_content = '{"name": "Alice", "age": 30, "city": "NYC"}'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(json_content)
            temp_path = f.name
        
        try:
            params = {"filepath": temp_path, "format": "json"}
            
            result = await file_tool.read_file(params)
            
            assert result['status'] == 'success'
            assert result['data']['name'] == 'Alice'
            assert result['data']['age'] == 30
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    @pytest.mark.asyncio
    async def test_file_not_found(self, file_tool):
        """Test handling of non-existent file."""
        params = {"filepath": "/nonexistent/file.txt"}
        
        result = await file_tool.read_file(params)
        
        assert result['status'] == 'error'
        assert 'not found' in result['error'].lower()
    
    @pytest.mark.asyncio
    async def test_invalid_file_extension(self, file_tool):
        """Test handling of unsupported file type."""
        params = {"filepath": "file.exe"}
        
        result = await file_tool.read_file(params)
        
        assert result['status'] == 'error'
        assert 'not supported' in result['error'].lower() or 'invalid' in result['error'].lower()
    
    @pytest.mark.asyncio
    async def test_file_size_limit(self, file_tool):
        """Test file size validation."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            # Write large content
            f.write('x' * (15 * 1024 * 1024))  # 15 MB
            temp_path = f.name
        
        try:
            params = {"filepath": temp_path}
            
            result = await file_tool.read_file(params)
            
            assert result['status'] == 'error'
            assert 'size' in result['error'].lower()
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    @pytest.mark.asyncio
    async def test_list_files_in_directory(self, file_tool):
        """Test listing files in a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            for i in range(3):
                with open(os.path.join(temp_dir, f'file{i}.txt'), 'w') as f:
                    f.write(f'Content {i}')
            
            params = {"directory": temp_dir}
            
            result = await file_tool.list_files(params)
            
            assert result['status'] == 'success'
            assert len(result['files']) == 3
    
    @pytest.mark.asyncio
    async def test_delete_file(self, file_tool):
        """Test deleting a file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        params = {"filepath": temp_path}
        
        result = await file_tool.delete_file(params)
        
        assert result['status'] == 'success'
        assert not os.path.exists(temp_path)
    
    @pytest.mark.asyncio
    async def test_copy_file(self, file_tool, temp_file):
        """Test copying a file."""
        dest_path = temp_file + '.copy'
        
        try:
            params = {
                "source": temp_file,
                "destination": dest_path
            }
            
            result = await file_tool.copy_file(params)
            
            assert result['status'] == 'success'
            assert os.path.exists(dest_path)
            
            # Verify content matches
            with open(temp_file, 'r') as f1, open(dest_path, 'r') as f2:
                assert f1.read() == f2.read()
        finally:
            if os.path.exists(dest_path):
                os.remove(dest_path)
    
    @pytest.mark.asyncio
    async def test_move_file(self, file_tool):
        """Test moving/renaming a file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'Test content')
            source_path = f.name
        
        dest_path = source_path + '.moved'
        
        try:
            params = {
                "source": source_path,
                "destination": dest_path
            }
            
            result = await file_tool.move_file(params)
            
            assert result['status'] == 'success'
            assert not os.path.exists(source_path)
            assert os.path.exists(dest_path)
        finally:
            if os.path.exists(dest_path):
                os.remove(dest_path)
    
    @pytest.mark.asyncio
    async def test_get_file_info(self, file_tool, temp_file):
        """Test getting file metadata."""
        params = {"filepath": temp_file}
        
        result = await file_tool.get_file_info(params)
        
        assert result['status'] == 'success'
        assert 'size' in result
        assert 'modified' in result
        assert 'created' in result
        assert result['extension'] == os.path.splitext(temp_file)[1]
    
    @pytest.mark.asyncio
    async def test_search_in_file(self, file_tool, temp_file):
        """Test searching for text in a file."""
        params = {
            "filepath": temp_file,
            "pattern": "Test"
        }
        
        result = await file_tool.search_in_file(params)
        
        assert result['status'] == 'success'
        assert len(result['matches']) > 0
        assert result['matches'][0]['line_number'] == 1
    
    @pytest.mark.asyncio
    async def test_create_directory(self, file_tool):
        """Test creating a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir = os.path.join(temp_dir, 'new_folder')
            
            params = {"directory": new_dir}
            
            result = await file_tool.create_directory(params)
            
            assert result['status'] == 'success'
            assert os.path.exists(new_dir)
            assert os.path.isdir(new_dir)
    
    @pytest.mark.asyncio
    async def test_read_lines_range(self, file_tool, temp_file):
        """Test reading specific lines from a file."""
        params = {
            "filepath": temp_file,
            "start_line": 1,
            "end_line": 2
        }
        
        result = await file_tool.read_file(params)
        
        assert result['status'] == 'success'
        assert result['lines_read'] == 2
    
    @pytest.mark.asyncio
    async def test_file_encoding(self, file_tool):
        """Test handling different file encodings."""
        content = "Hello 世界"
        
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            params = {
                "filepath": temp_path,
                "encoding": "utf-8"
            }
            
            result = await file_tool.read_file(params)
            
            assert result['status'] == 'success'
            assert "世界" in result['content']
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    @pytest.mark.asyncio
    async def test_permission_error(self, file_tool):
        """Test handling of permission errors."""
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            params = {"filepath": "/protected/file.txt"}
            
            result = await file_tool.read_file(params)
            
            assert result['status'] == 'error'
            assert 'permission' in result['error'].lower()
    
    @pytest.mark.parametrize("file_type,content,expected_format", [
        ('.txt', 'plain text', 'text'),
        ('.csv', 'a,b,c', 'csv'),
        ('.json', '{"key": "value"}', 'json'),
        ('.md', '# Markdown', 'markdown')
    ])
    @pytest.mark.asyncio
    async def test_file_type_detection(self, file_tool, file_type, content, expected_format):
        """Test automatic file type detection."""
        with tempfile.NamedTemporaryFile(mode='w', suffix=file_type, delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            params = {"filepath": temp_path}
            
            detected_format = file_tool.detect_format(temp_path)
            assert detected_format == expected_format
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)