"""
Generate visualization charts from benchmark data

This script creates various charts comparing LLM serving frameworks:
- Latency distribution charts
- Throughput comparison
- Cost efficiency analysis
- Performance vs cost scatter plots
"""

import json
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

# Use non-interactive backend for server environments
matplotlib.use('Agg')

# Color palette for consistent chart styling
COLORS = {
    'vllm': '#2ecc71',
    'sglang': '#3498db',
    'triton-vllm': '#9b59b6',
    'tgi': '#e74c3c',
    'primary': '#3498db',
    'secondary': '#e74c3c',
    'tertiary': '#f39c12',
    'quaternary': '#2ecc71'
}


def load_benchmark_data(data_file: str) -> dict:
    """Load benchmark data from JSON file."""
    with open(data_file, 'r') as f:
        return json.load(f)


def plot_latency_comparison(data: dict, output_dir: Path):
    """Create a bar chart comparing latency percentiles."""
    frameworks = [f['name'] for f in data['frameworks']]
    p50 = [f['p50_latency_ms'] for f in data['frameworks']]
    p95 = [f['p95_latency_ms'] for f in data['frameworks']]
    p99 = [f['p99_latency_ms'] for f in data['frameworks']]
    
    x = np.arange(len(frameworks))
    width = 0.25
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(x - width, p50, width, label='P50', color=COLORS['primary'])
    ax.bar(x, p95, width, label='P95', color=COLORS['secondary'])
    ax.bar(x + width, p99, width, label='P99', color=COLORS['tertiary'])
    
    ax.set_xlabel('Framework', fontsize=12, fontweight='bold')
    ax.set_ylabel('Latency (ms)', fontsize=12, fontweight='bold')
    ax.set_title('LLM Serving Latency Comparison (P50, P95, P99)', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(frameworks)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'latency_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_dir / 'latency_comparison.png'}")


def plot_throughput_comparison(data: dict, output_dir: Path):
    """Create a bar chart comparing throughput."""
    frameworks = [f['name'] for f in data['frameworks']]
    throughput = [f['throughput_rps'] for f in data['frameworks']]
    
    # Sort by throughput
    sorted_data = sorted(zip(frameworks, throughput), key=lambda x: x[1], reverse=True)
    frameworks, throughput = zip(*sorted_data)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    colors_list = [COLORS.get(fw, COLORS['primary']) for fw in frameworks]
    bars = ax.barh(frameworks, throughput, color=colors_list)
    
    ax.set_xlabel('Requests per Second', fontsize=12, fontweight='bold')
    ax.set_ylabel('Framework', fontsize=12, fontweight='bold')
    ax.set_title('LLM Serving Throughput Comparison', fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    
    # Add value labels on bars
    for bar in bars:
        width = bar.get_width()
        ax.text(width, bar.get_y() + bar.get_height()/2, f'{width:.0f}',
                ha='left', va='center', fontweight='bold', fontsize=10, color='black')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'throughput_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_dir / 'throughput_comparison.png'}")


def plot_cost_analysis(data: dict, output_dir: Path):
    """Create a chart comparing cost efficiency."""
    frameworks = [f['name'] for f in data['frameworks']]
    costs = [f['cost_per_1m_tokens'] for f in data['frameworks']]
    
    # Sort by cost
    sorted_data = sorted(zip(frameworks, costs), key=lambda x: x[1])
    frameworks, costs = zip(*sorted_data)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    colors_list = [COLORS['quaternary'], COLORS['primary'], COLORS['tertiary'], COLORS['secondary']]
    bars = ax.bar(frameworks, costs, color=colors_list)
    
    ax.set_xlabel('Framework', fontsize=12, fontweight='bold')
    ax.set_ylabel('Cost per 1M Tokens ($)', fontsize=12, fontweight='bold')
    ax.set_title('LLM Serving Cost Comparison', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'${height:.2f}',
                ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'cost_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_dir / 'cost_comparison.png'}")


def plot_performance_vs_cost(data: dict, output_dir: Path):
    """Create a scatter plot of performance vs cost."""
    frameworks = [f['name'] for f in data['frameworks']]
    throughput = [f['throughput_rps'] for f in data['frameworks']]
    costs = [f['cost_per_1m_tokens'] for f in data['frameworks']]
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    colors_list = [COLORS.get(fw, COLORS['primary']) for fw in frameworks]
    for i, (name, tp, cost) in enumerate(zip(frameworks, throughput, costs)):
        ax.scatter(cost, tp, s=500, alpha=0.6, c=colors_list[i], edgecolors='black', linewidth=2)
        ax.annotate(name, (cost, tp), fontsize=12, fontweight='bold',
                   ha='center', va='center')
    
    ax.set_xlabel('Cost per 1M Tokens ($)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Throughput (requests/sec)', fontsize=12, fontweight='bold')
    ax.set_title('Performance vs Cost Efficiency', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # Add quadrant labels
    ax.axhline(y=np.mean(throughput), color='gray', linestyle='--', alpha=0.5)
    ax.axvline(x=np.mean(costs), color='gray', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'performance_vs_cost.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_dir / 'performance_vs_cost.png'}")


def plot_concurrency_scaling(output_dir: Path):
    """Create a chart showing how throughput scales with concurrency.
    
    Note: This uses sample data for demonstration. Replace with actual
    benchmark data for production use.
    """
    concurrency_levels = [1, 10, 50, 100]
    
    # Sample data for demonstration - replace with actual benchmark results
    data = {
        'vllm': [45, 420, 750, 850],
        'sglang': [42, 410, 730, 820],
        'triton-vllm': [38, 380, 680, 780],
        'tgi': [32, 320, 580, 680]
    }
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    markers = {'vllm': 'o', 'sglang': 's', 'triton-vllm': '^', 'tgi': 'D'}
    
    for framework, throughputs in data.items():
        ax.plot(concurrency_levels, throughputs, marker=markers[framework],
                linewidth=2, markersize=10, label=framework, color=COLORS.get(framework, COLORS['primary']))
    
    ax.set_xlabel('Concurrency Level', fontsize=12, fontweight='bold')
    ax.set_ylabel('Throughput (requests/sec)', fontsize=12, fontweight='bold')
    ax.set_title('Throughput Scaling with Concurrency', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11, loc='upper left')
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log')
    ax.set_xticks(concurrency_levels)
    ax.set_xticklabels(concurrency_levels)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'concurrency_scaling.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_dir / 'concurrency_scaling.png'}")


def generate_summary_report(data: dict, output_dir: Path):
    """Generate a text summary report."""
    report = []
    report.append("=" * 80)
    report.append("LLM SERVING BENCHMARK SUMMARY REPORT")
    report.append("=" * 80)
    report.append("")
    
    # Test configuration
    config = data.get('test_configuration', {})
    report.append("Test Configuration:")
    report.append(f"  Model: {config.get('model', 'N/A')}")
    report.append(f"  Hardware: {config.get('hardware', 'N/A')}")
    report.append(f"  Instance: {config.get('instance', 'N/A')}")
    report.append(f"  Input Tokens: {config.get('input_tokens', 'N/A')}")
    report.append(f"  Output Tokens: {config.get('output_tokens', 'N/A')}")
    report.append("")
    
    # Framework rankings
    report.append("Framework Rankings:")
    report.append("")
    
    # By throughput
    by_throughput = sorted(data['frameworks'], key=lambda x: x['throughput_rps'], reverse=True)
    report.append("  By Throughput (req/s):")
    for i, f in enumerate(by_throughput, 1):
        report.append(f"    {i}. {f['name']:15} - {f['throughput_rps']:.0f} req/s")
    report.append("")
    
    # By latency (P95)
    by_latency = sorted(data['frameworks'], key=lambda x: x['p95_latency_ms'])
    report.append("  By P95 Latency (ms):")
    for i, f in enumerate(by_latency, 1):
        report.append(f"    {i}. {f['name']:15} - {f['p95_latency_ms']:.0f} ms")
    report.append("")
    
    # By cost
    by_cost = sorted(data['frameworks'], key=lambda x: x['cost_per_1m_tokens'])
    report.append("  By Cost Efficiency ($/1M tokens):")
    for i, f in enumerate(by_cost, 1):
        report.append(f"    {i}. {f['name']:15} - ${f['cost_per_1m_tokens']:.2f}")
    report.append("")
    
    report.append("=" * 80)
    
    report_text = "\n".join(report)
    report_file = output_dir / 'summary_report.txt'
    with open(report_file, 'w') as f:
        f.write(report_text)
    
    print(report_text)
    print(f"\nSaved: {report_file}")


def main():
    parser = argparse.ArgumentParser(description="Generate benchmark visualization charts")
    parser.add_argument("--input", type=str, required=True, help="Input benchmark data JSON file")
    parser.add_argument("--output", type=str, required=True, help="Output directory for charts")
    
    args = parser.parse_args()
    
    # Load data
    data = load_benchmark_data(args.input)
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate all charts
    print("Generating visualization charts...")
    plot_latency_comparison(data, output_dir)
    plot_throughput_comparison(data, output_dir)
    plot_cost_analysis(data, output_dir)
    plot_performance_vs_cost(data, output_dir)
    plot_concurrency_scaling(output_dir)
    generate_summary_report(data, output_dir)
    
    print(f"\nAll charts generated successfully in: {output_dir}")


if __name__ == "__main__":
    main()
