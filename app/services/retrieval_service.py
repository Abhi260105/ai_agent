"""
Retrieval Service - RAG System
Advanced retrieval with re-ranking, fusion, and relevance scoring
"""
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from collections import defaultdict

from app.services.embedding_service import embedding_service
from app.agent.memory import memory_manager
from app.utils.logger import get_logger

logger = get_logger("services.retrieval")


class RetrievalService:
    """
    Retrieval-Augmented Generation (RAG) system
    
    Features:
    - Semantic search
    - Re-ranking algorithms
    - Context window management
    - Relevance scoring
    - Multi-query fusion
    - Hybrid search (dense + sparse)
    """
    
    def __init__(self, context_window_size: int = 4096):
        self.logger = logger
        self.embeddings = embedding_service
        self.memory = memory_manager
        self.context_window_size = context_window_size
        
        self.logger.info("Retrieval service initialized")
    
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        min_relevance: float = 0.5,
        rerank: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for query
        
        Args:
            query: Search query
            top_k: Number of results
            min_relevance: Minimum relevance threshold
            rerank: Apply re-ranking
            
        Returns:
            List of retrieved documents with scores
        """
        self.logger.debug(
            "Retrieving documents",
            query=query[:50],
            top_k=top_k
        )
        
        # Initial retrieval using semantic search
        results = self.memory.retrieve_similar_tasks(
            query=query,
            limit=top_k * 2,  # Retrieve more for re-ranking
            min_similarity=min_relevance
        )
        
        if not results:
            self.logger.info("No results found")
            return []
        
        # Re-rank if enabled
        if rerank:
            results = self._rerank_results(query, results)
        
        # Calculate relevance scores
        for result in results:
            result["relevance_score"] = self._calculate_relevance(
                query, result
            )
        
        # Sort by relevance
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return results[:top_k]
    
    def retrieve_with_context(
        self,
        query: str,
        current_context: Dict[str, Any],
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve with awareness of current context
        
        Args:
            query: Search query
            current_context: Current execution context
            top_k: Number of results
            
        Returns:
            Contextually relevant documents
        """
        # Expand query with context
        expanded_query = self._expand_query_with_context(query, current_context)
        
        # Retrieve
        results = self.retrieve(
            query=expanded_query,
            top_k=top_k,
            rerank=True
        )
        
        # Filter by context relevance
        filtered = self._filter_by_context(results, current_context)
        
        return filtered
    
    def multi_query_fusion(
        self,
        queries: List[str],
        top_k: int = 5,
        fusion_method: str = "reciprocal_rank"
    ) -> List[Dict[str, Any]]:
        """
        Retrieve and fuse results from multiple queries
        
        Args:
            queries: List of query variations
            top_k: Number of final results
            fusion_method: Fusion algorithm (reciprocal_rank, max, average)
            
        Returns:
            Fused ranked results
        """
        self.logger.debug(
            "Multi-query fusion",
            num_queries=len(queries),
            method=fusion_method
        )
        
        # Retrieve for each query
        all_results = []
        for query in queries:
            results = self.retrieve(query, top_k=top_k * 2, rerank=False)
            all_results.append(results)
        
        # Fuse results
        if fusion_method == "reciprocal_rank":
            fused = self._reciprocal_rank_fusion(all_results)
        elif fusion_method == "max":
            fused = self._max_score_fusion(all_results)
        elif fusion_method == "average":
            fused = self._average_score_fusion(all_results)
        else:
            raise ValueError(f"Unknown fusion method: {fusion_method}")
        
        return fused[:top_k]
    
    def hybrid_search(
        self,
        query: str,
        keywords: List[str],
        top_k: int = 5,
        semantic_weight: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Combine semantic (dense) and keyword (sparse) search
        
        Args:
            query: Semantic query
            keywords: Keyword filters
            top_k: Number of results
            semantic_weight: Weight for semantic score (0-1)
            
        Returns:
            Hybrid ranked results
        """
        # Semantic search
        semantic_results = self.retrieve(query, top_k=top_k * 2, rerank=False)
        
        # Keyword scoring
        keyword_weight = 1.0 - semantic_weight
        
        for result in semantic_results:
            # Calculate keyword match score
            text = result.get("text", "").lower()
            keyword_score = sum(
                1 for kw in keywords if kw.lower() in text
            ) / len(keywords) if keywords else 0
            
            # Combine scores
            semantic_score = result.get("similarity", 0)
            result["hybrid_score"] = (
                semantic_score * semantic_weight +
                keyword_score * keyword_weight
            )
        
        # Sort by hybrid score
        semantic_results.sort(key=lambda x: x["hybrid_score"], reverse=True)
        
        return semantic_results[:top_k]
    
    def retrieve_for_context_window(
        self,
        query: str,
        max_tokens: int = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Retrieve documents that fit within context window
        
        Args:
            query: Search query
            max_tokens: Maximum tokens (default: context_window_size)
            
        Returns:
            (results, total_tokens_used)
        """
        max_tokens = max_tokens or self.context_window_size
        
        # Retrieve candidates
        candidates = self.retrieve(query, top_k=20, rerank=True)
        
        # Select documents that fit in window
        selected = []
        total_tokens = 0
        
        for doc in candidates:
            # Estimate tokens (rough: 1 token ≈ 4 chars)
            doc_tokens = len(doc.get("text", "")) // 4
            
            if total_tokens + doc_tokens <= max_tokens:
                selected.append(doc)
                total_tokens += doc_tokens
            else:
                break
        
        self.logger.debug(
            "Context window filled",
            documents=len(selected),
            tokens_used=total_tokens
        )
        
        return selected, total_tokens
    
    # =========================================================================
    # RE-RANKING
    # =========================================================================
    
    def _rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Re-rank results using cross-encoder or advanced scoring
        
        Args:
            query: Original query
            results: Initial results
            
        Returns:
            Re-ranked results
        """
        # Simple re-ranking based on multiple factors
        query_emb = self.embeddings.embed(query)
        
        for result in results:
            # Re-calculate similarity with query embedding
            text_emb = self.embeddings.embed(result.get("text", ""))
            similarity = self.embeddings.similarity(query_emb, text_emb)
            
            # Factors for re-ranking
            recency_score = self._calculate_recency_score(result)
            usage_score = self._calculate_usage_score(result)
            
            # Combined score
            result["rerank_score"] = (
                similarity * 0.6 +
                recency_score * 0.2 +
                usage_score * 0.2
            )
        
        # Sort by rerank score
        results.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
        
        return results
    
    def _calculate_recency_score(self, result: Dict[str, Any]) -> float:
        """Calculate recency score (newer = higher)"""
        from datetime import datetime
        
        timestamp_str = result.get("timestamp")
        if not timestamp_str:
            return 0.5
        
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            age_days = (datetime.now() - timestamp).days
            
            # Decay score over time (30 days half-life)
            return np.exp(-age_days / 30)
            
        except:
            return 0.5
    
    def _calculate_usage_score(self, result: Dict[str, Any]) -> float:
        """Calculate usage/popularity score"""
        # Placeholder: could track document access counts
        return 0.5
    
    def _calculate_relevance(
        self,
        query: str,
        result: Dict[str, Any]
    ) -> float:
        """
        Calculate comprehensive relevance score
        
        Considers:
        - Semantic similarity
        - Recency
        - Memory type
        - Tags match
        """
        # Base similarity
        similarity = result.get("similarity", 0)
        
        # Recency bonus
        recency = self._calculate_recency_score(result)
        
        # Memory type relevance
        memory_type = result.get("memory_type", "")
        type_score = {
            "success": 0.9,
            "task": 0.8,
            "failure": 0.7
        }.get(memory_type, 0.5)
        
        # Combined score
        relevance = (
            similarity * 0.5 +
            recency * 0.2 +
            type_score * 0.3
        )
        
        return relevance
    
    # =========================================================================
    # QUERY EXPANSION
    # =========================================================================
    
    def _expand_query_with_context(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """Expand query with context information"""
        expanded_parts = [query]
        
        # Add current task context
        if "current_task" in context:
            expanded_parts.append(context["current_task"])
        
        # Add recent steps context
        if "recent_steps" in context:
            steps = context["recent_steps"][-3:]  # Last 3 steps
            for step in steps:
                if "action" in step:
                    expanded_parts.append(step["action"])
        
        return " ".join(expanded_parts)
    
    def _filter_by_context(
        self,
        results: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Filter results by context relevance"""
        # Keep all for now; could add sophisticated filtering
        return results
    
    # =========================================================================
    # FUSION METHODS
    # =========================================================================
    
    def _reciprocal_rank_fusion(
        self,
        result_lists: List[List[Dict[str, Any]]],
        k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Reciprocal Rank Fusion (RRF)
        Combines rankings from multiple queries
        """
        # Collect all unique documents
        doc_scores = defaultdict(float)
        doc_data = {}
        
        for results in result_lists:
            for rank, doc in enumerate(results):
                doc_id = doc.get("text", str(rank))
                
                # RRF score: 1 / (k + rank)
                doc_scores[doc_id] += 1.0 / (k + rank + 1)
                
                # Store document data
                if doc_id not in doc_data:
                    doc_data[doc_id] = doc
        
        # Sort by RRF score
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Return documents with scores
        fused = []
        for doc_id, score in sorted_docs:
            doc = doc_data[doc_id].copy()
            doc["fusion_score"] = score
            fused.append(doc)
        
        return fused
    
    def _max_score_fusion(
        self,
        result_lists: List[List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Take maximum score across queries"""
        doc_scores = defaultdict(float)
        doc_data = {}
        
        for results in result_lists:
            for doc in results:
                doc_id = doc.get("text", "")
                score = doc.get("similarity", 0)
                
                doc_scores[doc_id] = max(doc_scores[doc_id], score)
                
                if doc_id not in doc_data:
                    doc_data[doc_id] = doc
        
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        fused = []
        for doc_id, score in sorted_docs:
            doc = doc_data[doc_id].copy()
            doc["fusion_score"] = score
            fused.append(doc)
        
        return fused
    
    def _average_score_fusion(
        self,
        result_lists: List[List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Average scores across queries"""
        doc_scores = defaultdict(list)
        doc_data = {}
        
        for results in result_lists:
            for doc in results:
                doc_id = doc.get("text", "")
                score = doc.get("similarity", 0)
                
                doc_scores[doc_id].append(score)
                
                if doc_id not in doc_data:
                    doc_data[doc_id] = doc
        
        # Calculate averages
        doc_avg_scores = {
            doc_id: np.mean(scores)
            for doc_id, scores in doc_scores.items()
        }
        
        sorted_docs = sorted(
            doc_avg_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        fused = []
        for doc_id, score in sorted_docs:
            doc = doc_data[doc_id].copy()
            doc["fusion_score"] = score
            fused.append(doc)
        
        return fused
    
    # =========================================================================
    # UTILITIES
    # =========================================================================
    
    def format_context_for_llm(
        self,
        results: List[Dict[str, Any]],
        max_length: int = 2000
    ) -> str:
        """
        Format retrieved documents for LLM context
        
        Args:
            results: Retrieved documents
            max_length: Maximum character length
            
        Returns:
            Formatted context string
        """
        if not results:
            return ""
        
        context_parts = ["# Relevant Context\n"]
        current_length = len(context_parts[0])
        
        for i, doc in enumerate(results):
            doc_text = doc.get("text", "")
            doc_type = doc.get("memory_type", "unknown")
            
            # Format document
            doc_str = f"\n## Document {i+1} (type: {doc_type})\n{doc_text}\n"
            
            # Check length
            if current_length + len(doc_str) > max_length:
                break
            
            context_parts.append(doc_str)
            current_length += len(doc_str)
        
        return "".join(context_parts)


# Global retrieval service instance
retrieval_service = RetrievalService()


if __name__ == "__main__":
    """Test retrieval service"""
    print("🔍 Testing Retrieval Service...")
    
    # Store some test memories first
    from app.agent.memory import memory_manager
    
    memory_manager.store_task_memory({
        "user_goal": "Send email to team about meeting",
        "status": "completed",
        "steps_completed": ["step_1", "step_2"],
        "duration_seconds": 10.5
    })
    
    memory_manager.store_task_memory({
        "user_goal": "Schedule meeting with John",
        "status": "completed",
        "steps_completed": ["step_1"],
        "duration_seconds": 5.0
    })
    
    # Test basic retrieval
    print("\n📥 Testing basic retrieval...")
    results = retrieval_service.retrieve(
        query="email task",
        top_k=3
    )
    print(f"   Results: {len(results)}")
    if results:
        print(f"   Top result relevance: {results[0].get('relevance_score', 0):.3f}")
    
    # Test multi-query fusion
    print("\n🔀 Testing multi-query fusion...")
    fused = retrieval_service.multi_query_fusion(
        queries=["email", "send message", "communicate"],
        top_k=3
    )
    print(f"   Fused results: {len(fused)}")
    
    # Test context window
    print("\n📏 Testing context window...")
    docs, tokens = retrieval_service.retrieve_for_context_window(
        query="meeting",
        max_tokens=500
    )
    print(f"   Documents: {len(docs)}")
    print(f"   Tokens used: {tokens}")
    
    # Test hybrid search
    print("\n🔍 Testing hybrid search...")
    hybrid = retrieval_service.hybrid_search(
        query="email task",
        keywords=["email", "team"],
        top_k=3
    )
    print(f"   Hybrid results: {len(hybrid)}")
    
    print("\n✅ Retrieval service test complete")