# Load Testing Tools

This directory contains load testing tools for benchmarking LLM serving frameworks.

## Contents

### benchmark-runner.py

Python-based benchmark runner that:
- Generates concurrent requests to LLM endpoints
- Collects latency and throughput metrics
- Supports single framework and comparative benchmarks
- Outputs results in JSON format

**Usage:**

```bash
# Single framework benchmark
python benchmark-runner.py \
  --framework vllm \
  --endpoint http://localhost:8000 \
  --duration 600 \
  --concurrency 100 \
  --output results/vllm_benchmark.json

# Compare all frameworks
python benchmark-runner.py --compare-all --duration 600 --concurrency 100
```

### locust/

Locust-based load testing with web UI:
- Interactive load testing interface
- Real-time metrics visualization
- HTML report generation
- CSV export of results

**Usage:**

```bash
cd locust
locust -f locustfile.py --host=http://localhost:8000 --users=100 --spawn-rate=10
```

### requirements.txt

Python dependencies for load testing:
- `requests` - HTTP client
- `locust` - Load testing framework
- `pandas` - Data analysis
- `matplotlib` - Chart generation
- `numpy` - Numerical operations

**Installation:**

```bash
pip install -r requirements.txt
```

### results/

Directory for storing benchmark results (JSON, CSV, HTML).

Results are gitignored but the directory structure is maintained.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Ensure services are running and accessible

3. Run a simple benchmark:
   ```bash
   python benchmark-runner.py \
     --framework vllm \
     --endpoint http://localhost:8000 \
     --duration 60 \
     --concurrency 10 \
     --output results/test.json
   ```

4. View results:
   ```bash
   cat results/test.json | jq '.'
   ```

## For More Information

See [Running Benchmarks](../docs/running-benchmarks.md) for detailed instructions.
