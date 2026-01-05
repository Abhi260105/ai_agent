"""
Code Executor Tool - Sandboxed Python Execution
Provides safe Python code execution with timeout and output capture
"""
from typing import Dict, Any, Optional
import sys
import io
import traceback
import signal
from contextlib import redirect_stdout, redirect_stderr
import ast
import subprocess
from pathlib import Path

from app.tools.base_tool import BaseTool
from app.schemas.tool_schema import ToolInput, ToolResult, ToolCapability
from app.utils.logger import get_logger

logger = get_logger("tools.code_executor")


class CodeExecutorTool(BaseTool):
    """
    Execute Python code in sandboxed environment
    
    Supported actions:
    - execute: Run Python code
    - validate: Validate Python syntax
    - install: Install Python package (pip)
    
    Security features:
    - Timeout enforcement
    - Output capture
    - Restricted builtins
    - No file system access (optional)
    """
    
    def __init__(self, enable_file_access: bool = False, max_output_length: int = 10000):
        super().__init__(
            name="code_executor_tool",
            description="Execute Python code safely with timeout and output capture"
        )
        
        self.enable_file_access = enable_file_access
        self.max_output_length = max_output_length
        
        # Restricted builtins (security)
        self.restricted_builtins = {
            'print', 'len', 'range', 'enumerate', 'zip', 'map', 'filter',
            'sum', 'min', 'max', 'abs', 'round', 'sorted', 'list', 'dict',
            'set', 'tuple', 'str', 'int', 'float', 'bool', 'type', 'isinstance'
        }
        
        # Dangerous modules to block
        self.blocked_modules = {
            'os', 'sys', 'subprocess', 'shutil', 'socket', 'urllib',
            'requests', 'http', 'pickle', 'eval', 'exec', '__import__'
        }
    
    def execute(self, tool_input: ToolInput) -> ToolResult:
        """Execute code action"""
        action = tool_input.action.lower()
        params = tool_input.params
        
        if action == "execute":
            return self._execute_code(params)
        elif action == "validate":
            return self._validate_code(params)
        elif action == "install":
            return self._install_package(params)
        else:
            return ToolResult(
                success=False,
                error=f"Unknown action: {action}",
                error_type="validation"
            )
    
    def _execute_code(self, params: Dict[str, Any]) -> ToolResult:
        """
        Execute Python code
        
        Params:
            code: Python code to execute
            timeout: Execution timeout in seconds (default: 10)
            globals: Global variables dict (optional)
        """
        code = params.get("code")
        timeout = params.get("timeout", 10)
        globals_dict = params.get("globals", {})
        
        if not code:
            return ToolResult(
                success=False,
                error="code required",
                error_type="validation"
            )
        
        # Validate syntax first
        validation = self._validate_syntax(code)
        if not validation["valid"]:
            return ToolResult(
                success=False,
                error=f"Syntax error: {validation['error']}",
                error_type="validation"
            )
        
        # Check for dangerous imports
        if not self._check_imports(code):
            return ToolResult(
                success=False,
                error="Code contains blocked imports (os, sys, subprocess, etc.)",
                error_type="validation"
            )
        
        try:
            # Execute with timeout
            result = self._execute_with_timeout(
                code,
                globals_dict,
                timeout
            )
            
            return ToolResult(
                success=True,
                data={
                    "stdout": result["stdout"][:self.max_output_length],
                    "stderr": result["stderr"][:self.max_output_length],
                    "return_value": str(result.get("return_value", ""))[:1000],
                    "execution_time_ms": result["execution_time_ms"],
                    "output_truncated": len(result["stdout"]) > self.max_output_length
                }
            )
            
        except TimeoutError:
            return ToolResult(
                success=False,
                error=f"Execution timeout after {timeout} seconds",
                error_type="timeout"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Execution error: {str(e)}",
                error_type="internal_error",
                data={
                    "traceback": traceback.format_exc()[:self.max_output_length]
                }
            )
    
    def _validate_code(self, params: Dict[str, Any]) -> ToolResult:
        """
        Validate Python code syntax
        
        Params:
            code: Python code to validate
        """
        code = params.get("code")
        
        if not code:
            return ToolResult(
                success=False,
                error="code required",
                error_type="validation"
            )
        
        validation = self._validate_syntax(code)
        
        if validation["valid"]:
            return ToolResult(
                success=True,
                data={
                    "valid": True,
                    "message": "Code syntax is valid"
                }
            )
        else:
            return ToolResult(
                success=False,
                error=validation["error"],
                error_type="validation",
                data={
                    "valid": False,
                    "line": validation.get("line"),
                    "column": validation.get("column")
                }
            )
    
    def _install_package(self, params: Dict[str, Any]) -> ToolResult:
        """
        Install Python package using pip
        
        Params:
            package: Package name
            version: Package version (optional)
        """
        package = params.get("package")
        version = params.get("version")
        
        if not package:
            return ToolResult(
                success=False,
                error="package required",
                error_type="validation"
            )
        
        try:
            # Build pip command
            if version:
                package_spec = f"{package}=={version}"
            else:
                package_spec = package
            
            # Run pip install
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package_spec],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return ToolResult(
                    success=True,
                    data={
                        "package": package,
                        "version": version,
                        "installed": True,
                        "output": result.stdout
                    }
                )
            else:
                return ToolResult(
                    success=False,
                    error=f"Installation failed: {result.stderr}",
                    error_type="external_api"
                )
                
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                error="Installation timeout",
                error_type="timeout"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                error_type="internal_error"
            )
    
    def _execute_with_timeout(
        self,
        code: str,
        globals_dict: Dict,
        timeout: int
    ) -> Dict[str, Any]:
        """Execute code with timeout"""
        import time
        
        start_time = time.time()
        
        # Prepare globals with restricted builtins
        safe_globals = {
            '__builtins__': {
                name: getattr(__builtins__, name)
                for name in self.restricted_builtins
                if hasattr(__builtins__, name)
            },
            **globals_dict
        }
        
        # Capture output
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        return_value = None
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Execution exceeded {timeout} seconds")
        
        try:
            # Set timeout alarm (Unix only)
            if hasattr(signal, 'SIGALRM'):
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(timeout)
            
            # Execute code
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec_result = exec(code, safe_globals)
                # Try to capture last expression value
                try:
                    return_value = eval(code.split('\n')[-1], safe_globals)
                except:
                    pass
            
            # Cancel timeout
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            return {
                "stdout": stdout_capture.getvalue(),
                "stderr": stderr_capture.getvalue(),
                "return_value": return_value,
                "execution_time_ms": execution_time_ms
            }
            
        except TimeoutError:
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
            raise
        except Exception as e:
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
            raise
    
    def _validate_syntax(self, code: str) -> Dict[str, Any]:
        """Validate Python syntax"""
        try:
            ast.parse(code)
            return {"valid": True}
        except SyntaxError as e:
            return {
                "valid": False,
                "error": str(e),
                "line": e.lineno,
                "column": e.offset
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    def _check_imports(self, code: str) -> bool:
        """Check for dangerous imports"""
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in self.blocked_modules:
                            return False
                elif isinstance(node, ast.ImportFrom):
                    if node.module in self.blocked_modules:
                        return False
            
            return True
            
        except:
            return False
    
    def get_capability(self) -> ToolCapability:
        """Get code executor capability"""
        return ToolCapability(
            name=self.name,
            description=self.description,
            supported_actions=["execute", "validate", "install"],
            required_params={
                "execute": "code",
                "validate": "code",
                "install": "package"
            },
            optional_params={
                "execute": "timeout, globals",
                "install": "version"
            },
            requires_auth=False,
            examples=[
                {
                    "action": "execute",
                    "params": {
                        "code": "print('Hello, World!')\nresult = 2 + 2\nprint(f'2 + 2 = {result}')"
                    },
                    "description": "Execute simple Python code"
                },
                {
                    "action": "validate",
                    "params": {
                        "code": "def hello():\n    print('hello')"
                    },
                    "description": "Validate Python syntax"
                }
            ]
        )
    
    def health_check(self) -> bool:
        """Check if Python execution works"""
        try:
            result = self._execute_code({
                "code": "print('test')",
                "timeout": 1
            })
            return result.success
        except:
            return False


if __name__ == "__main__":
    """Test code executor tool"""
    print("⚙️ Testing Code Executor Tool...")
    
    executor = CodeExecutorTool()
    
    # Test simple execution
    print("\n▶️ Testing code execution...")
    result = executor.run(ToolInput(
        action="execute",
        params={
            "code": """
print("Hello, World!")
x = 10
y = 20
print(f"Sum: {x + y}")
result = x * y
print(f"Product: {result}")
"""
        }
    ))
    print(f"   Success: {result.success}")
    if result.success:
        print(f"   Output:\n{result.data.get('stdout', '')}")
    
    # Test syntax validation
    print("\n✅ Testing syntax validation...")
    result = executor.run(ToolInput(
        action="validate",
        params={
            "code": "def hello():\n    print('hello')"
        }
    ))
    print(f"   Valid: {result.success}")
    
    # Test invalid syntax
    print("\n❌ Testing invalid syntax...")
    result = executor.run(ToolInput(
        action="validate",
        params={
            "code": "def hello(\n    print('hello')"
        }
    ))
    print(f"   Valid: {result.success}")
    if not result.success:
        print(f"   Error: {result.error}")
    
    # Test blocked imports
    print("\n🚫 Testing blocked imports...")
    result = executor.run(ToolInput(
        action="execute",
        params={
            "code": "import os\nprint(os.listdir())"
        }
    ))
    print(f"   Blocked: {not result.success}")
    
    print("\n✅ Code executor tool test complete")