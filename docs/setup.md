# Setup Guide

This guide walks you through setting up the LLM serving benchmark environment.

## Prerequisites

### Hardware Requirements

- Kubernetes cluster with GPU nodes
  - Recommended: NVIDIA A100 40GB or 80GB GPUs
  - Minimum: NVIDIA V100 16GB or T4 16GB GPUs
- At least 1 GPU node with:
  - 8+ CPU cores
  - 64GB+ RAM
  - 500GB+ disk space for model storage

### Software Requirements

- Kubernetes 1.24+
- kubectl configured to access your cluster
- Helm 3.8+
- Python 3.9+ (for load testing)
- NVIDIA GPU Operator installed on your cluster
- Container runtime with GPU support (containerd or Docker)

## Kubernetes Cluster Setup

### 1. Install NVIDIA GPU Operator

If you haven't already installed the NVIDIA GPU Operator:

```bash
helm repo add nvidia https://nvidia.github.io/gpu-operator
helm repo update

helm install gpu-operator nvidia/gpu-operator \
  --namespace gpu-operator \
  --create-namespace \
  --wait
```

Verify GPU availability:

```bash
kubectl get nodes -o json | jq '.items[].status.capacity."nvidia.com/gpu"'
```

### 2. Create Namespace

```bash
kubectl create namespace llm-serving
```

### 3. Create HuggingFace Token Secret

Most models require authentication to download from HuggingFace Hub:

```bash
kubectl create secret generic huggingface-secret \
  --from-literal=token=YOUR_HF_TOKEN \
  --namespace llm-serving
```

Get your token from: https://huggingface.co/settings/tokens

### 4. (Optional) Setup Persistent Storage

If your cluster doesn't have a default StorageClass:

```bash
# Example for AWS EBS
kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
volumeBindingMode: WaitForFirstConsumer
EOF
```

## Deploy LLM Serving Frameworks

### Deploy vLLM

```bash
cd helm-charts/vllm

# Option 1: Deploy with default values
helm install vllm . --namespace llm-serving

# Option 2: Deploy with custom values
helm install vllm . --namespace llm-serving \
  --set model.name="meta-llama/Llama-2-7b-chat-hf" \
  --set resources.limits."nvidia.com/gpu"=1 \
  --set vllm.tensorParallelSize=1
```

### Deploy SGLang

```bash
cd helm-charts/sglang

helm install sglang . --namespace llm-serving \
  --set model.name="meta-llama/Llama-2-7b-chat-hf"
```

### Deploy Triton + vLLM

```bash
cd helm-charts/triton-vllm

helm install triton . --namespace llm-serving \
  --set model.name="meta-llama/Llama-2-7b-chat-hf"
```

### Deploy TGI

```bash
cd helm-charts/tgi

helm install tgi . --namespace llm-serving \
  --set model.name="meta-llama/Llama-2-7b-chat-hf"
```

## Verify Deployments

Check pod status:

```bash
kubectl get pods -n llm-serving
```

Wait for all pods to be in `Running` state and `READY 1/1`.

Check logs:

```bash
# vLLM
kubectl logs -n llm-serving -l app.kubernetes.io/name=vllm -f

# SGLang
kubectl logs -n llm-serving -l app.kubernetes.io/name=sglang -f

# Triton
kubectl logs -n llm-serving -l app.kubernetes.io/name=triton-vllm -f

# TGI
kubectl logs -n llm-serving -l app.kubernetes.io/name=tgi -f
```

## Setup Port Forwarding for Testing

To access services from your local machine:

```bash
# vLLM
kubectl port-forward -n llm-serving svc/vllm 8000:8000

# SGLang
kubectl port-forward -n llm-serving svc/sglang 8001:8000

# Triton
kubectl port-forward -n llm-serving svc/triton 8002:8000

# TGI
kubectl port-forward -n llm-serving svc/tgi 8003:8080
```

## Test Endpoints

Test vLLM:

```bash
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-2-7b-chat-hf",
    "prompt": "San Francisco is a",
    "max_tokens": 50,
    "temperature": 0.7
  }'
```

## Install Load Testing Tools

```bash
cd load-tests
pip install -r requirements.txt
```

## Troubleshooting

### Pod stuck in Pending state

Check events:
```bash
kubectl describe pod <pod-name> -n llm-serving
```

Common issues:
- No GPU nodes available
- Insufficient GPU memory
- PVC not bound (check StorageClass)

### Pod crashes or restarts

Check logs:
```bash
kubectl logs <pod-name> -n llm-serving --previous
```

Common issues:
- Out of memory (reduce model size or increase resources)
- Model download failed (check HuggingFace token)
- GPU compatibility issues (check CUDA version)

### Model download is slow

Models are downloaded on first startup. For Llama-2-7b:
- Size: ~13GB
- Expected download time: 5-15 minutes depending on network

You can pre-download models to a shared PVC to speed up future deployments.

## Next Steps

- Proceed to [Running Benchmarks](running-benchmarks.md)
- Learn about the [Analysis Methodology](analysis-methodology.md)
- Customize deployment configurations in `values.yaml` files
