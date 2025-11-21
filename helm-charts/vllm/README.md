# vLLM Helm Chart

This Helm chart deploys vLLM inference server on Kubernetes with GPU support.

## Prerequisites

- Kubernetes 1.24+
- Helm 3.8+
- NVIDIA GPU Operator installed
- At least 1 GPU node

## Installation

### Quick Start

```bash
helm install vllm . --namespace llm-serving --create-namespace
```

### Custom Installation

```bash
helm install vllm . \
  --namespace llm-serving \
  --create-namespace \
  --set model.name="meta-llama/Llama-2-13b-chat-hf" \
  --set resources.limits."nvidia.com/gpu"=2 \
  --set vllm.tensorParallelSize=2 \
  --set vllm.maxModelLen=8192
```

## Configuration

Key configuration options in `values.yaml`:

### Model Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `model.name` | HuggingFace model ID | `meta-llama/Llama-2-7b-chat-hf` |
| `model.downloadDir` | Directory for model storage | `/models` |

### vLLM Settings

| Parameter | Description | Default |
|-----------|-------------|---------|
| `vllm.tensorParallelSize` | Number of GPUs for tensor parallelism | `1` |
| `vllm.maxModelLen` | Maximum sequence length | `4096` |
| `vllm.gpuMemoryUtilization` | GPU memory utilization ratio | `0.9` |
| `vllm.dtype` | Model data type | `float16` |
| `vllm.enablePrefixCaching` | Enable prefix caching | `true` |
| `vllm.maxNumBatchedTokens` | Max tokens in a batch | `8192` |
| `vllm.maxNumSeqs` | Max sequences in a batch | `256` |

### Resources

| Parameter | Description | Default |
|-----------|-------------|---------|
| `resources.limits."nvidia.com/gpu"` | Number of GPUs | `1` |
| `resources.limits.memory` | Memory limit | `48Gi` |
| `resources.limits.cpu` | CPU limit | `8` |

### Persistence

| Parameter | Description | Default |
|-----------|-------------|---------|
| `persistence.enabled` | Enable persistent volume | `true` |
| `persistence.size` | PVC size | `100Gi` |
| `persistence.storageClass` | Storage class name | `""` (default) |

## Examples

### Multi-GPU Deployment

```bash
helm install vllm . \
  --namespace llm-serving \
  --set resources.limits."nvidia.com/gpu"=4 \
  --set vllm.tensorParallelSize=4 \
  --set model.name="meta-llama/Llama-2-70b-chat-hf"
```

### High Throughput Configuration

```bash
helm install vllm . \
  --namespace llm-serving \
  --set vllm.maxNumBatchedTokens=16384 \
  --set vllm.maxNumSeqs=512 \
  --set vllm.gpuMemoryUtilization=0.95
```

## Accessing the Service

### Port Forward

```bash
kubectl port-forward -n llm-serving svc/vllm 8000:8000
```

### Test Request

```bash
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-2-7b-chat-hf",
    "prompt": "San Francisco is a",
    "max_tokens": 50
  }'
```

## Upgrading

```bash
helm upgrade vllm . --namespace llm-serving
```

## Uninstalling

```bash
helm uninstall vllm --namespace llm-serving
```

## Troubleshooting

### Pod Not Starting

Check events:
```bash
kubectl describe pod -n llm-serving -l app.kubernetes.io/name=vllm
```

### Out of Memory

Reduce GPU memory utilization:
```bash
helm upgrade vllm . \
  --namespace llm-serving \
  --set vllm.gpuMemoryUtilization=0.8
```

### Model Download Failed

Check HuggingFace token:
```bash
kubectl get secret huggingface-secret -n llm-serving
```

## More Information

- [vLLM Documentation](https://docs.vllm.ai/)
- [vLLM GitHub](https://github.com/vllm-project/vllm)
