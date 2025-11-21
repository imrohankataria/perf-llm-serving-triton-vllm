"""
LLM Serving Benchmark Runner

This script orchestrates benchmarks across different LLM serving frameworks.
It generates load, collects metrics, and produces comparison reports.
"""

import argparse
import json
import time
import statistics
from datetime import datetime
from typing import Dict, List, Optional
import requests
import concurrent.futures
from dataclasses import dataclass, asdict
import random


@dataclass
class BenchmarkConfig:
    framework: str
    endpoint: str
    duration: int  # seconds
    concurrency: int
    model: str
    input_tokens: int = 512
    output_tokens: int = 128


@dataclass
class RequestMetrics:
    timestamp: float
    latency_ms: float
    success: bool
    error: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0


class BenchmarkRunner:
    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.metrics: List[RequestMetrics] = []
        self.start_time = None
        self.end_time = None

    def generate_prompt(self, length: int = 512) -> str:
        """Generate a prompt of approximately the specified token length."""
        # Rough approximation: 1 token ≈ 4 characters
        words = ["benchmark", "test", "performance", "evaluation", "llm", "inference", "server"]
        prompt = "Summarize the following text:\n\n"
        
        while len(prompt) < length * 4:
            prompt += random.choice(words) + " "
        
        return prompt[:length * 4]

    def make_request(self) -> RequestMetrics:
        """Make a single request to the LLM endpoint."""
        start = time.time()
        prompt = self.generate_prompt(self.config.input_tokens)
        
        try:
            # Support for OpenAI-compatible API format
            payload = {
                "model": self.config.model,
                "prompt": prompt,
                "max_tokens": self.config.output_tokens,
                "temperature": 0.7,
            }
            
            response = requests.post(
                f"{self.config.endpoint}/v1/completions",
                json=payload,
                timeout=60
            )
            
            end = time.time()
            latency_ms = (end - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                # Extract token counts if available
                usage = data.get("usage", {})
                return RequestMetrics(
                    timestamp=start,
                    latency_ms=latency_ms,
                    success=True,
                    input_tokens=usage.get("prompt_tokens", self.config.input_tokens),
                    output_tokens=usage.get("completion_tokens", self.config.output_tokens)
                )
            else:
                return RequestMetrics(
                    timestamp=start,
                    latency_ms=latency_ms,
                    success=False,
                    error=f"HTTP {response.status_code}"
                )
        except Exception as e:
            end = time.time()
            return RequestMetrics(
                timestamp=start,
                latency_ms=(end - start) * 1000,
                success=False,
                error=str(e)
            )

    def worker(self, worker_id: int):
        """Worker thread that continuously makes requests."""
        while time.time() < self.end_time:
            metric = self.make_request()
            self.metrics.append(metric)

    def run(self):
        """Execute the benchmark."""
        print(f"Starting benchmark for {self.config.framework}...")
        print(f"Endpoint: {self.config.endpoint}")
        print(f"Duration: {self.config.duration}s")
        print(f"Concurrency: {self.config.concurrency}")
        
        self.start_time = time.time()
        self.end_time = self.start_time + self.config.duration
        
        # Run concurrent workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.concurrency) as executor:
            futures = [executor.submit(self.worker, i) for i in range(self.config.concurrency)]
            concurrent.futures.wait(futures)
        
        print(f"Benchmark completed. Total requests: {len(self.metrics)}")
        return self.analyze()

    def analyze(self) -> Dict:
        """Analyze collected metrics and generate report."""
        successful = [m for m in self.metrics if m.success]
        failed = [m for m in self.metrics if not m.success]
        
        if not successful:
            return {
                "framework": self.config.framework,
                "error": "No successful requests",
                "total_requests": len(self.metrics),
                "failed_requests": len(failed)
            }
        
        latencies = [m.latency_ms for m in successful]
        latencies.sort()
        
        duration = self.end_time - self.start_time
        
        return {
            "framework": self.config.framework,
            "config": asdict(self.config),
            "summary": {
                "total_requests": len(self.metrics),
                "successful_requests": len(successful),
                "failed_requests": len(failed),
                "duration_seconds": duration,
                "requests_per_second": len(successful) / duration,
            },
            "latency": {
                "mean_ms": statistics.mean(latencies),
                "median_ms": statistics.median(latencies),
                "p50_ms": self._percentile(latencies, 50),
                "p95_ms": self._percentile(latencies, 95),
                "p99_ms": self._percentile(latencies, 99),
                "min_ms": min(latencies),
                "max_ms": max(latencies),
                "stdev_ms": statistics.stdev(latencies) if len(latencies) > 1 else 0,
            },
            "throughput": {
                "tokens_per_second": sum(m.output_tokens for m in successful) / duration,
                "requests_per_second": len(successful) / duration,
            },
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def _percentile(data: List[float], percentile: float) -> float:
        """Calculate percentile from sorted data."""
        if not data:
            return 0
        k = (len(data) - 1) * percentile / 100
        f = int(k)
        c = f + 1
        if c >= len(data):
            return data[-1]
        return data[f] + (k - f) * (data[c] - data[f])


def compare_frameworks(results: List[Dict]) -> Dict:
    """Compare results from multiple frameworks."""
    comparison = {
        "timestamp": datetime.now().isoformat(),
        "frameworks": []
    }
    
    for result in results:
        if "error" not in result:
            comparison["frameworks"].append({
                "name": result["framework"],
                "throughput_rps": result["summary"]["requests_per_second"],
                "p50_latency_ms": result["latency"]["p50_ms"],
                "p95_latency_ms": result["latency"]["p95_ms"],
                "p99_latency_ms": result["latency"]["p99_ms"],
                "success_rate": result["summary"]["successful_requests"] / result["summary"]["total_requests"],
            })
    
    # Sort by throughput
    comparison["frameworks"].sort(key=lambda x: x["throughput_rps"], reverse=True)
    
    return comparison


def main():
    parser = argparse.ArgumentParser(description="LLM Serving Benchmark Runner")
    parser.add_argument("--framework", type=str, help="Framework to benchmark (vllm, sglang, triton, tgi)")
    parser.add_argument("--endpoint", type=str, help="API endpoint URL")
    parser.add_argument("--duration", type=int, default=600, help="Benchmark duration in seconds")
    parser.add_argument("--concurrency", type=int, default=10, help="Number of concurrent requests")
    parser.add_argument("--model", type=str, default="meta-llama/Llama-2-7b-chat-hf", help="Model name")
    parser.add_argument("--input-tokens", type=int, default=512, help="Input token length")
    parser.add_argument("--output-tokens", type=int, default=128, help="Output token length")
    parser.add_argument("--output", type=str, default="results/benchmark.json", help="Output file path")
    parser.add_argument("--compare-all", action="store_true", help="Compare all frameworks")
    
    args = parser.parse_args()
    
    if args.compare_all:
        # Run benchmarks for all frameworks
        frameworks = [
            ("vllm", "http://vllm:8000"),
            ("sglang", "http://sglang:8000"),
            ("triton", "http://triton:8000"),
            ("tgi", "http://tgi:8080"),
        ]
        
        all_results = []
        for name, endpoint in frameworks:
            config = BenchmarkConfig(
                framework=name,
                endpoint=endpoint,
                duration=args.duration,
                concurrency=args.concurrency,
                model=args.model,
                input_tokens=args.input_tokens,
                output_tokens=args.output_tokens,
            )
            runner = BenchmarkRunner(config)
            result = runner.run()
            all_results.append(result)
            
            # Save individual result
            with open(f"results/{name}_benchmark.json", "w") as f:
                json.dump(result, f, indent=2)
        
        # Generate comparison
        comparison = compare_frameworks(all_results)
        with open(args.output, "w") as f:
            json.dump(comparison, f, indent=2)
        
        print("\n=== Comparison ===")
        print(json.dumps(comparison, indent=2))
    else:
        # Run single benchmark
        if not args.framework or not args.endpoint:
            parser.error("--framework and --endpoint are required when not using --compare-all")
        
        config = BenchmarkConfig(
            framework=args.framework,
            endpoint=args.endpoint,
            duration=args.duration,
            concurrency=args.concurrency,
            model=args.model,
            input_tokens=args.input_tokens,
            output_tokens=args.output_tokens,
        )
        
        runner = BenchmarkRunner(config)
        result = runner.run()
        
        # Save result
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        
        print("\n=== Results ===")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
