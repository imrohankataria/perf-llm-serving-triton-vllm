#!/bin/bash
set -e

# Deploy all LLM serving frameworks
# Usage: ./deploy-all.sh [namespace]

NAMESPACE=${1:-llm-serving}
MODEL=${2:-meta-llama/Llama-2-7b-chat-hf}

echo "=================================="
echo "Deploying All LLM Serving Frameworks"
echo "=================================="
echo "Namespace: $NAMESPACE"
echo "Model: $MODEL"
echo ""

# Create namespace if it doesn't exist
echo "Creating namespace $NAMESPACE..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Check if HuggingFace secret exists
if ! kubectl get secret huggingface-secret -n $NAMESPACE &> /dev/null; then
    echo ""
    echo "WARNING: HuggingFace secret not found!"
    echo "Please create it with:"
    echo "  kubectl create secret generic huggingface-secret \\"
    echo "    --from-literal=token=YOUR_HF_TOKEN \\"
    echo "    --namespace $NAMESPACE"
    echo ""
    read -p "Do you want to continue without the secret? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Deploy vLLM
echo ""
echo "Deploying vLLM..."
cd helm-charts/vllm
helm upgrade --install vllm . \
  --namespace $NAMESPACE \
  --set model.name="$MODEL" \
  --wait \
  --timeout 10m

# Deploy SGLang
echo ""
echo "Deploying SGLang..."
cd ../sglang
helm upgrade --install sglang . \
  --namespace $NAMESPACE \
  --set model.name="$MODEL" \
  --wait \
  --timeout 10m

# Deploy Triton + vLLM
echo ""
echo "Deploying Triton + vLLM..."
cd ../triton-vllm
helm upgrade --install triton . \
  --namespace $NAMESPACE \
  --set model.name="$MODEL" \
  --wait \
  --timeout 10m

# Deploy TGI
echo ""
echo "Deploying TGI..."
cd ../tgi
helm upgrade --install tgi . \
  --namespace $NAMESPACE \
  --set model.name="$MODEL" \
  --wait \
  --timeout 10m

cd ../..

echo ""
echo "=================================="
echo "Deployment Complete!"
echo "=================================="
echo ""
echo "Check status with:"
echo "  kubectl get pods -n $NAMESPACE"
echo ""
echo "View logs with:"
echo "  kubectl logs -n $NAMESPACE -l app.kubernetes.io/name=vllm -f"
echo "  kubectl logs -n $NAMESPACE -l app.kubernetes.io/name=sglang -f"
echo "  kubectl logs -n $NAMESPACE -l app.kubernetes.io/name=triton-vllm -f"
echo "  kubectl logs -n $NAMESPACE -l app.kubernetes.io/name=tgi -f"
echo ""
echo "Setup port forwarding with:"
echo "  kubectl port-forward -n $NAMESPACE svc/vllm 8000:8000"
echo "  kubectl port-forward -n $NAMESPACE svc/sglang 8001:8000"
echo "  kubectl port-forward -n $NAMESPACE svc/triton 8002:8000"
echo "  kubectl port-forward -n $NAMESPACE svc/tgi 8003:8080"
echo ""
