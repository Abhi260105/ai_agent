#!/usr/bin/env python3
"""
Performance benchmarking script
Measures and reports system performance metrics
"""

import sys
import os
import time
import argparse
from pathlib import Path
from typing import Dict, List, Any
import statistics
import json
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


class Benchmark:
    """Benchmark runner"""
    
    def __init__(self, iterations: int = 10):
        self.iterations = iterations
        self.results: Dict[str, List[float]] = {}
    
    def run(self, name: str, func, *args, **kwargs):
        """Run a benchmark"""
        print(f"\nRunning: {name}")
        print(f"Iterations: {self.iterations}")
        
        times = []
        
        for i in range(self.iterations):
            start = time.time()
            func(*args, **kwargs)
            elapsed = time.time() - start
            times.append(elapsed)
            
            print(f"  Iteration {i+1}: {elapsed*1000:.2f}ms")
        
        self.results[name] = times
        
        return times
    
    def get_stats(self, name: str) -> Dict[str, float]:
        """Get statistics for a benchmark"""
        times = self.results.get(name, [])
        
        if not times:
            return {}
        
        return {
            "min": min(times),
            "max": max(times),
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "stdev": statistics.stdev(times) if len(times) > 1 else 0,
            "p95": statistics.quantiles(times, n=20)[18] if len(times) >= 20 else max(times)
        }
    
    def print_summary(self):
        """Print benchmark summary"""
        print("\n" + "=" * 70)
        print("BENCHMARK SUMMARY")
        print("=" * 70)
        
        for name, times in self.results.items():
            stats = self.get_stats(name)
            
            print(f"\n{name}:")
            print(f"  Mean:   {stats['mean']*1000:>8.2f}ms")
            print(f"  Median: {stats['median']*1000:>8.2f}ms")
            print(f"  Min:    {stats['min']*1000:>8.2f}ms")
            print(f"  Max:    {stats['max']*1000:>8.2f}ms")
            print(f"  StdDev: {stats['stdev']*1000:>8.2f}ms")
            print(f"  P95:    {stats['p95']*1000:>8.2f}ms")
        
        print("\n" + "=" * 70)
    
    def export_results(self, filepath: str):
        """Export results to JSON"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "iterations": self.iterations,
            "benchmarks": {}
        }
        
        for name in self.results:
            data["benchmarks"][name] = {
                "times": self.results[name],
                "stats": self.get_stats(name)
            }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n✓ Results exported to: {filepath}")


def benchmark_database_operations(bench: Benchmark, db_path: str):
    """Benchmark database operations"""
    import sqlite3
    
    def insert_records():
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for i in range(100):
            cursor.execute("""
                INSERT INTO memory (user_id, context_type, content)
                VALUES (?, ?, ?)
            """, (1, 'test', f'Test content {i}'))
        
        conn.commit()
        conn.close()
    
    def select_records():
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM memory WHERE user_id = 1 LIMIT 100")
        results = cursor.fetchall()
        
        conn.close()
        return results
    
    def update_records():
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE memory 
            SET content = 'Updated content'
            WHERE user_id = 1
        """)
        
        conn.commit()
        conn.close()
    
    bench.run("DB Insert (100 records)", insert_records)
    bench.run("DB Select (100 records)", select_records)
    bench.run("DB Update (100 records)", update_records)


def benchmark_llm_operations(bench: Benchmark):
    """Benchmark LLM operations"""
    from mocks.mock_llm import MockLLMService
    
    llm = MockLLMService(base_latency_ms=200)
    
    def simple_generation():
        llm.generate("Test prompt", max_tokens=100)
    
    def complex_generation():
        llm.generate(
            "Generate a detailed daily plan with priorities",
            max_tokens=500
        )
    
    bench.run("LLM Simple Generation", simple_generation)
    bench.run("LLM Complex Generation", complex_generation)


def benchmark_memory_operations(bench: Benchmark):
    """Benchmark memory operations"""
    import sys
    from memory_profiler import memory_usage
    
    def create_large_list():
        data = [{"key": i, "value": f"value_{i}"} for i in range(10000)]
        return data
    
    def process_json():
        data = {"items": [{"id": i} for i in range(1000)]}
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        return parsed
    
    bench.run("Memory: Large List Creation", create_large_list)
    bench.run("Memory: JSON Processing", process_json)


def benchmark_plan_generation(bench: Benchmark):
    """Benchmark full plan generation"""
    from mocks.mock_llm import MockLLMService
    from mocks.mock_tools import MockEmailTool, MockCalendarTool
    
    llm = MockLLMService(base_latency_ms=300)
    email_tool = MockEmailTool(latency_ms=100)
    calendar_tool = MockCalendarTool(latency_ms=100)
    
    def generate_plan():
        # Simulate plan generation
        emails = email_tool.fetch_recent(limit=10)
        events = calendar_tool.get_events(days=1)
        plan = llm.generate("Generate daily plan", max_tokens=500)
        return plan
    
    bench.run("Full Plan Generation", generate_plan)


def main():
    parser = argparse.ArgumentParser(
        description="Performance benchmarking tool"
    )
    parser.add_argument(
        '--iterations',
        type=int,
        default=10,
        help='Number of iterations per benchmark'
    )
    parser.add_argument(
        '--db-path',
        default=':memory:',
        help='Database path for benchmarks'
    )
    parser.add_argument(
        '--suite',
        choices=['all', 'db', 'llm', 'memory', 'plan'],
        default='all',
        help='Benchmark suite to run'
    )
    parser.add_argument(
        '--export',
        help='Export results to JSON file'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("PERFORMANCE BENCHMARK")
    print("=" * 70)
    print(f"Suite: {args.suite}")
    print(f"Iterations: {args.iterations}")
    print(f"Database: {args.db_path}")
    
    bench = Benchmark(iterations=args.iterations)
    
    try:
        if args.suite in ['all', 'db']:
            benchmark_database_operations(bench, args.db_path)
        
        if args.suite in ['all', 'llm']:
            benchmark_llm_operations(bench)
        
        if args.suite in ['all', 'memory']:
            benchmark_memory_operations(bench)
        
        if args.suite in ['all', 'plan']:
            benchmark_plan_generation(bench)
        
        bench.print_summary()
        
        if args.export:
            bench.export_results(args.export)
        
    except Exception as e:
        print(f"\n✗ Benchmark failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
