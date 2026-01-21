"""
LLM Service - Interface for Large Language Model providers

Supports multiple LLM providers:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Local models (Llama, etc.)
"""

import os
import logging
from typing import Dict, List, Any, Optional, AsyncIterator
from abc import ABC, abstractmethod
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate text from prompt."""
        pass
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Generate response in chat format."""
        pass
    
    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """Generate text embedding."""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI provider."""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model = "gpt-4"
        self.base_url = "https://api.openai.com/v1"
        
        if not self.api_key:
            logger.warning("OpenAI API key not found")
    
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate text using OpenAI."""
        try:
            # Lazy import to avoid dependency issues
            import openai
            
            client = openai.AsyncOpenAI(api_key=self.api_key)
            
            response = await client.chat.completions.create(
                model=kwargs.get('model', self.model),
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 1000),
                top_p=kwargs.get('top_p', 1.0),
                frequency_penalty=kwargs.get('frequency_penalty', 0.0),
                presence_penalty=kwargs.get('presence_penalty', 0.0),
                stop=kwargs.get('stop_sequences'),
            )
            
            return {
                'content': response.choices[0].message.content,
                'tokens': response.usage.total_tokens,
                'model': response.model,
                'finish_reason': response.choices[0].finish_reason
            }
            
        except ImportError:
            logger.error("OpenAI package not installed. Install with: pip install openai")
            return {
                'content': None,
                'error': "OpenAI package not installed"
            }
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return {
                'content': None,
                'error': str(e)
            }
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Chat completion using OpenAI."""
        try:
            import openai
            
            client = openai.AsyncOpenAI(api_key=self.api_key)
            
            response = await client.chat.completions.create(
                model=kwargs.get('model', self.model),
                messages=messages,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 1000),
                functions=kwargs.get('functions'),
                function_call=kwargs.get('function_call'),
            )
            
            result = {
                'content': response.choices[0].message.content,
                'tokens': response.usage.total_tokens,
                'model': response.model,
                'finish_reason': response.choices[0].finish_reason
            }
            
            # Check for function call
            if response.choices[0].message.function_call:
                result['function_call'] = {
                    'name': response.choices[0].message.function_call.name,
                    'arguments': response.choices[0].message.function_call.arguments
                }
            
            return result
            
        except Exception as e:
            logger.error(f"OpenAI chat error: {str(e)}")
            return {'content': None, 'error': str(e)}
    
    async def get_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI."""
        try:
            import openai
            
            client = openai.AsyncOpenAI(api_key=self.api_key)
            
            response = await client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"OpenAI embedding error: {str(e)}")
            return []


class AnthropicProvider(BaseLLMProvider):
    """Anthropic (Claude) API provider."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Anthropic provider."""
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.model = "claude-3-opus-20240229"
        
        if not self.api_key:
            logger.warning("Anthropic API key not found")
    
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate text using Claude."""
        try:
            import anthropic
            
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            
            response = await client.messages.create(
                model=kwargs.get('model', self.model),
                max_tokens=kwargs.get('max_tokens', 1000),
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get('temperature', 0.7),
                system=kwargs.get('system_message'),
            )
            
            return {
                'content': response.content[0].text,
                'tokens': response.usage.input_tokens + response.usage.output_tokens,
                'model': response.model,
                'finish_reason': response.stop_reason
            }
            
        except ImportError:
            logger.error("Anthropic package not installed. Install with: pip install anthropic")
            return {'content': None, 'error': "Anthropic package not installed"}
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            return {'content': None, 'error': str(e)}
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Chat using Claude."""
        try:
            import anthropic
            
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            
            response = await client.messages.create(
                model=kwargs.get('model', self.model),
                max_tokens=kwargs.get('max_tokens', 1000),
                messages=messages,
                temperature=kwargs.get('temperature', 0.7),
            )
            
            return {
                'content': response.content[0].text,
                'tokens': response.usage.input_tokens + response.usage.output_tokens,
                'model': response.model,
                'finish_reason': response.stop_reason
            }
            
        except Exception as e:
            logger.error(f"Anthropic chat error: {str(e)}")
            return {'content': None, 'error': str(e)}
    
    async def get_embedding(self, text: str) -> List[float]:
        """Anthropic doesn't provide embeddings, use alternative."""
        logger.warning("Anthropic doesn't provide embeddings, use OpenAI or local model")
        return []


class LocalLLMProvider(BaseLLMProvider):
    """Local LLM provider (Llama, etc.)."""
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize local LLM provider."""
        self.model_path = model_path or os.getenv('LOCAL_MODEL_PATH')
        self.model = None
        logger.info("Local LLM provider initialized")
    
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate text using local model."""
        try:
            # This is a placeholder for local model integration
            # You would integrate with llama-cpp-python, transformers, etc.
            logger.warning("Local LLM generation not fully implemented")
            
            return {
                'content': f"Local LLM response to: {prompt[:50]}...",
                'tokens': 100,
                'model': 'local',
                'finish_reason': 'stop'
            }
            
        except Exception as e:
            logger.error(f"Local LLM error: {str(e)}")
            return {'content': None, 'error': str(e)}
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Chat using local model."""
        last_message = messages[-1]['content'] if messages else ""
        return await self.generate(last_message, **kwargs)
    
    async def get_embedding(self, text: str) -> List[float]:
        """Generate embedding using local model."""
        try:
            from sentence_transformers import SentenceTransformer
            
            model = SentenceTransformer('all-mpnet-base-v2')
            embedding = model.encode(text)
            return embedding.tolist()
            
        except ImportError:
            logger.error("sentence-transformers not installed")
            return []
        except Exception as e:
            logger.error(f"Local embedding error: {str(e)}")
            return []


class LLMService:
    """
    Main LLM service that manages different providers.
    """
    
    def __init__(self, provider: str = "openai", **kwargs):
        """
        Initialize LLM service.
        
        Args:
            provider: LLM provider name (openai, anthropic, local)
            **kwargs: Additional provider-specific arguments
        """
        self.provider_name = provider
        self.provider = self._create_provider(provider, **kwargs)
        self.call_history = []
        
        logger.info(f"LLM Service initialized with provider: {provider}")
    
    def _create_provider(self, provider: str, **kwargs) -> BaseLLMProvider:
        """Create provider instance."""
        providers = {
            'openai': OpenAIProvider,
            'anthropic': AnthropicProvider,
            'local': LocalLLMProvider
        }
        
        if provider not in providers:
            logger.warning(f"Unknown provider: {provider}, defaulting to OpenAI")
            provider = 'openai'
        
        return providers[provider](**kwargs)
    
    def set_provider(self, provider: str, **kwargs):
        """Switch to a different provider."""
        self.provider_name = provider
        self.provider = self._create_provider(provider, **kwargs)
        logger.info(f"Switched to provider: {provider}")
    
    def set_model(self, model: str):
        """Set the model to use."""
        if hasattr(self.provider, 'model'):
            self.provider.model = model
            logger.info(f"Set model to: {model}")
    
    async def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        max_retries: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input prompt
            system_message: System message for context
            temperature: Randomness (0-1)
            max_tokens: Maximum tokens to generate
            max_retries: Number of retries on failure
            **kwargs: Additional provider-specific arguments
            
        Returns:
            Dictionary with generated content and metadata
        """
        if system_message:
            kwargs['system_message'] = system_message
        
        kwargs.update({
            'temperature': temperature,
            'max_tokens': max_tokens
        })
        
        # Retry mechanism
        for attempt in range(max_retries):
            try:
                result = await self.provider.generate(prompt, **kwargs)
                
                # Log call
                self.call_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'provider': self.provider_name,
                    'prompt_length': len(prompt),
                    'tokens': result.get('tokens', 0),
                    'success': result.get('content') is not None
                })
                
                if result.get('content') is None and attempt < max_retries - 1:
                    logger.warning(f"Attempt {attempt + 1} failed, retrying...")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                
                return result
                
            except Exception as e:
                logger.error(f"Generation error (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    return {'content': None, 'error': str(e)}
        
        return {'content': None, 'error': 'Max retries exceeded'}
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate chat response.
        
        Args:
            messages: List of chat messages
            temperature: Randomness (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with response and metadata
        """
        kwargs.update({
            'temperature': temperature,
            'max_tokens': max_tokens
        })
        
        result = await self.provider.chat(messages, **kwargs)
        
        # Log call
        self.call_history.append({
            'timestamp': datetime.now().isoformat(),
            'provider': self.provider_name,
            'message_count': len(messages),
            'tokens': result.get('tokens', 0),
            'success': result.get('content') is not None
        })
        
        return result
    
    async def generate_stream(
        self,
        prompt: str,
        **kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Generate text with streaming.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional arguments
            
        Yields:
            Chunks of generated text
        """
        # This is a simplified streaming implementation
        # Real implementation would depend on provider's streaming API
        result = await self.generate(prompt, **kwargs)
        
        if result.get('content'):
            # Simulate streaming by yielding chunks
            content = result['content']
            chunk_size = 10
            
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                yield {
                    'content': chunk,
                    'done': i + chunk_size >= len(content)
                }
                await asyncio.sleep(0.05)  # Simulate delay
    
    async def get_embedding(self, text: str) -> List[float]:
        """
        Generate text embedding.
        
        Args:
            text: Input text
            
        Returns:
            List of float values representing the embedding
        """
        return await self.provider.get_embedding(text)
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embeddings
        """
        embeddings = []
        for text in texts:
            embedding = await self.get_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Input text
            
        Returns:
            Approximate token count
        """
        # Rough estimation: 1 token ≈ 4 characters
        # For accurate counting, use tiktoken for OpenAI models
        try:
            import tiktoken
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except ImportError:
            # Fallback to rough estimation
            return len(text) // 4
    
    def calculate_cost(self, tokens: int, model: str = "gpt-4") -> float:
        """
        Calculate approximate cost for API usage.
        
        Args:
            tokens: Number of tokens used
            model: Model name
            
        Returns:
            Estimated cost in USD
        """
        # Prices per 1K tokens (as of 2024)
        prices = {
            'gpt-4': 0.03,
            'gpt-3.5-turbo': 0.002,
            'claude-3-opus': 0.015,
            'claude-3-sonnet': 0.003,
        }
        
        price_per_1k = prices.get(model, 0.01)
        return (tokens / 1000) * price_per_1k
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get usage statistics."""
        if not self.call_history:
            return {
                'total_calls': 0,
                'total_tokens': 0,
                'success_rate': 0
            }
        
        total_calls = len(self.call_history)
        total_tokens = sum(call.get('tokens', 0) for call in self.call_history)
        successful_calls = sum(1 for call in self.call_history if call.get('success'))
        
        return {
            'total_calls': total_calls,
            'total_tokens': total_tokens,
            'success_rate': (successful_calls / total_calls) * 100 if total_calls > 0 else 0,
            'estimated_cost': self.calculate_cost(total_tokens)
        }
    
    def clear_history(self):
        """Clear call history."""
        self.call_history = []
        logger.info("Call history cleared")


# Global instance
_llm_service = None


def get_llm_service(provider: str = "openai", **kwargs) -> LLMService:
    """
    Get or create global LLM service instance.
    
    Args:
        provider: LLM provider name
        **kwargs: Additional provider arguments
        
    Returns:
        LLM service instance
    """
    global _llm_service
    
    if _llm_service is None:
        _llm_service = LLMService(provider=provider, **kwargs)
    
    return _llm_service