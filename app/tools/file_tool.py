"""
File Tool - File System Operations
Provides safe file reading, writing, and management
Includes cloud storage support (S3) and content extraction
"""
from typing import Dict, Any, Optional, List
from pathlib import Path
import os
import shutil
import mimetypes
from datetime import datetime

from app.tools.base_tool import BaseTool
from app.schemas.tool_schema import ToolInput, ToolResult, ToolCapability
from app.config import config
from app.utils.logger import get_logger

logger = get_logger("tools.file")


class FileTool(BaseTool):
    """
    File system operations with security
    
    Supported actions:
    - read: Read file contents
    - write: Write/create file
    - append: Append to file
    - delete: Delete file
    - list: List directory contents
    - exists: Check if file exists
    - info: Get file metadata
    - extract: Extract content from PDF/DOCX
    """
    
    def __init__(self, base_path: str = "data/files", enable_s3: bool = False):
        super().__init__(
            name="file_tool",
            description="File system operations with security controls"
        )
        
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.enable_s3 = enable_s3
        self.s3_client = None
        
        if enable_s3:
            self._initialize_s3()
        
        # Security: Allowed file extensions
        self.allowed_extensions = {
            '.txt', '.md', '.json', '.csv', '.xml', '.yaml', '.yml',
            '.log', '.pdf', '.docx', '.xlsx', '.html', '.py'
        }
    
    def _initialize_s3(self):
        """Initialize S3 client for cloud storage"""
        try:
            import boto3
            self.s3_client = boto3.client('s3')
            self.logger.info("S3 client initialized")
        except ImportError:
            self.logger.warning("boto3 not installed, S3 disabled")
            self.enable_s3 = False
        except Exception as e:
            self.logger.error(f"S3 initialization failed: {e}")
            self.enable_s3 = False
    
    def execute(self, tool_input: ToolInput) -> ToolResult:
        """Execute file action"""
        action = tool_input.action.lower()
        params = tool_input.params
        
        action_map = {
            "read": self._read_file,
            "write": self._write_file,
            "append": self._append_file,
            "delete": self._delete_file,
            "list": self._list_directory,
            "exists": self._file_exists,
            "info": self._file_info,
            "extract": self._extract_content
        }
        
        handler = action_map.get(action)
        if not handler:
            return ToolResult(
                success=False,
                error=f"Unknown action: {action}",
                error_type="validation"
            )
        
        return handler(params)
    
    def _read_file(self, params: Dict[str, Any]) -> ToolResult:
        """
        Read file contents
        
        Params:
            path: File path (relative to base_path)
            encoding: Text encoding (default: utf-8)
            binary: Read as binary (default: False)
        """
        path = params.get("path")
        encoding = params.get("encoding", "utf-8")
        binary = params.get("binary", False)
        
        if not path:
            return ToolResult(
                success=False,
                error="path required",
                error_type="validation"
            )
        
        try:
            # Security: Validate path
            safe_path = self._validate_path(path)
            if not safe_path:
                return ToolResult(
                    success=False,
                    error="Invalid or unsafe path",
                    error_type="validation"
                )
            
            # Check if file exists
            if not safe_path.exists():
                return ToolResult(
                    success=False,
                    error=f"File not found: {path}",
                    error_type="resource_not_found"
                )
            
            if not safe_path.is_file():
                return ToolResult(
                    success=False,
                    error=f"Path is not a file: {path}",
                    error_type="validation"
                )
            
            # Read file
            if binary:
                content = safe_path.read_bytes()
                # Return base64 encoded for binary
                import base64
                content_str = base64.b64encode(content).decode('ascii')
            else:
                content_str = safe_path.read_text(encoding=encoding)
            
            file_size = safe_path.stat().st_size
            
            return ToolResult(
                success=True,
                data={
                    "path": str(safe_path.relative_to(self.base_path)),
                    "content": content_str,
                    "size_bytes": file_size,
                    "encoding": encoding if not binary else "binary",
                    "line_count": content_str.count('\n') + 1 if not binary else None
                }
            )
            
        except UnicodeDecodeError as e:
            return ToolResult(
                success=False,
                error=f"Encoding error: {e}. Try binary=True",
                error_type="validation"
            )
        except Exception as e:
            self.logger.error(f"Read file failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                error_type="internal_error"
            )
    
    def _write_file(self, params: Dict[str, Any]) -> ToolResult:
        """
        Write/create file
        
        Params:
            path: File path
            content: File content
            encoding: Text encoding (default: utf-8)
            overwrite: Allow overwriting (default: False)
        """
        path = params.get("path")
        content = params.get("content")
        encoding = params.get("encoding", "utf-8")
        overwrite = params.get("overwrite", False)
        
        if not path or content is None:
            return ToolResult(
                success=False,
                error="path and content required",
                error_type="validation"
            )
        
        try:
            # Security: Validate path
            safe_path = self._validate_path(path)
            if not safe_path:
                return ToolResult(
                    success=False,
                    error="Invalid or unsafe path",
                    error_type="validation"
                )
            
            # Check if file exists and overwrite not allowed
            if safe_path.exists() and not overwrite:
                return ToolResult(
                    success=False,
                    error=f"File exists. Set overwrite=True to replace",
                    error_type="conflict"
                )
            
            # Create parent directories if needed
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            safe_path.write_text(content, encoding=encoding)
            
            file_size = safe_path.stat().st_size
            
            return ToolResult(
                success=True,
                data={
                    "path": str(safe_path.relative_to(self.base_path)),
                    "size_bytes": file_size,
                    "created": True,
                    "overwritten": safe_path.exists()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Write file failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                error_type="internal_error"
            )
    
    def _append_file(self, params: Dict[str, Any]) -> ToolResult:
        """
        Append to file
        
        Params:
            path: File path
            content: Content to append
        """
        path = params.get("path")
        content = params.get("content")
        
        if not path or content is None:
            return ToolResult(
                success=False,
                error="path and content required",
                error_type="validation"
            )
        
        try:
            safe_path = self._validate_path(path)
            if not safe_path:
                return ToolResult(
                    success=False,
                    error="Invalid or unsafe path",
                    error_type="validation"
                )
            
            # Create file if doesn't exist
            if not safe_path.exists():
                safe_path.parent.mkdir(parents=True, exist_ok=True)
                safe_path.touch()
            
            # Append content
            with safe_path.open('a', encoding='utf-8') as f:
                f.write(content)
            
            file_size = safe_path.stat().st_size
            
            return ToolResult(
                success=True,
                data={
                    "path": str(safe_path.relative_to(self.base_path)),
                    "size_bytes": file_size,
                    "appended": True
                }
            )
            
        except Exception as e:
            self.logger.error(f"Append file failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                error_type="internal_error"
            )
    
    def _delete_file(self, params: Dict[str, Any]) -> ToolResult:
        """
        Delete file
        
        Params:
            path: File path
        """
        path = params.get("path")
        
        if not path:
            return ToolResult(
                success=False,
                error="path required",
                error_type="validation"
            )
        
        try:
            safe_path = self._validate_path(path)
            if not safe_path:
                return ToolResult(
                    success=False,
                    error="Invalid or unsafe path",
                    error_type="validation"
                )
            
            if not safe_path.exists():
                return ToolResult(
                    success=False,
                    error=f"File not found: {path}",
                    error_type="resource_not_found"
                )
            
            # Delete file
            safe_path.unlink()
            
            return ToolResult(
                success=True,
                data={
                    "path": path,
                    "deleted": True
                }
            )
            
        except Exception as e:
            self.logger.error(f"Delete file failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                error_type="internal_error"
            )
    
    def _list_directory(self, params: Dict[str, Any]) -> ToolResult:
        """
        List directory contents
        
        Params:
            path: Directory path (default: root)
            pattern: File pattern (e.g., *.txt)
        """
        path = params.get("path", ".")
        pattern = params.get("pattern", "*")
        
        try:
            safe_path = self._validate_path(path)
            if not safe_path:
                return ToolResult(
                    success=False,
                    error="Invalid or unsafe path",
                    error_type="validation"
                )
            
            if not safe_path.exists():
                return ToolResult(
                    success=False,
                    error=f"Directory not found: {path}",
                    error_type="resource_not_found"
                )
            
            if not safe_path.is_dir():
                return ToolResult(
                    success=False,
                    error=f"Path is not a directory: {path}",
                    error_type="validation"
                )
            
            # List files
            files = []
            for item in safe_path.glob(pattern):
                files.append({
                    "name": item.name,
                    "path": str(item.relative_to(self.base_path)),
                    "type": "file" if item.is_file() else "directory",
                    "size_bytes": item.stat().st_size if item.is_file() else None,
                    "modified": datetime.fromtimestamp(
                        item.stat().st_mtime
                    ).isoformat()
                })
            
            return ToolResult(
                success=True,
                data={
                    "path": path,
                    "files": files,
                    "count": len(files)
                }
            )
            
        except Exception as e:
            self.logger.error(f"List directory failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                error_type="internal_error"
            )
    
    def _file_exists(self, params: Dict[str, Any]) -> ToolResult:
        """Check if file exists"""
        path = params.get("path")
        
        if not path:
            return ToolResult(
                success=False,
                error="path required",
                error_type="validation"
            )
        
        try:
            safe_path = self._validate_path(path)
            if not safe_path:
                exists = False
            else:
                exists = safe_path.exists()
            
            return ToolResult(
                success=True,
                data={
                    "path": path,
                    "exists": exists,
                    "is_file": safe_path.is_file() if exists else None,
                    "is_directory": safe_path.is_dir() if exists else None
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                error_type="internal_error"
            )
    
    def _file_info(self, params: Dict[str, Any]) -> ToolResult:
        """Get file metadata"""
        path = params.get("path")
        
        if not path:
            return ToolResult(
                success=False,
                error="path required",
                error_type="validation"
            )
        
        try:
            safe_path = self._validate_path(path)
            if not safe_path or not safe_path.exists():
                return ToolResult(
                    success=False,
                    error="File not found",
                    error_type="resource_not_found"
                )
            
            stat = safe_path.stat()
            mime_type, _ = mimetypes.guess_type(str(safe_path))
            
            return ToolResult(
                success=True,
                data={
                    "path": str(safe_path.relative_to(self.base_path)),
                    "name": safe_path.name,
                    "size_bytes": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "mime_type": mime_type,
                    "extension": safe_path.suffix,
                    "is_file": safe_path.is_file(),
                    "is_directory": safe_path.is_dir()
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                error_type="internal_error"
            )
    
    def _extract_content(self, params: Dict[str, Any]) -> ToolResult:
        """
        Extract text content from PDF/DOCX
        
        Params:
            path: File path
        """
        path = params.get("path")
        
        if not path:
            return ToolResult(
                success=False,
                error="path required",
                error_type="validation"
            )
        
        try:
            safe_path = self._validate_path(path)
            if not safe_path or not safe_path.exists():
                return ToolResult(
                    success=False,
                    error="File not found",
                    error_type="resource_not_found"
                )
            
            extension = safe_path.suffix.lower()
            
            if extension == '.pdf':
                content = self._extract_pdf(safe_path)
            elif extension == '.docx':
                content = self._extract_docx(safe_path)
            else:
                return ToolResult(
                    success=False,
                    error=f"Unsupported file type: {extension}",
                    error_type="validation"
                )
            
            return ToolResult(
                success=True,
                data={
                    "path": str(safe_path.relative_to(self.base_path)),
                    "content": content,
                    "length": len(content)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Extract content failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                error_type="internal_error"
            )
    
    def _extract_pdf(self, path: Path) -> str:
        """Extract text from PDF"""
        try:
            import PyPDF2
            
            with path.open('rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = []
                for page in reader.pages:
                    text.append(page.extract_text())
                return '\n'.join(text)
                
        except ImportError:
            return "PDF extraction requires PyPDF2 (pip install PyPDF2)"
        except Exception as e:
            raise Exception(f"PDF extraction failed: {e}")
    
    def _extract_docx(self, path: Path) -> str:
        """Extract text from DOCX"""
        try:
            import docx
            
            doc = docx.Document(str(path))
            return '\n'.join([para.text for para in doc.paragraphs])
            
        except ImportError:
            return "DOCX extraction requires python-docx (pip install python-docx)"
        except Exception as e:
            raise Exception(f"DOCX extraction failed: {e}")
    
    def _validate_path(self, path: str) -> Optional[Path]:
        """
        Validate and sanitize file path
        Prevents directory traversal attacks
        """
        try:
            # Convert to Path
            requested_path = Path(path)
            
            # Resolve to absolute path within base_path
            full_path = (self.base_path / requested_path).resolve()
            
            # Security: Ensure path is within base_path
            if not str(full_path).startswith(str(self.base_path.resolve())):
                self.logger.warning(
                    f"Path traversal attempt blocked: {path}"
                )
                return None
            
            # Check file extension if it's a file
            if full_path.exists() and full_path.is_file():
                if full_path.suffix.lower() not in self.allowed_extensions:
                    self.logger.warning(
                        f"Disallowed file extension: {full_path.suffix}"
                    )
                    return None
            
            return full_path
            
        except Exception as e:
            self.logger.error(f"Path validation failed: {e}")
            return None
    
    def get_capability(self) -> ToolCapability:
        """Get file tool capability"""
        return ToolCapability(
            name=self.name,
            description=self.description,
            supported_actions=[
                "read", "write", "append", "delete",
                "list", "exists", "info", "extract"
            ],
            required_params={
                "read": "path",
                "write": "path, content",
                "append": "path, content",
                "delete": "path",
                "list": "",
                "exists": "path",
                "info": "path",
                "extract": "path"
            },
            optional_params={
                "read": "encoding, binary",
                "write": "encoding, overwrite",
                "list": "path, pattern"
            },
            requires_auth=False,
            examples=[
                {
                    "action": "read",
                    "params": {"path": "data.txt"},
                    "description": "Read text file"
                },
                {
                    "action": "write",
                    "params": {
                        "path": "output.txt",
                        "content": "Hello World"
                    },
                    "description": "Write to file"
                }
            ]
        )


if __name__ == "__main__":
    """Test file tool"""
    print("📁 Testing File Tool...")
    
    file_tool = FileTool(base_path="data/test_files")
    
    # Test write
    print("\n✍️  Testing write...")
    result = file_tool.run(ToolInput(
        action="write",
        params={
            "path": "test.txt",
            "content": "Hello, World!",
            "overwrite": True
        }
    ))
    print(f"   Success: {result.success}")
    
    # Test read
    print("\n📖 Testing read...")
    result = file_tool.run(ToolInput(
        action="read",
        params={"path": "test.txt"}
    ))
    print(f"   Success: {result.success}")
    print(f"   Content: {result.data.get('content', '')[:50]}")
    
    # Test list
    print("\n📋 Testing list...")
    result = file_tool.run(ToolInput(
        action="list",
        params={"path": "."}
    ))
    print(f"   Success: {result.success}")
    print(f"   Files: {result.data.get('count', 0)}")
    
    print("\n✅ File tool test complete")