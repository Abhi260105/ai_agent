"""
Unit tests for LLM Service.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock


class TestLLMService:
    """Test suite for LLM Service."""
    
    @pytest.fixture
    def llm_service(self):
        """Create an LLM Service instance for testing."""
        from app.services.llm_service import LLMService
        return LLMService(provider="openai")
    
    @pytest.fixture
    def mock_llm_response(self):
        """Mock LLM response."""
        return {
            "content": "This is a generated response from the LLM.",
            "tokens": 150,
            "model": "gpt-4",
            "finish_reason": "stop"
        }
    
    def test_llm_service_initialization(self, llm_service):
        """Test LLM service initializes correctly."""
        assert llm_service is not None
        assert llm_service.provider == "openai"
        assert hasattr(llm_service, 'generate')
    
    @pytest.mark.asyncio
    async def test_simple_generation(self, llm_service, mock_llm_response):
        """Test simple text generation."""
        prompt = "What is Python?"
        
        with patch.object(llm_service, '_call_api', return_value=mock_llm_response):
            result = await llm_service.generate(prompt)
            
            assert result['content'] is not None
            assert len(result['content']) > 0
            assert 'tokens' in result
    
    @pytest.mark.asyncio
    async def test_generation_with_system_message(self, llm_service, mock_llm_response):
        """Test generation with system message."""
        prompt = "Explain quantum computing"
        system_message = "You are a helpful physics teacher"
        
        with patch.object(llm_service, '_call_api', return_value=mock_llm_response):
            result = await llm_service.generate(
                prompt,
                system_message=system_message
            )
            
            assert result['content'] is not None
    
    @pytest.mark.asyncio
    async def test_generation_with_temperature(self, llm_service, mock_llm_response):
        """Test generation with custom temperature."""
        prompt = "Write a creative story"
        
        with patch.object(llm_service, '_call_api', return_value=mock_llm_response) as mock_call:
            await llm_service.generate(prompt, temperature=0.9)
            
            # Verify temperature was passed
            call_args = mock_call.call_args
            assert call_args is not None
    
    @pytest.mark.asyncio
    async def test_generation_with_max_tokens(self, llm_service, mock_llm_response):
        """Test generation with token limit."""
        prompt = "Summarize this article"
        
        with patch.object(llm_service, '_call_api', return_value=mock_llm_response):
            result = await llm_service.generate(prompt, max_tokens=100)
            
            assert result['tokens'] <= 150  # Mock response has 150 tokens
    
    @pytest.mark.asyncio
    async def test_streaming_generation(self, llm_service):
        """Test streaming generation."""
        prompt = "Tell me a story"
        
        async def mock_stream():
            chunks = ["Once ", "upon ", "a ", "time..."]
            for chunk in chunks:
                yield {"content": chunk, "done": False}
            yield {"content": "", "done": True}
        
        with patch.object(llm_service, '_stream_api', return_value=mock_stream()):
            chunks = []
            async for chunk in llm_service.generate_stream(prompt):
                chunks.append(chunk)
            
            assert len(chunks) > 0
    
    @pytest.mark.asyncio
    async def test_chat_conversation(self, llm_service, mock_llm_response):
        """Test multi-turn chat conversation."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi! How can I help?"},
            {"role": "user", "content": "What's the weather?"}
        ]
        
        with patch.object(llm_service, '_call_api', return_value=mock_llm_response):
            result = await llm_service.chat(messages)
            
            assert result['content'] is not None
    
    @pytest.mark.asyncio
    async def test_function_calling(self, llm_service):
        """Test function calling capability."""
        prompt = "What's the weather in New York?"
        
        functions = [{
            "name": "get_weather",
            "description": "Get weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                }
            }
        }]
        
        mock_response = {
            "content": "",
            "function_call": {
                "name": "get_weather",
                "arguments": '{"location": "New York"}'
            }
        }
        
        with patch.object(llm_service, '_call_api', return_value=mock_response):
            result = await llm_service.generate(prompt, functions=functions)
            
            assert 'function_call' in result
            assert result['function_call']['name'] == 'get_weather'
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, llm_service):
        """Test handling of API errors."""
        prompt = "Test prompt"
        
        with patch.object(llm_service, '_call_api', side_effect=Exception("API Error")):
            with pytest.raises(Exception):
                await llm_service.generate(prompt)
    
    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, llm_service):
        """Test rate limit error handling."""
        prompt = "Test prompt"
        
        with patch.object(llm_service, '_call_api', side_effect=Exception("Rate limit exceeded")):
            with pytest.raises(Exception) as exc_info:
                await llm_service.generate(prompt)
            
            assert "rate limit" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_token_counting(self, llm_service):
        """Test token counting functionality."""
        text = "This is a test sentence with multiple words."
        
        token_count = llm_service.count_tokens(text)
        
        assert token_count > 0
        assert isinstance(token_count, int)
    
    @pytest.mark.asyncio
    async def test_embedding_generation(self, llm_service):
        """Test text embedding generation."""
        text = "This is sample text for embedding"
        
        mock_embedding = [0.1, 0.2, 0.3] * 256  # 768 dimensions
        
        with patch.object(llm_service, '_get_embedding', return_value=mock_embedding):
            embedding = await llm_service.get_embedding(text)
            
            assert len(embedding) > 0
            assert all(isinstance(x, (int, float)) for x in embedding)
    
    @pytest.mark.asyncio
    async def test_batch_embeddings(self, llm_service):
        """Test batch embedding generation."""
        texts = [
            "First text",
            "Second text",
            "Third text"
        ]
        
        mock_embeddings = [[0.1] * 768 for _ in texts]
        
        with patch.object(llm_service, '_get_embeddings_batch', return_value=mock_embeddings):
            embeddings = await llm_service.get_embeddings(texts)
            
            assert len(embeddings) == len(texts)
    
    @pytest.mark.asyncio
    async def test_provider_switching(self, llm_service):
        """Test switching between LLM providers."""
        # Start with OpenAI
        assert llm_service.provider == "openai"
        
        # Switch to Anthropic
        llm_service.set_provider("anthropic")
        assert llm_service.provider == "anthropic"
        
        # Switch to local
        llm_service.set_provider("local")
        assert llm_service.provider == "local"
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self, llm_service, mock_llm_response):
        """Test retry mechanism on transient failures."""
        prompt = "Test prompt"
        
        call_count = 0
        
        async def mock_call_with_retry(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary error")
            return mock_llm_response
        
        with patch.object(llm_service, '_call_api', side_effect=mock_call_with_retry):
            result = await llm_service.generate(prompt, max_retries=3)
            
            assert result['content'] is not None
            assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_context_window_limit(self, llm_service):
        """Test handling of context window limits."""
        # Create a very long prompt
        long_prompt = "word " * 10000
        
        with pytest.raises(Exception) as exc_info:
            await llm_service.generate(long_prompt)
        
        assert "context" in str(exc_info.value).lower() or "tokens" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_stop_sequences(self, llm_service, mock_llm_response):
        """Test generation with stop sequences."""
        prompt = "Count to 10"
        stop_sequences = ["5", "five"]
        
        with patch.object(llm_service, '_call_api', return_value=mock_llm_response):
            result = await llm_service.generate(
                prompt,
                stop_sequences=stop_sequences
            )
            
            assert result['content'] is not None
    
    @pytest.mark.asyncio
    async def test_json_mode(self, llm_service):
        """Test JSON output mode."""
        prompt = "Generate a JSON object with name and age"
        
        mock_response = {
            "content": '{"name": "Alice", "age": 30}',
            "tokens": 20
        }
        
        with patch.object(llm_service, '_call_api', return_value=mock_response):
            result = await llm_service.generate(prompt, response_format="json")
            
            import json
            parsed = json.loads(result['content'])
            assert 'name' in parsed
            assert 'age' in parsed
    
    @pytest.mark.asyncio
    async def test_model_selection(self, llm_service):
        """Test selecting specific model."""
        models = ["gpt-4", "gpt-3.5-turbo", "claude-3"]
        
        for model in models:
            llm_service.set_model(model)
            assert llm_service.model == model
    
    @pytest.mark.asyncio
    async def test_cost_calculation(self, llm_service, mock_llm_response):
        """Test cost calculation for API usage."""
        prompt = "Test prompt"
        
        with patch.object(llm_service, '_call_api', return_value=mock_llm_response):
            result = await llm_service.generate(prompt)
            
            cost = llm_service.calculate_cost(result['tokens'], model="gpt-4")
            assert cost >= 0
    
    @pytest.mark.parametrize("provider,model", [
        ("openai", "gpt-4"),
        ("anthropic", "claude-3-opus"),
        ("local", "llama-2-7b")
    ])
    @pytest.mark.asyncio
    async def test_multiple_providers(self, provider, model, mock_llm_response):
        """Test different provider and model combinations."""
        from app.services.llm_service import LLMService
        service = LLMService(provider=provider)
        service.set_model(model)
        
        with patch.object(service, '_call_api', return_value=mock_llm_response):
            result = await service.generate("Test")
            assert result['content'] is not None