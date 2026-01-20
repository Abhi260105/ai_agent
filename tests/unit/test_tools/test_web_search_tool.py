"""
Unit tests for Web Search Tool.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock


class TestWebSearchTool:
    """Test suite for Web Search Tool."""
    
    @pytest.fixture
    def web_search_tool(self):
        """Create a WebSearchTool instance for testing."""
        from app.tools.web_search_tool import WebSearchTool
        return WebSearchTool()
    
    @pytest.fixture
    def mock_search_results(self):
        """Mock search results."""
        return {
            'results': [
                {
                    'title': 'Python Tutorial',
                    'url': 'https://example.com/python-tutorial',
                    'snippet': 'Learn Python programming from basics to advanced...'
                },
                {
                    'title': 'Python Documentation',
                    'url': 'https://docs.python.org',
                    'snippet': 'Official Python documentation and guides...'
                },
                {
                    'title': 'Python for Data Science',
                    'url': 'https://example.com/python-data-science',
                    'snippet': 'Using Python for data analysis and machine learning...'
                }
            ],
            'total_results': 3
        }
    
    def test_web_search_tool_initialization(self, web_search_tool):
        """Test web search tool initializes correctly."""
        assert web_search_tool is not None
        assert web_search_tool.name == "web_search"
        assert hasattr(web_search_tool, 'search')
    
    @pytest.mark.asyncio
    async def test_simple_search(self, web_search_tool, mock_search_results):
        """Test performing a simple web search."""
        params = {"query": "Python programming"}
        
        with patch.object(web_search_tool, '_perform_search', return_value=mock_search_results):
            result = await web_search_tool.execute(params)
            
            assert result['status'] == 'success'
            assert len(result['results']) == 3
            assert result['total_results'] == 3
    
    @pytest.mark.asyncio
    async def test_search_with_limit(self, web_search_tool, mock_search_results):
        """Test search with result limit."""
        params = {
            "query": "Python programming",
            "max_results": 2
        }
        
        with patch.object(web_search_tool, '_perform_search', return_value=mock_search_results):
            result = await web_search_tool.execute(params)
            
            assert result['status'] == 'success'
            assert len(result['results']) <= 2
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self, web_search_tool, mock_search_results):
        """Test search with filters."""
        params = {
            "query": "Python programming",
            "filters": {
                "site": "docs.python.org",
                "date_range": "past_year"
            }
        }
        
        with patch.object(web_search_tool, '_perform_search', return_value=mock_search_results):
            result = await web_search_tool.execute(params)
            
            assert result['status'] == 'success'
            assert len(result['results']) > 0
    
    @pytest.mark.asyncio
    async def test_search_safe_mode(self, web_search_tool, mock_search_results):
        """Test search with safe search enabled."""
        params = {
            "query": "test query",
            "safe_search": True
        }
        
        with patch.object(web_search_tool, '_perform_search', return_value=mock_search_results):
            result = await web_search_tool.execute(params)
            
            assert result['status'] == 'success'
            assert result.get('safe_search') is True
    
    @pytest.mark.asyncio
    async def test_empty_query(self, web_search_tool):
        """Test handling of empty query."""
        params = {"query": ""}
        
        result = await web_search_tool.execute(params)
        
        assert result['status'] == 'error'
        assert 'query' in result['error'].lower()
    
    @pytest.mark.asyncio
    async def test_no_results_found(self, web_search_tool):
        """Test handling when no results are found."""
        params = {"query": "very specific unique query xyz123abc"}
        
        with patch.object(web_search_tool, '_perform_search', return_value={'results': [], 'total_results': 0}):
            result = await web_search_tool.execute(params)
            
            assert result['status'] == 'success'
            assert len(result['results']) == 0
    
    @pytest.mark.asyncio
    async def test_network_error(self, web_search_tool):
        """Test handling of network errors."""
        params = {"query": "test query"}
        
        with patch.object(web_search_tool, '_perform_search', side_effect=ConnectionError("Network unavailable")):
            result = await web_search_tool.execute(params)
            
            assert result['status'] == 'error'
            assert 'network' in result['error'].lower() or 'connection' in result['error'].lower()
    
    @pytest.mark.asyncio
    async def test_api_rate_limit(self, web_search_tool):
        """Test handling of API rate limit."""
        params = {"query": "test query"}
        
        with patch.object(web_search_tool, '_perform_search', side_effect=Exception("Rate limit exceeded")):
            result = await web_search_tool.execute(params)
            
            assert result['status'] == 'error'
            assert 'rate limit' in result['error'].lower()
    
    @pytest.mark.asyncio
    async def test_search_with_region(self, web_search_tool, mock_search_results):
        """Test search with region/country specification."""
        params = {
            "query": "local news",
            "region": "US"
        }
        
        with patch.object(web_search_tool, '_perform_search', return_value=mock_search_results):
            result = await web_search_tool.execute(params)
            
            assert result['status'] == 'success'
            assert result.get('region') == 'US'
    
    @pytest.mark.asyncio
    async def test_search_with_language(self, web_search_tool, mock_search_results):
        """Test search with language specification."""
        params = {
            "query": "Python tutoriel",
            "language": "fr"
        }
        
        with patch.object(web_search_tool, '_perform_search', return_value=mock_search_results):
            result = await web_search_tool.execute(params)
            
            assert result['status'] == 'success'
    
    @pytest.mark.asyncio
    async def test_get_page_content(self, web_search_tool):
        """Test fetching full page content."""
        url = "https://example.com/article"
        
        mock_content = {
            'title': 'Article Title',
            'content': 'Full article content here...',
            'author': 'John Doe',
            'published_date': '2025-01-08'
        }
        
        with patch.object(web_search_tool, '_fetch_page', return_value=mock_content):
            result = await web_search_tool.get_page_content(url)
            
            assert result['status'] == 'success'
            assert result['content'] == mock_content['content']
    
    @pytest.mark.asyncio
    async def test_extract_links(self, web_search_tool):
        """Test extracting links from search results."""
        params = {"query": "Python resources"}
        
        mock_results = {
            'results': [
                {'url': 'https://example1.com'},
                {'url': 'https://example2.com'},
                {'url': 'https://example3.com'}
            ],
            'total_results': 3
        }
        
        with patch.object(web_search_tool, '_perform_search', return_value=mock_results):
            result = await web_search_tool.execute(params)
            
            links = [r['url'] for r in result['results']]
            assert len(links) == 3
            assert all(link.startswith('http') for link in links)
    
    @pytest.mark.asyncio
    async def test_search_cache(self, web_search_tool, mock_search_results):
        """Test search result caching."""
        params = {"query": "Python programming"}
        
        with patch.object(web_search_tool, '_perform_search', return_value=mock_search_results) as mock_search:
            # First search
            result1 = await web_search_tool.execute(params)
            
            # Second search with same query (should use cache)
            result2 = await web_search_tool.execute(params)
            
            # Should only call API once if caching works
            if web_search_tool.cache_enabled:
                assert mock_search.call_count == 1
    
    @pytest.mark.asyncio
    async def test_search_timeout(self, web_search_tool):
        """Test search timeout handling."""
        params = {
            "query": "test query",
            "timeout": 5
        }
        
        import asyncio
        
        async def slow_search(*args, **kwargs):
            await asyncio.sleep(10)
            return {'results': []}
        
        with patch.object(web_search_tool, '_perform_search', side_effect=slow_search):
            result = await web_search_tool.execute(params)
            
            assert result['status'] == 'timeout' or result['status'] == 'error'
    
    @pytest.mark.asyncio
    async def test_image_search(self, web_search_tool):
        """Test image search functionality."""
        params = {
            "query": "Python logo",
            "search_type": "images",
            "max_results": 5
        }
        
        mock_images = {
            'results': [
                {'url': 'https://example.com/image1.jpg', 'title': 'Python Logo 1'},
                {'url': 'https://example.com/image2.png', 'title': 'Python Logo 2'}
            ],
            'total_results': 2
        }
        
        with patch.object(web_search_tool, '_perform_search', return_value=mock_images):
            result = await web_search_tool.execute(params)
            
            assert result['status'] == 'success'
            assert result.get('search_type') == 'images'
    
    @pytest.mark.asyncio
    async def test_news_search(self, web_search_tool):
        """Test news-specific search."""
        params = {
            "query": "AI breakthrough",
            "search_type": "news",
            "date_range": "past_week"
        }
        
        mock_news = {
            'results': [
                {
                    'title': 'New AI Model Announced',
                    'url': 'https://news.com/ai-model',
                    'source': 'Tech News',
                    'published': '2025-01-08'
                }
            ],
            'total_results': 1
        }
        
        with patch.object(web_search_tool, '_perform_search', return_value=mock_news):
            result = await web_search_tool.execute(params)
            
            assert result['status'] == 'success'
            assert result.get('search_type') == 'news'
    
    @pytest.mark.asyncio
    async def test_autocomplete_suggestions(self, web_search_tool):
        """Test search query autocomplete."""
        query = "Python pro"
        
        mock_suggestions = [
            "Python programming",
            "Python projects",
            "Python programming language",
            "Python programming tutorial"
        ]
        
        with patch.object(web_search_tool, '_get_suggestions', return_value=mock_suggestions):
            result = await web_search_tool.get_suggestions(query)
            
            assert result['status'] == 'success'
            assert len(result['suggestions']) > 0
    
    @pytest.mark.asyncio
    async def test_related_searches(self, web_search_tool, mock_search_results):
        """Test getting related searches."""
        params = {"query": "Python programming"}
        
        mock_search_results['related_searches'] = [
            "Python tutorial",
            "Python for beginners",
            "Learn Python online"
        ]
        
        with patch.object(web_search_tool, '_perform_search', return_value=mock_search_results):
            result = await web_search_tool.execute(params)
            
            assert 'related_searches' in result
            assert len(result['related_searches']) > 0
    
    @pytest.mark.parametrize("provider,expected_endpoint", [
        ("google", "googleapis.com"),
        ("bing", "api.bing.microsoft.com"),
        ("duckduckgo", "duckduckgo.com")
    ])
    @pytest.mark.asyncio
    async def test_search_providers(self, web_search_tool, provider, expected_endpoint):
        """Test different search providers."""
        web_search_tool.provider = provider
        
        endpoint = web_search_tool.get_endpoint()
        assert expected_endpoint in endpoint