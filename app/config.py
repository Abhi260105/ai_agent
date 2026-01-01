"""
Configuration Management
Centralized config using Pydantic Settings for type safety
"""
from typing import Literal, Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class LLMConfig(BaseSettings):
    """LLM Provider Configuration"""
    
    provider: Literal["openai", "anthropic", "ollama"] = Field(
        default="openai",
        env="LLM_PROVIDER"
    )
    
    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.1, env="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(default=4096, env="OPENAI_MAX_TOKENS")
    
    # Anthropic
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-opus-20240229", env="ANTHROPIC_MODEL")
    
    # Ollama
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3", env="OLLAMA_MODEL")
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    @validator("openai_api_key")
    def validate_openai_key(cls, v, values):
        """Ensure OpenAI key exists if OpenAI is the provider"""
        if values.get("provider") == "openai" and not v:
            raise ValueError("OPENAI_API_KEY required when using OpenAI provider")
        return v


class AgentConfig(BaseSettings):
    """Agent Behavior Configuration"""
    
    name: str = Field(default="TaskExecutorAgent", env="AGENT_NAME")
    max_retries: int = Field(default=3, env="AGENT_MAX_RETRIES", ge=1, le=10)
    timeout_seconds: int = Field(default=300, env="AGENT_TIMEOUT_SECONDS", ge=10)
    temperature: float = Field(default=0.1, env="AGENT_TEMPERATURE", ge=0.0, le=1.0)
    verbose: bool = Field(default=True, env="AGENT_VERBOSE")
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class StorageConfig(BaseSettings):
    """Database and Memory Configuration"""
    
    database_url: str = Field(default="sqlite:///data/memory.db", env="DATABASE_URL")
    vector_store_path: str = Field(default="data/vector_store", env="VECTOR_STORE_PATH")
    memory_retention_days: int = Field(default=90, env="MEMORY_RETENTION_DAYS", ge=1)
    enable_vector_memory: bool = Field(default=True, env="ENABLE_VECTOR_MEMORY")
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    @property
    def db_path(self) -> Path:
        """Extract database file path from URL"""
        if self.database_url.startswith("sqlite:///"):
            return Path(self.database_url.replace("sqlite:///", ""))
        return Path("data/memory.db")
    
    @property
    def vector_path(self) -> Path:
        """Vector store directory as Path object"""
        return Path(self.vector_store_path)


class ToolConfig(BaseSettings):
    """External Tool API Configuration"""
    
    # Google APIs
    google_client_id: Optional[str] = Field(default=None, env="GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = Field(default=None, env="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field(default="http://localhost:8080", env="GOOGLE_REDIRECT_URI")
    google_credentials_path: str = Field(default="data/credentials.json", env="GOOGLE_CREDENTIALS_PATH")
    
    # Search APIs
    serpapi_api_key: Optional[str] = Field(default=None, env="SERPAPI_API_KEY")
    brave_search_api_key: Optional[str] = Field(default=None, env="BRAVE_SEARCH_API_KEY")
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class LoggingConfig(BaseSettings):
    """Logging Configuration"""
    
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        env="LOG_LEVEL"
    )
    format: Literal["json", "console"] = Field(default="json", env="LOG_FORMAT")
    file_path: str = Field(default="logs/agent.log", env="LOG_FILE_PATH")
    enable_file_logging: bool = Field(default=True, env="ENABLE_FILE_LOGGING")
    enable_console_logging: bool = Field(default=True, env="ENABLE_CONSOLE_LOGGING")
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    @property
    def log_file(self) -> Path:
        """Log file path as Path object"""
        return Path(self.file_path)


class SecurityConfig(BaseSettings):
    """Security and Authentication Configuration"""
    
    secret_key: str = Field(default="change-this-secret-key", env="SECRET_KEY")
    enable_auth: bool = Field(default=False, env="ENABLE_AUTH")
    allowed_hosts: str = Field(default="localhost,127.0.0.1", env="ALLOWED_HOSTS")
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    @property
    def allowed_hosts_list(self) -> list[str]:
        """Parse comma-separated hosts"""
        return [host.strip() for host in self.allowed_hosts.split(",")]


class UIConfig(BaseSettings):
    """User Interface Configuration"""
    
    enable_web_ui: bool = Field(default=True, env="ENABLE_WEB_UI")
    web_ui_port: int = Field(default=8501, env="WEB_UI_PORT", ge=1024, le=65535)
    enable_cli: bool = Field(default=True, env="ENABLE_CLI")
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class DevelopmentConfig(BaseSettings):
    """Development and Debugging Configuration"""
    
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        env="ENVIRONMENT"
    )
    debug_mode: bool = Field(default=True, env="DEBUG_MODE")
    enable_mock_tools: bool = Field(default=False, env="ENABLE_MOCK_TOOLS")
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class Config:
    """
    Master Configuration Object
    Aggregates all configuration sections
    """
    
    def __init__(self):
        self.llm = LLMConfig()
        self.agent = AgentConfig()
        self.storage = StorageConfig()
        self.tools = ToolConfig()
        self.logging = LoggingConfig()
        self.security = SecurityConfig()
        self.ui = UIConfig()
        self.dev = DevelopmentConfig()
        
        # Ensure critical directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create required directories if they don't exist"""
        directories = [
            self.storage.db_path.parent,
            self.storage.vector_path,
            self.logging.log_file.parent,
            Path("data")
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def validate(self) -> bool:
        """
        Validate configuration integrity
        Returns True if config is valid
        """
        errors = []
        
        # Check LLM provider configuration
        if self.llm.provider == "openai" and not self.llm.openai_api_key:
            errors.append("OpenAI API key missing")
        
        if self.llm.provider == "anthropic" and not self.llm.anthropic_api_key:
            errors.append("Anthropic API key missing")
        
        # Check database path writability
        if not self.storage.db_path.parent.exists():
            errors.append(f"Database directory does not exist: {self.storage.db_path.parent}")
        
        if errors:
            for error in errors:
                print(f"❌ Config Error: {error}")
            return False
        
        return True
    
    def summary(self) -> str:
        """Generate human-readable config summary"""
        return f"""
╔════════════════════════════════════════════════════════════════════
║ AI AGENT CONFIGURATION
╠════════════════════════════════════════════════════════════════════
║ Environment: {self.dev.environment.upper()}
║ Debug Mode: {'✓' if self.dev.debug_mode else '✗'}
║
║ LLM Provider: {self.llm.provider.upper()}
║ Model: {getattr(self.llm, f'{self.llm.provider}_model')}
║ Temperature: {self.agent.temperature}
║
║ Database: {self.storage.database_url}
║ Vector Store: {self.storage.vector_store_path}
║ Memory Retention: {self.storage.memory_retention_days} days
║
║ Max Retries: {self.agent.max_retries}
║ Timeout: {self.agent.timeout_seconds}s
║
║ Log Level: {self.logging.level}
║ Log Format: {self.logging.format}
║
║ Web UI: {'✓' if self.ui.enable_web_ui else '✗'}
║ CLI: {'✓' if self.ui.enable_cli else '✗'}
╚════════════════════════════════════════════════════════════════════
        """.strip()


# Global configuration instance
config = Config()


if __name__ == "__main__":
    """Test configuration loading"""
    print(config.summary())
    
    if config.validate():
        print("\n✅ Configuration is valid")
    else:
        print("\n❌ Configuration has errors")