# Running Benchmarks

This guide explains how to run performance benchmarks for LLM serving frameworks.

## Prerequisites

- All frameworks deployed and running (see [Setup Guide](setup.md))
- Python 3.9+ installed
- Load testing tools installed (`pip install -r load-tests/requirements.txt`)
- Port forwarding configured or direct cluster access

## Benchmark Methods

We provide two methods for running benchmarks:

1. **Python Benchmark Runner** - Simple, programmatic benchmarking
2. **Locust** - Web-based load testing with real-time metrics

## Method 1: Python Benchmark Runner

### Single Framework Benchmark

Run a benchmark against a single framework:

```bash
cd load-tests

python benchmark-runner.py \
  --framework vllm \
  --endpoint http://localhost:8000 \
  --duration 600 \
  --concurrency 100 \
  --model meta-llama/Llama-2-7b-chat-hf \
  --input-tokens 512 \
  --output-tokens 128 \
  --output results/vllm_benchmark.json
```

Parameters:
- `--framework`: Framework name (vllm, sglang, triton, tgi)
- `--endpoint`: API endpoint URL
- `--duration`: Test duration in seconds (default: 600)
- `--concurrency`: Number of concurrent requests (default: 10)
- `--model`: Model identifier
- `--input-tokens`: Average input token length (default: 512)
- `--output-tokens`: Average output token length (default: 128)
- `--output`: Output JSON file path

### Compare All Frameworks

Run benchmarks for all frameworks and generate a comparison:

```bash
python benchmark-runner.py \
  --compare-all \
  --duration 600 \
  --concurrency 100 \
  --output results/comparison.json
```

This will:
1. Run benchmarks sequentially for each framework
2. Save individual results to `results/{framework}_benchmark.json`
3. Generate a comparison report in `results/comparison.json`

### Analyze Results

View the JSON output:

```bash
cat results/comparison.json | jq '.'
```

Results include:
- **Throughput**: Requests per second
- **Latency**: P50, P95, P99 percentiles
- **Success rate**: Percentage of successful requests
- **Token throughput**: Tokens generated per second

## Method 2: Locust Load Testing

Locust provides a web interface for interactive load testing.

### Start Locust

```bash
cd load-tests/locust

# Basic usage
locust -f locustfile.py --host=http://localhost:8000

# With specific parameters
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --users=100 \
  --spawn-rate=10 \
  --run-time=10m \
  --html=results/locust_report.html
```

### Use Web Interface

1. Open browser to http://localhost:8089
2. Set number of users and spawn rate
3. Click "Start swarming"
4. Monitor real-time metrics:
   - Requests per second
   - Response times (median, 95th percentile)
   - Number of failures
   - Charts and graphs

### Headless Mode

Run without the web interface:

```bash
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --users=100 \
  --spawn-rate=10 \
  --run-time=10m \
  --headless \
  --html=results/locust_report.html \
  --csv=results/locust_stats
```

This generates:
- HTML report: `locust_report.html`
- CSV files: `locust_stats_stats.csv`, `locust_stats_failures.csv`

## Benchmark Scenarios

### 1. Latency Test (Low Concurrency)

Focus on measuring minimum latency:

```bash
python benchmark-runner.py \
  --framework vllm \
  --endpoint http://localhost:8000 \
  --duration 300 \
  --concurrency 1 \
  --output results/vllm_latency.json
```

### 2. Throughput Test (High Concurrency)

Measure maximum throughput:

```bash
python benchmark-runner.py \
  --framework vllm \
  --endpoint http://localhost:8000 \
  --duration 600 \
  --concurrency 100 \
  --output results/vllm_throughput.json
```

### 3. Stress Test (Overload)

Test behavior under extreme load:

```bash
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --users=500 \
  --spawn-rate=50 \
  --run-time=15m
```

### 4. Scaling Test (Varying Concurrency)

Test how performance scales:

```bash
for concurrency in 1 10 50 100 200; do
  python benchmark-runner.py \
    --framework vllm \
    --endpoint http://localhost:8000 \
    --duration 300 \
    --concurrency $concurrency \
    --output results/vllm_concurrency_${concurrency}.json
done
```

### 5. Long-Running Stability Test

Test stability over extended period:

```bash
python benchmark-runner.py \
  --framework vllm \
  --endpoint http://localhost:8000 \
  --duration 3600 \
  --concurrency 50 \
  --output results/vllm_stability.json
```

## Generate Visualization Charts

After collecting benchmark data, generate charts:

```bash
cd scripts

python generate-charts.py \
  --input ../benchmarks/data/comparison.json \
  --output ../benchmarks/visualizations/
```

This creates:
- `latency_comparison.png` - Latency percentiles comparison
- `throughput_comparison.png` - Throughput bar chart
- `cost_comparison.png` - Cost efficiency comparison
- `performance_vs_cost.png` - Scatter plot of performance vs cost
- `concurrency_scaling.png` - Throughput scaling with concurrency
- `summary_report.txt` - Text summary of results

## Best Practices

### 1. Warmup Period

Always include a warmup period before measuring:

```bash
# Run warmup
python benchmark-runner.py \
  --framework vllm \
  --endpoint http://localhost:8000 \
  --duration 120 \
  --concurrency 10 \
  --output /dev/null

# Then run actual benchmark
python benchmark-runner.py \
  --framework vllm \
  --endpoint http://localhost:8000 \
  --duration 600 \
  --concurrency 100 \
  --output results/vllm_benchmark.json
```

### 2. Multiple Runs

Run each test multiple times and average results:

```bash
for i in {1..3}; do
  python benchmark-runner.py \
    --framework vllm \
    --endpoint http://localhost:8000 \
    --duration 600 \
    --concurrency 100 \
    --output results/vllm_run_${i}.json
done
```

### 3. Monitor Resources

Monitor cluster resources during benchmarks:

```bash
# In a separate terminal
watch kubectl top pods -n llm-serving
watch kubectl top nodes
```

### 4. Consistent Test Environment

- Use the same hardware for all tests
- Same model and configuration
- Same input/output token lengths
- Same concurrency patterns
- Test during low cluster activity

### 5. Document Configuration

Record all test parameters:
- Hardware specs (GPU model, count, memory)
- Framework versions
- Model name and size
- Input/output token lengths
- Concurrency levels
- Test duration
- Date and time of test

## Interpreting Results

### Latency Metrics

- **P50 (Median)**: Typical request latency
- **P95**: 95% of requests complete within this time
- **P99**: 99% of requests complete within this time
- Lower is better

### Throughput Metrics

- **Requests/second**: Total request handling capacity
- **Tokens/second**: Total token generation capacity
- Higher is better

### Success Rate

- Should be > 99% for production systems
- Lower rates indicate instability or overload

### Cost Efficiency

- Calculate: `(Instance cost per hour) / (Tokens per second * 3600)`
- Lower cost per token is better

## Troubleshooting

### High Failure Rate

- Reduce concurrency
- Increase timeout values
- Check server logs for errors
- Verify sufficient resources

### Inconsistent Results

- Run warmup period
- Increase test duration
- Check for background activity
- Ensure network stability

### Low Throughput

- Check GPU utilization (`nvidia-smi`)
- Verify batch size configuration
- Check for CPU bottlenecks
- Review memory usage

## Next Steps

- Review [Analysis Methodology](analysis-methodology.md)
- Optimize framework configurations based on results
- Share results with the community
- Contribute improvements
