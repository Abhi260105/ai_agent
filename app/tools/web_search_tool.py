"""
Web Search Tool - Internet Search Capabilities
Provides web search via SerpAPI with DuckDuckGo fallback
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import requests
import hashlib
import json
from pathlib import Path

from app.tools.base_tool import BaseTool
from app.schemas.tool_schema import ToolInput, ToolResult, ToolCapability
from app.config import config
from app.utils.logger import get_logger

logger = get_logger("tools.web_search")


class WebSearchTool(BaseTool):
    """
    Web search with caching and multiple providers
    
    Supported actions:
    - search: General web search
    - news: Search recent news
    - images: Image search
    - videos: Video search
    
    Providers:
    1. SerpAPI (primary, requires API key)
    2. DuckDuckGo (fallback, free)
    3. Mock (testing)
    """
    
    def __init__(self, mock_mode: bool = None):
        super().__init__(
            name="web_search_tool",
            description="Search the web for information"
        )
        
        self.mock_mode = (
            mock_mode if mock_mode is not None
            else config.dev.enable_mock_tools
        )
        
        # API keys
        self.serpapi_key = config.tools.serpapi_api_key
        self.brave_key = config.tools.brave_search_api_key
        
        # Cache
        self.cache_dir = Path("data/search_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl_hours = 24
        
        # Rate limiting
        self.last_request_time = None
        self.min_request_interval = 1.0  # seconds
        
        self.logger.info(
            "Web search tool initialized",
            mock_mode=self.mock_mode,
            has_serpapi=bool(self.serpapi_key),
            has_brave=bool(self.brave_key)
        )
    
    def execute(self, tool_input: ToolInput) -> ToolResult:
        """Execute search action"""
        action = tool_input.action.lower()
        params = tool_input.params
        
        if action == "search":
            return self._search(params)
        elif action == "news":
            return self._search_news(params)
        elif action == "images":
            return self._search_images(params)
        elif action == "videos":
            return self._search_videos(params)
        else:
            return ToolResult(
                success=False,
                error=f"Unknown action: {action}",
                error_type="validation"
            )
    
    def _search(self, params: Dict[str, Any]) -> ToolResult:
        """
        General web search
        
        Params:
            query: Search query
            num_results: Number of results (default: 10)
            safe_search: Enable safe search (default: True)
        """
        query = params.get("query")
        num_results = params.get("num_results", 10)
        safe_search = params.get("safe_search", True)
        
        if not query:
            return ToolResult(
                success=False,
                error="query required",
                error_type="validation"
            )
        
        # Check cache first
        cached = self._get_cached_results(query, "search")
        if cached:
            self.logger.info("Returning cached results", query=query)
            return ToolResult(
                success=True,
                data={**cached, "cached": True}
            )
        
        # Try search providers
        if self.mock_mode:
            result = self._mock_search(query, num_results)
        elif self.serpapi_key:
            result = self._search_serpapi(query, num_results, safe_search)
        elif self.brave_key:
            result = self._search_brave(query, num_results, safe_search)
        else:
            result = self._search_duckduckgo(query, num_results)
        
        # Cache results if successful
        if result.success:
            self._cache_results(query, "search", result.data)
        
        return result
    
    def _search_news(self, params: Dict[str, Any]) -> ToolResult:
        """Search recent news"""
        query = params.get("query")
        num_results = params.get("num_results", 10)
        
        if not query:
            return ToolResult(
                success=False,
                error="query required",
                error_type="validation"
            )
        
        if self.mock_mode:
            return self._mock_search_news(query, num_results)
        
        # Use SerpAPI news search if available
        if self.serpapi_key:
            return self._search_serpapi_news(query, num_results)
        
        # Fallback: regular search with "news" added
        return self._search({
            "query": f"{query} news",
            "num_results": num_results
        })
    
    def _search_images(self, params: Dict[str, Any]) -> ToolResult:
        """Search images"""
        return ToolResult(
            success=False,
            error="Image search not yet implemented",
            error_type="internal_error"
        )
    
    def _search_videos(self, params: Dict[str, Any]) -> ToolResult:
        """Search videos"""
        return ToolResult(
            success=False,
            error="Video search not yet implemented",
            error_type="internal_error"
        )
    
    def _search_serpapi(
        self,
        query: str,
        num_results: int,
        safe_search: bool
    ) -> ToolResult:
        """Search using SerpAPI"""
        try:
            import time
            
            # Rate limiting
            self._rate_limit()
            
            params = {
                "q": query,
                "num": num_results,
                "api_key": self.serpapi_key,
                "safe": "active" if safe_search else "off"
            }
            
            response = requests.get(
                "https://serpapi.com/search",
                params=params,
                timeout=10
            )
            
            if response.status_code == 429:
                return ToolResult(
                    success=False,
                    error="Rate limit exceeded",
                    error_type="rate_limit"
                )
            
            response.raise_for_status()
            data = response.json()
            
            # Parse results
            results = []
            for item in data.get("organic_results", [])[:num_results]:
                results.append({
                    "title": item.get("title"),
                    "url": item.get("link"),
                    "snippet": item.get("snippet"),
                    "position": item.get("position")
                })
            
            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "results": results,
                    "total_results": len(results),
                    "provider": "serpapi"
                }
            )
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"SerpAPI request failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                error_type="external_api"
            )
        except Exception as e:
            self.logger.error(f"SerpAPI search failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                error_type="internal_error"
            )
    
    def _search_brave(
        self,
        query: str,
        num_results: int,
        safe_search: bool
    ) -> ToolResult:
        """Search using Brave Search API"""
        try:
            self._rate_limit()
            
            headers = {
                "Accept": "application/json",
                "X-Subscription-Token": self.brave_key
            }
            
            params = {
                "q": query,
                "count": num_results,
                "safesearch": "strict" if safe_search else "off"
            }
            
            response = requests.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers=headers,
                params=params,
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("web", {}).get("results", [])[:num_results]:
                results.append({
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "snippet": item.get("description"),
                    "age": item.get("age")
                })
            
            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "results": results,
                    "total_results": len(results),
                    "provider": "brave"
                }
            )
            
        except Exception as e:
            self.logger.error(f"Brave search failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                error_type="external_api"
            )
    
    def _search_duckduckgo(self, query: str, num_results: int) -> ToolResult:
        """Search using DuckDuckGo (free, no API key needed)"""
        try:
            from duckduckgo_search import DDGS
            
            self._rate_limit()
            
            with DDGS() as ddgs:
                results_list = list(ddgs.text(
                    query,
                    max_results=num_results
                ))
            
            results = []
            for i, item in enumerate(results_list[:num_results]):
                results.append({
                    "title": item.get("title"),
                    "url": item.get("href"),
                    "snippet": item.get("body"),
                    "position": i + 1
                })
            
            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "results": results,
                    "total_results": len(results),
                    "provider": "duckduckgo"
                }
            )
            
        except ImportError:
            return ToolResult(
                success=False,
                error="DuckDuckGo search requires duckduckgo-search (pip install duckduckgo-search)",
                error_type="internal_error"
            )
        except Exception as e:
            self.logger.error(f"DuckDuckGo search failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                error_type="external_api"
            )
    
    def _search_serpapi_news(self, query: str, num_results: int) -> ToolResult:
        """Search news using SerpAPI"""
        try:
            self._rate_limit()
            
            params = {
                "q": query,
                "num": num_results,
                "api_key": self.serpapi_key,
                "tbm": "nws"  # News search
            }
            
            response = requests.get(
                "https://serpapi.com/search",
                params=params,
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("news_results", [])[:num_results]:
                results.append({
                    "title": item.get("title"),
                    "url": item.get("link"),
                    "snippet": item.get("snippet"),
                    "source": item.get("source"),
                    "date": item.get("date")
                })
            
            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "results": results,
                    "total_results": len(results),
                    "provider": "serpapi_news"
                }
            )
            
        except Exception as e:
            self.logger.error(f"SerpAPI news search failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                error_type="external_api"
            )
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        import time
        
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_request_interval:
                time.sleep(self.min_request_interval - elapsed)
        
        self.last_request_time = time.time()
    
    def _get_cache_key(self, query: str, search_type: str) -> str:
        """Generate cache key"""
        return hashlib.md5(
            f"{search_type}:{query}".encode()
        ).hexdigest()
    
    def _get_cached_results(
        self,
        query: str,
        search_type: str
    ) -> Optional[Dict]:
        """Get cached search results"""
        cache_key = self._get_cache_key(query, search_type)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            # Check if cache is expired
            file_age = datetime.now() - datetime.fromtimestamp(
                cache_file.stat().st_mtime
            )
            
            if file_age > timedelta(hours=self.cache_ttl_hours):
                cache_file.unlink()
                return None
            
            # Load cached data
            with cache_file.open('r') as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.warning(f"Cache read failed: {e}")
            return None
    
    def _cache_results(self, query: str, search_type: str, data: Dict):
        """Cache search results"""
        cache_key = self._get_cache_key(query, search_type)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with cache_file.open('w') as f:
                json.dump(data, f)
        except Exception as e:
            self.logger.warning(f"Cache write failed: {e}")
    
    # Mock implementations
    def _mock_search(self, query: str, num_results: int) -> ToolResult:
        """Mock search for testing"""
        results = [
            {
                "title": f"Result {i+1} for: {query}",
                "url": f"https://example.com/result{i+1}",
                "snippet": f"This is mock search result {i+1} for query: {query}",
                "position": i+1
            }
            for i in range(min(num_results, 5))
        ]
        
        return ToolResult(
            success=True,
            data={
                "query": query,
                "results": results,
                "total_results": len(results),
                "provider": "mock",
                "mock": True
            }
        )
    
    def _mock_search_news(self, query: str, num_results: int) -> ToolResult:
        """Mock news search"""
        results = [
            {
                "title": f"News {i+1}: {query}",
                "url": f"https://news.example.com/article{i+1}",
                "snippet": f"Recent news about {query}",
                "source": "Mock News",
                "date": datetime.now().isoformat()
            }
            for i in range(min(num_results, 3))
        ]
        
        return ToolResult(
            success=True,
            data={
                "query": query,
                "results": results,
                "total_results": len(results),
                "provider": "mock_news",
                "mock": True
            }
        )
    
    def get_capability(self) -> ToolCapability:
        """Get web search tool capability"""
        return ToolCapability(
            name=self.name,
            description=self.description,
            supported_actions=["search", "news", "images", "videos"],
            required_params={
                "search": "query",
                "news": "query"
            },
            optional_params={
                "search": "num_results, safe_search",
                "news": "num_results"
            },
            requires_auth=False,
            rate_limit=100,
            examples=[
                {
                    "action": "search",
                    "params": {
                        "query": "Python programming tutorials",
                        "num_results": 5
                    },
                    "description": "Search for Python tutorials"
                },
                {
                    "action": "news",
                    "params": {
                        "query": "artificial intelligence",
                        "num_results": 10
                    },
                    "description": "Search recent AI news"
                }
            ]
        )
    
    def health_check(self) -> bool:
        """Check if search providers are accessible"""
        if self.mock_mode:
            return True
        
        # Try a simple search
        try:
            result = self._search({"query": "test", "num_results": 1})
            return result.success
        except:
            return False


if __name__ == "__main__":
    """Test web search tool"""
    print("🔍 Testing Web Search Tool...")
    
    search_tool = WebSearchTool(mock_mode=True)
    
    # Test search
    print("\n🌐 Testing search...")
    result = search_tool.run(ToolInput(
        action="search",
        params={
            "query": "Python programming",
            "num_results": 5
        }
    ))
    print(f"   Success: {result.success}")
    print(f"   Results: {result.data.get('total_results', 0)}")
    if result.data.get('results'):
        print(f"   First result: {result.data['results'][0]['title']}")
    
    # Test news search
    print("\n📰 Testing news search...")
    result = search_tool.run(ToolInput(
        action="news",
        params={
            "query": "artificial intelligence",
            "num_results": 3
        }
    ))
    print(f"   Success: {result.success}")
    print(f"   News items: {result.data.get('total_results', 0)}")
    
    print("\n✅ Web search tool test complete")