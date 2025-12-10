#!/bin/bash

# Script to cleanup/delete all Kubernetes resources

echo "Cleaning up LastMile Kubernetes deployment..."
echo "=============================================="

kubectl delete namespace lastmile

echo ""
echo "✓ Cleanup complete!"
echo ""
echo "To redeploy, run: ./deploy-k8s.sh"

