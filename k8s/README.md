# Kubernetes Deployment Guide

## Prerequisites

- Kubernetes cluster (minikube, kind, or cloud provider)
- kubectl CLI installed
- Docker installed

## Quick Start

### Option 1: Using Deployment Script

```bash
# Make scripts executable
chmod +x build-images.sh deploy-k8s.sh cleanup-k8s.sh

# Deploy everything
./deploy-k8s.sh
```

### Option 2: Manual Deployment

```bash
# 1. Build Docker images
./build-images.sh

# 2. If using minikube, use its docker daemon
eval $(minikube docker-env)

# 3. Apply Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/postgres-deployments.yaml
kubectl apply -f k8s/rabbitmq-deployment.yaml
kubectl apply -f k8s/location-service.yaml
kubectl apply -f k8s/user-service.yaml
kubectl apply -f k8s/station-service.yaml
kubectl apply -f k8s/rider-service.yaml
kubectl apply -f k8s/driver-service.yaml
kubectl apply -f k8s/matching-service.yaml
kubectl apply -f k8s/matching-service-hpa.yaml
kubectl apply -f k8s/frontend.yaml
```

## Accessing Services

### Frontend
```bash
# Access via NodePort
http://<node-ip>:30000

# Or port-forward
kubectl port-forward svc/frontend 3000:3000 -n lastmile
```

### API Services (for demo script)
```bash
kubectl port-forward svc/user-service 8001:8001 -n lastmile
kubectl port-forward svc/station-service 8002:8002 -n lastmile
kubectl port-forward svc/rider-service 8003:8003 -n lastmile
kubectl port-forward svc/driver-service 8004:8004 -n lastmile
kubectl port-forward svc/matching-service 8005:8005 -n lastmile
```

### RabbitMQ Management
```bash
kubectl port-forward svc/rabbitmq 15672:15672 -n lastmile
# Access at http://localhost:15672 (admin/admin)
```

## Monitoring

### Check Pods
```bash
kubectl get pods -n lastmile
kubectl logs <pod-name> -n lastmile
```

### Check HPA
```bash
kubectl get hpa -n lastmile
kubectl describe hpa matching-service-hpa -n lastmile
```

### Check Services
```bash
kubectl get svc -n lastmile
```

## Auto-Scaling Demo

The Matching Service is configured with Horizontal Pod Autoscaler:
- **Min Replicas**: 1
- **Max Replicas**: 5
- **Target CPU**: 50%

To observe auto-scaling:
1. Run the demo script to generate load
2. Watch HPA: `kubectl get hpa -n lastmile -w`
3. Watch pods scale: `kubectl get pods -n lastmile -w`

## Cleanup

```bash
./cleanup-k8s.sh
# Or manually:
kubectl delete namespace lastmile
```

## Troubleshooting

### Pods not starting
```bash
# Check pod status
kubectl describe pod <pod-name> -n lastmile

# Check logs
kubectl logs <pod-name> -n lastmile
```

### Database connection issues
```bash
# Check if postgres pods are ready
kubectl get pods -n lastmile | grep postgres

# Check service endpoints
kubectl get endpoints -n lastmile
```

### HPA not working
```bash
# Install metrics-server if not present
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# For minikube
minikube addons enable metrics-server
```

