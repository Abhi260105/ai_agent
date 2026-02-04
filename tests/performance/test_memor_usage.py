"""
Performance tests for memory usage and resource management
"""

import pytest
import psutil
import os
import gc
from memory_profiler import memory_usage


class TestMemoryUsage:
    """Test memory consumption and resource management"""
    
    @pytest.fixture
    def process(self):
        """Get current process for memory monitoring"""
        return psutil.Process(os.getpid())
    
    def test_baseline_memory(self, process):
        """Establish baseline memory usage"""
        gc.collect()
        baseline = process.memory_info().rss / 1024 / 1024  # MB
        
        # Baseline should be reasonable
        assert baseline < 500, f"Baseline memory {baseline:.2f}MB is too high"
    
    def test_plan_generation_memory(self, planner, process):
        """Test memory usage during plan generation"""
        gc.collect()
        before = process.memory_info().rss / 1024 / 1024
        
        # Generate multiple plans
        for i in range(10):
            plan = planner.generate_daily_plan(date=f"2024-01-{i+1}")
        
        gc.collect()
        after = process.memory_info().rss / 1024 / 1024
        
        increase = after - before
        
        # Memory increase should be reasonable
        assert increase < 100, f"Memory increased by {increase:.2f}MB"
    
    def test_memory_leak_detection(self, planner, process):
        """Test for memory leaks over repeated operations"""
        gc.collect()
        measurements = []
        
        for i in range(50):
            planner.generate_daily_plan(date="2024-01-15")
            
            if i % 10 == 0:
                gc.collect()
                mem = process.memory_info().rss / 1024 / 1024
                measurements.append(mem)
        
        # Check if memory keeps growing
        # Allow some growth but not continuous leak
        first_half_avg = sum(measurements[:len(measurements)//2]) / (len(measurements)//2)
        second_half_avg = sum(measurements[len(measurements)//2:]) / (len(measurements)//2)
        
        growth = second_half_avg - first_half_avg
        
        assert growth < 50, f"Possible memory leak detected: {growth:.2f}MB growth"
    
    def test_large_dataset_memory(self, planner):
        """Test memory with large datasets"""
        
        def generate_large_batch():
            # Generate plans for a full year
            dates = [f"2024-{m:02d}-{d:02d}" 
                    for m in range(1, 13) 
                    for d in range(1, 29)]
            return planner.generate_batch_plans(dates=dates)
        
        # Measure memory usage
        mem_usage = memory_usage(generate_large_batch, interval=0.1)
        peak_memory = max(mem_usage)
        
        # Peak memory should be under 1GB
        assert peak_memory < 1024, f"Peak memory {peak_memory:.2f}MB exceeds limit"
    
    def test_cache_memory_limit(self, planner):
        """Test that caching doesn't consume excessive memory"""
        gc.collect()
        
        # Enable caching
        planner.enable_cache(max_size_mb=100)
        
        # Fill cache
        for i in range(100):
            planner.generate_daily_plan(date=f"2024-{i//31 + 1:02d}-{i%31 + 1:02d}")
        
        gc.collect()
        cache_size = planner.get_cache_size_mb()
        
        # Cache should respect limits
        assert cache_size <= 110, f"Cache size {cache_size:.2f}MB exceeds limit"
    
    def test_resource_cleanup(self, planner, process):
        """Test that resources are properly cleaned up"""
        gc.collect()
        before = process.memory_info().rss / 1024 / 1024
        
        # Create and destroy multiple planners
        for _ in range(10):
            temp_planner = planner.__class__()
            temp_planner.generate_daily_plan(date="2024-01-15")
            del temp_planner
        
        gc.collect()
        after = process.memory_info().rss / 1024 / 1024
        
        increase = after - before
        
        # Should not accumulate memory
        assert increase < 20, f"Resource cleanup issue: {increase:.2f}MB not freed"
