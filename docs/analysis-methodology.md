# Benchmark Analysis Methodology

This document explains the methodology used for benchmarking LLM serving frameworks and how to interpret the results.

## Test Environment

### Hardware Configuration

All benchmarks were conducted on identical hardware:

- **Instance Type**: AWS p4d.24xlarge
- **GPUs**: 8x NVIDIA A100 40GB (SXM4)
- **CPU**: 96 vCPUs (Intel Xeon Platinum 8275CL @ 3.0 GHz)
- **RAM**: 1152 GB
- **Network**: 400 Gbps EFA-enabled
- **Storage**: 8TB NVMe SSD

For single-GPU tests, tensor parallelism was set to 1, utilizing only one A100 GPU per framework.

### Software Configuration

- **Kubernetes**: v1.28
- **NVIDIA GPU Operator**: v23.9.0
- **CUDA**: 12.2
- **Container Runtime**: containerd 1.7

### Framework Versions

- **vLLM**: v0.6.0
- **SGLang**: v0.2.0
- **Triton Inference Server**: v24.08 (with vLLM backend)
- **Text Generation Inference (TGI)**: v2.0.0

## Model Configuration

### Model Details

- **Model**: meta-llama/Llama-2-7b-chat-hf
- **Parameters**: 7 billion
- **Precision**: FP16 (float16)
- **Context Length**: 4096 tokens
- **Vocabulary Size**: 32,000 tokens

### Why Llama-2-7B?

1. **Representative Size**: Medium-sized model commonly used in production
2. **Widely Available**: Open-source and accessible
3. **Well-Optimized**: Supported by all frameworks with mature optimizations
4. **Reproducible**: Results can be verified by others

## Benchmark Methodology

### Request Pattern

We use a **Poisson distribution** for request arrival to simulate realistic production traffic:

```python
inter_arrival_time = -log(random()) / request_rate
```

This creates bursts and idle periods similar to real-world usage.

### Input/Output Configuration

- **Input Tokens**: 512 tokens (mean), normal distribution (σ=50)
- **Output Tokens**: 128 tokens (mean), normal distribution (σ=20)
- **Prompt Type**: Mixed (code, text, instructions)

These values represent typical chatbot/assistant workloads.

### Test Parameters

#### Latency Tests
- **Concurrency**: 1-10 concurrent requests
- **Duration**: 10 minutes
- **Warmup**: 2 minutes
- **Goal**: Measure minimum achievable latency

#### Throughput Tests
- **Concurrency**: 100 concurrent requests
- **Duration**: 10 minutes
- **Warmup**: 2 minutes
- **Goal**: Measure maximum sustainable throughput

#### Stress Tests
- **Concurrency**: Gradually increase to saturation point
- **Duration**: 15 minutes
- **Goal**: Identify breaking points and behavior under overload

### Warmup Period

A 2-minute warmup is always performed before measurements to:
- Load model into GPU memory
- Initialize kernels and caches
- Stabilize memory allocation
- Prime any adaptive optimizations

Data from warmup period is **not included** in final metrics.

## Metrics Collected

### Primary Metrics

#### 1. Latency

**Time-to-First-Token (TTFT)**:
- Time from request submission to first token generation
- Critical for user experience in streaming applications
- Measured in milliseconds

**Time-per-Output-Token (TPOT)**:
- Time to generate each subsequent token
- Affects overall generation speed
- Measured in milliseconds per token

**End-to-End Latency**:
- Total time from request to completion
- Includes TTFT + (TPOT × output tokens)
- We report P50, P95, and P99 percentiles

#### 2. Throughput

**Requests per Second (RPS)**:
- Number of completed requests per second
- Primary measure of capacity
- Higher is better

**Tokens per Second (TPS)**:
- Total tokens generated per second
- Better measure for variable-length requests
- Calculated as: output_tokens / total_time

#### 3. Success Rate

**Percentage of successful requests**:
- Status code 200 responses
- No timeouts or errors
- Should be ≥ 99% for production systems

### Secondary Metrics

#### Resource Utilization

- **GPU Utilization**: Percentage (measured via nvidia-smi)
- **GPU Memory**: GB used and percentage
- **CPU Utilization**: Percentage across all cores
- **Memory Usage**: RAM consumption

#### Batch Efficiency

- **Average Batch Size**: Mean number of requests processed together
- **Batch Utilization**: Percentage of max batch size used
- **Queue Depth**: Average number of waiting requests

## Cost Analysis Methodology

### Instance Pricing

Based on AWS on-demand pricing (us-east-1, as of Jan 2024):
- **p4d.24xlarge**: $32.77 per hour

### Cost Calculation

**Cost per 1M tokens** = (Instance cost per hour) / (Tokens per second × 3,600)

Example for vLLM:
- Tokens/second: 1,280
- Cost/hour: $32.77
- Cost per 1M tokens = $32.77 / (1,280 × 3.6) = $2.80

### Assumptions

1. **Full GPU Utilization**: Each framework uses available GPUs efficiently
2. **No Idle Time**: Continuous serving (100% utilization)
3. **Steady State**: Average performance sustained over time
4. **No Spot/Reserved Pricing**: On-demand pricing only

**Real-world costs** will be higher due to:
- Idle time between requests
- Infrastructure overhead (load balancers, monitoring)
- Data transfer costs
- Storage costs

## Statistical Analysis

### Percentile Calculation

We use **Type 7** (default in NumPy/R) for percentile calculation:

```python
def percentile(data, p):
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * p / 100
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return sorted_data[-1]
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])
```

### Outlier Handling

- **No outlier removal**: All data points included
- **Rationale**: Production systems must handle all requests, including slow ones
- **Transparency**: P99 metric captures worst-case behavior

### Confidence Intervals

For claims about performance differences:
- Multiple runs (n=3 minimum)
- Student's t-test for statistical significance (p < 0.05)
- Only report differences > 5% and statistically significant

## Scoring System

The **Overall Score** in the leaderboard combines:

1. **Latency Score (40%)**:
   - Based on P95 latency
   - Normalized: `100 × (best_latency / framework_latency)`

2. **Throughput Score (40%)**:
   - Based on requests per second
   - Normalized: `100 × (framework_throughput / best_throughput)`

3. **Cost Score (20%)**:
   - Based on cost per 1M tokens
   - Normalized: `100 × (lowest_cost / framework_cost)`

**Final Score** = 0.4 × Latency Score + 0.4 × Throughput Score + 0.2 × Cost Score

### Why This Weighting?

- **Latency (40%)**: Critical for user experience
- **Throughput (40%)**: Critical for cost efficiency and scale
- **Cost (20%)**: Important but can be optimized through infrastructure choices

Different workloads may prioritize differently:
- **Real-time chat**: Weight latency higher (60%)
- **Batch processing**: Weight throughput higher (60%)
- **Cost-sensitive**: Weight cost higher (40%)

## Limitations and Caveats

### 1. Single Model Only

Results are specific to Llama-2-7B. Different models may show different patterns:
- Larger models may favor different frameworks
- Different architectures (e.g., Mistral, GPT) may perform differently
- Quantized models have different characteristics

### 2. Specific Hardware

Results on NVIDIA A100. Performance may differ on:
- Other GPU models (H100, V100, T4, L4)
- Different GPU memory sizes
- CPU-only serving
- Different cloud providers or regions

### 3. Default Configurations

We use recommended default settings. Performance can be improved with:
- Framework-specific tuning
- Model optimization (quantization, pruning)
- Custom kernels
- Workload-specific batching strategies

### 4. Synthetic Workload

Our synthetic workload may not match your use case:
- Fixed input/output lengths
- No conversation history
- No function calling
- Simplified prompt patterns

### 5. Point-in-Time

Framework performance changes over time:
- New releases add optimizations
- Bug fixes improve stability
- New features may affect performance

These benchmarks represent **a snapshot** at a specific point in time.

## Reproducibility

### Running Your Own Benchmarks

To reproduce these results:

1. Follow the [Setup Guide](setup.md)
2. Use identical hardware (or note differences)
3. Deploy frameworks with default configurations
4. Run benchmarks as described in [Running Benchmarks](running-benchmarks.md)
5. Report all parameters and environment details

### Sharing Results

If you run benchmarks and want to share:

1. Document hardware and software versions
2. Include raw data (JSON files)
3. Note any configuration changes from defaults
4. Run multiple times and report variance
5. Open an issue or PR with results

## Framework-Specific Notes

### vLLM
- Uses PagedAttention for memory efficiency
- Continuous batching enabled by default
- Prefix caching improves repeated prompts

### SGLang
- Uses RadixAttention for prefix caching
- Excellent for workloads with shared prefixes
- Optimized for structured generation

### Triton + vLLM
- Enterprise features (model ensemble, versioning)
- Multiple backend support
- Advanced batching policies
- Some overhead from abstraction layer

### TGI
- Simpler deployment and configuration
- Great for getting started quickly
- Active HuggingFace integration
- Flash Attention 2 support

## Future Work

Areas for expanded benchmarking:

1. **More Models**: Llama-13B, 70B, Mistral, Mixtral, etc.
2. **Different Hardware**: H100, V100, T4, L4 GPUs
3. **Quantization**: Compare INT8, INT4, GPTQ, AWQ
4. **Multi-GPU**: Tensor and pipeline parallelism
5. **Production Patterns**: Rate limiting, queueing, autoscaling
6. **Streaming**: Measure token-by-token latency
7. **Structured Output**: JSON mode, function calling performance
8. **Long Context**: 8K, 16K, 32K context windows

## Questions or Feedback?

If you have questions about the methodology or suggestions for improvement:

- Open an issue in the repository
- Provide detailed feedback on specific aspects
- Share your own benchmark results

We're committed to transparent, reproducible benchmarking that helps the community make informed decisions.
