# Benchmark Visualizations

This directory contains generated charts and visualizations from benchmark data.

## Generated Charts

After running `generate-charts.py`, the following files are created:

1. **latency_comparison.png** - Bar chart comparing P50, P95, and P99 latencies across frameworks
2. **throughput_comparison.png** - Bar chart showing requests per second for each framework
3. **cost_comparison.png** - Bar chart comparing cost per 1M tokens
4. **performance_vs_cost.png** - Scatter plot showing performance vs cost efficiency
5. **concurrency_scaling.png** - Line chart showing how throughput scales with concurrency
6. **summary_report.txt** - Text summary of all benchmark results

## Generating Charts

```bash
cd ../../scripts
python generate-charts.py \
  --input ../benchmarks/data/comparison.json \
  --output ../benchmarks/visualizations/
```

## Requirements

- matplotlib
- numpy
- pandas

Install with: `pip install matplotlib numpy pandas`
