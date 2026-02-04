"""
Performance tests for throughput and concurrent request handling
"""

import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List


class TestThroughput:
    """Test system throughput under concurrent load"""
    
    def test_concurrent_email_fetches(self, email_client):
        """Test handling multiple concurrent email fetches"""
        num_concurrent = 10
        
        def fetch_emails():
            return email_client.fetch_recent(limit=5)
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(fetch_emails) for _ in range(num_concurrent)]
            results = [f.result() for f in as_completed(futures)]
        
        elapsed = time.time() - start_time
        
        # All requests should complete successfully
        assert len(results) == num_concurrent
        
        # Should handle concurrent requests reasonably fast
        assert elapsed < 5.0, f"Concurrent fetches took {elapsed:.2f}s"
    
    def test_concurrent_plan_generation(self, planner):
        """Test concurrent plan generation requests"""
        num_concurrent = 5
        dates = [f"2024-01-{15+i}" for i in range(num_concurrent)]
        
        def generate_plan(date):
            return planner.generate_daily_plan(date=date)
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(generate_plan, date) for date in dates]
            results = [f.result() for f in as_completed(futures)]
        
        elapsed = time.time() - start_time
        
        assert len(results) == num_concurrent
        # Should be faster than sequential execution
        assert elapsed < num_concurrent * 5.0
    
    @pytest.mark.asyncio
    async def test_async_throughput(self, async_planner):
        """Test async operation throughput"""
        num_requests = 20
        
        async def generate_plan_async(date):
            return await async_planner.generate_daily_plan(date=date)
        
        dates = [f"2024-01-{i}" for i in range(1, num_requests + 1)]
        
        start_time = time.time()
        
        tasks = [generate_plan_async(date) for date in dates]
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        
        assert len(results) == num_requests
        
        # Calculate throughput
        throughput = num_requests / elapsed
        
        assert throughput > 2.0, f"Throughput {throughput:.2f} req/s is too low"
    
    def test_requests_per_second(self, planner):
        """Measure sustained requests per second"""
        duration = 10  # seconds
        request_count = 0
        
        start_time = time.time()
        
        while time.time() - start_time < duration:
            planner.generate_daily_plan(date="2024-01-15", quick_mode=True)
            request_count += 1
        
        elapsed = time.time() - start_time
        rps = request_count / elapsed
        
        assert rps > 1.0, f"Sustained RPS {rps:.2f} is below minimum threshold"
    
    def test_batch_processing_throughput(self, planner):
        """Test throughput of batch processing"""
        dates = [f"2024-01-{i}" for i in range(1, 31)]  # 30 days
        
        start_time = time.time()
        
        results = planner.generate_batch_plans(dates=dates)
        
        elapsed = time.time() - start_time
        
        assert len(results) == 30
        
        # Batch processing should be efficient
        avg_time_per_plan = elapsed / len(results)
        assert avg_time_per_plan < 3.0, \
            f"Average time per plan {avg_time_per_plan:.2f}s is too high"
