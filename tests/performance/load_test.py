"""
Load testing and stress testing
"""

import pytest
import time
from concurrent.futures import ThreadPoolExecutor
import random


class TestLoadTesting:
    """Stress tests and load testing scenarios"""
    
    def test_sustained_load(self, planner):
        """Test system under sustained load"""
        duration = 60  # 1 minute
        num_workers = 5
        
        results = {
            "success": 0,
            "failure": 0,
            "total_time": 0
        }
        
        def worker():
            start = time.time()
            try:
                plan = planner.generate_daily_plan(
                    date=f"2024-01-{random.randint(1, 28)}"
                )
                results["success"] += 1
                results["total_time"] += time.time() - start
            except Exception as e:
                results["failure"] += 1
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            while time.time() - start_time < duration:
                executor.submit(worker)
                time.sleep(0.1)  # Small delay between submissions
        
        # Calculate metrics
        total_requests = results["success"] + results["failure"]
        success_rate = results["success"] / total_requests if total_requests > 0 else 0
        avg_response_time = results["total_time"] / results["success"] if results["success"] > 0 else 0
        
        # Assert quality metrics
        assert success_rate > 0.95, f"Success rate {success_rate:.2%} is too low"
        assert avg_response_time < 5.0, f"Average response time {avg_response_time:.2f}s is too high"
    
    def test_spike_load(self, planner):
        """Test system response to sudden traffic spike"""
        normal_load = 2
        spike_load = 20
        
        def generate_load(num_concurrent):
            with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
                futures = [
                    executor.submit(planner.generate_daily_plan, date="2024-01-15")
                    for _ in range(num_concurrent)
                ]
                results = [f.result() for f in futures]
            return len(results)
        
        # Normal load
        start = time.time()
        normal_count = generate_load(normal_load)
        normal_time = time.time() - start
        
        # Spike load
        start = time.time()
        spike_count = generate_load(spike_load)
        spike_time = time.time() - start
        
        # System should handle spike without complete failure
        assert spike_count == spike_load, "System failed under spike load"
        
        # Response time degradation should be reasonable
        time_ratio = spike_time / normal_time
        load_ratio = spike_load / normal_load
        
        # Time shouldn't increase more than load increase + 50%
        assert time_ratio < load_ratio * 1.5, \
            f"Performance degraded too much under load: {time_ratio:.2f}x slower"
    
    def test_gradual_ramp_up(self, planner):
        """Test system behavior under gradually increasing load"""
        max_concurrent = 15
        step_duration = 10  # seconds
        
        metrics = []
        
        for concurrent in range(1, max_concurrent + 1, 2):
            start_time = time.time()
            success_count = 0
            
            with ThreadPoolExecutor(max_workers=concurrent) as executor:
                while time.time() - start_time < step_duration:
                    try:
                        executor.submit(
                            planner.generate_daily_plan,
                            date="2024-01-15"
                        ).result(timeout=10)
                        success_count += 1
                    except:
                        pass
            
            metrics.append({
                "concurrent": concurrent,
                "throughput": success_count / step_duration
            })
        
        # Throughput should increase with concurrency (up to a point)
        # Check that we don't see dramatic drops
        for i in range(1, len(metrics)):
            if metrics[i]["concurrent"] < 8:  # Before saturation
                assert metrics[i]["throughput"] >= metrics[i-1]["throughput"] * 0.7, \
                    "Throughput dropped too much with increased concurrency"
    
    def test_error_recovery(self, planner):
        """Test system recovery after errors"""
        
        # Inject failures
        planner.set_failure_rate(0.5)  # 50% failure rate
        
        success_count = 0
        for _ in range(20):
            try:
                planner.generate_daily_plan(date="2024-01-15")
                success_count += 1
            except:
                pass
        
        # Reset to normal
        planner.set_failure_rate(0.0)
        
        # System should recover
        recovery_success = 0
        for _ in range(10):
            try:
                planner.generate_daily_plan(date="2024-01-15")
                recovery_success += 1
            except:
                pass
        
        recovery_rate = recovery_success / 10
        assert recovery_rate > 0.9, f"System didn't recover well: {recovery_rate:.2%} success"
    
    @pytest.mark.slow
    def test_endurance(self, planner):
        """Long-running endurance test"""
        duration = 300  # 5 minutes
        num_workers = 3
        
        start_time = time.time()
        request_count = 0
        error_count = 0
        
        def worker():
            nonlocal request_count, error_count
            try:
                planner.generate_daily_plan(date="2024-01-15")
                request_count += 1
            except:
                error_count += 1
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            while time.time() - start_time < duration:
                executor.submit(worker)
                time.sleep(0.5)
        
        total_requests = request_count + error_count
        success_rate = request_count / total_requests if total_requests > 0 else 0
        
        assert success_rate > 0.95, f"Endurance test success rate {success_rate:.2%} too low"
        assert request_count > 100, "Not enough requests completed during endurance test"
