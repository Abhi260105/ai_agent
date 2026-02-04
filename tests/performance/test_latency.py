"""
Performance tests for response time and latency
"""

import pytest
import time
from typing import Dict, List
import statistics


class TestLatency:
    """Test response time for various operations"""
    
    @pytest.fixture
    def latency_threshold(self) -> Dict[str, float]:
        """Define acceptable latency thresholds in seconds"""
        return {
            "email_fetch": 2.0,
            "calendar_query": 1.5,
            "plan_generation": 5.0,
            "llm_response": 3.0,
            "tool_execution": 1.0
        }
    
    def test_email_fetch_latency(self, email_client, latency_threshold):
        """Test email fetching response time"""
        start_time = time.time()
        
        # Simulate email fetch
        emails = email_client.fetch_recent(limit=10)
        
        elapsed = time.time() - start_time
        
        assert elapsed < latency_threshold["email_fetch"], \
            f"Email fetch took {elapsed:.2f}s, threshold: {latency_threshold['email_fetch']}s"
    
    def test_calendar_query_latency(self, calendar_client, latency_threshold):
        """Test calendar query response time"""
        start_time = time.time()
        
        # Simulate calendar query
        events = calendar_client.get_events(days=7)
        
        elapsed = time.time() - start_time
        
        assert elapsed < latency_threshold["calendar_query"], \
            f"Calendar query took {elapsed:.2f}s, threshold: {latency_threshold['calendar_query']}s"
    
    def test_llm_response_latency(self, llm_client, latency_threshold):
        """Test LLM response generation time"""
        start_time = time.time()
        
        # Simulate LLM request
        response = llm_client.generate(
            prompt="Summarize today's schedule",
            max_tokens=500
        )
        
        elapsed = time.time() - start_time
        
        assert elapsed < latency_threshold["llm_response"], \
            f"LLM response took {elapsed:.2f}s, threshold: {latency_threshold['llm_response']}s"
    
    def test_plan_generation_latency(self, planner, latency_threshold):
        """Test complete plan generation latency"""
        start_time = time.time()
        
        # Simulate full plan generation
        plan = planner.generate_daily_plan(
            date="2024-01-15",
            include_emails=True,
            include_calendar=True
        )
        
        elapsed = time.time() - start_time
        
        assert elapsed < latency_threshold["plan_generation"], \
            f"Plan generation took {elapsed:.2f}s, threshold: {latency_threshold['plan_generation']}s"
    
    def test_p95_latency(self, planner):
        """Test 95th percentile latency over multiple runs"""
        latencies = []
        num_runs = 20
        
        for _ in range(num_runs):
            start_time = time.time()
            planner.generate_daily_plan(date="2024-01-15")
            elapsed = time.time() - start_time
            latencies.append(elapsed)
        
        p95 = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
        
        assert p95 < 6.0, f"P95 latency {p95:.2f}s exceeds 6.0s threshold"
    
    def test_cold_start_latency(self, planner):
        """Test latency on cold start (first request)"""
        # Reset/restart the planner to simulate cold start
        planner.reset()
        
        start_time = time.time()
        plan = planner.generate_daily_plan(date="2024-01-15")
        elapsed = time.time() - start_time
        
        # Cold start should be slower but still reasonable
        assert elapsed < 10.0, f"Cold start took {elapsed:.2f}s, should be under 10s"
