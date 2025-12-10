#!/bin/bash

# Script to deploy LastMile to Kubernetes

echo "Deploying LastMile to Kubernetes..."
echo "===================================="

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Check if minikube is running (optional)
if command -v minikube &> /dev/null; then
    if minikube status | grep -q "Running"; then
        echo "✓ Minikube is running"
        
        # Use minikube's docker daemon
        eval $(minikube docker-env)
        echo "✓ Using Minikube's Docker daemon"
    fi
fi

# Build images first
echo ""
echo "Step 1: Building Docker images..."
./build-images.sh

# Create namespace
echo ""
echo "Step 2: Creating namespace..."
kubectl apply -f k8s/namespace.yaml

# Deploy databases
echo ""
echo "Step 3: Deploying databases..."
kubectl apply -f k8s/postgres-deployments.yaml

# Deploy RabbitMQ
echo ""
echo "Step 4: Deploying RabbitMQ..."
kubectl apply -f k8s/rabbitmq-deployment.yaml

# Wait for databases and RabbitMQ
echo ""
echo "Waiting for databases and RabbitMQ to be ready..."
sleep 10

# Deploy Location Service (stateless)
echo ""
echo "Step 5: Deploying Location Service..."
kubectl apply -f k8s/location-service.yaml

# Deploy other services
echo ""
echo "Step 6: Deploying microservices..."
kubectl apply -f k8s/user-service.yaml
kubectl apply -f k8s/station-service.yaml
kubectl apply -f k8s/rider-service.yaml
kubectl apply -f k8s/driver-service.yaml
kubectl apply -f k8s/matching-service.yaml
kubectl apply -f k8s/trip-service.yaml
kubectl apply -f k8s/notification-service.yaml

# Deploy HPA for Matching Service
echo ""
echo "Step 7: Deploying HPA for Matching Service..."
kubectl apply -f k8s/matching-service-hpa.yaml

# Deploy Frontend
echo ""
echo "Step 8: Deploying Frontend..."
kubectl apply -f k8s/frontend.yaml

echo ""
echo "✓ Deployment complete!"
echo ""
echo "Checking pod status..."
kubectl get pods -n lastmile

echo ""
echo "Services:"
kubectl get svc -n lastmile

echo ""
echo "HPA Status:"
kubectl get hpa -n lastmile

echo ""
echo "Access the application:"
echo "  Frontend: http://localhost:30000"
echo "  RabbitMQ Management: kubectl port-forward svc/rabbitmq 15672:15672 -n lastmile"
echo ""
echo "To run the demo:"
echo "  1. kubectl port-forward svc/user-service 8001:8001 -n lastmile"
echo "  2. kubectl port-forward svc/station-service 8002:8002 -n lastmile"
echo "  3. kubectl port-forward svc/rider-service 8003:8003 -n lastmile"
echo "  4. kubectl port-forward svc/driver-service 8004:8004 -n lastmile"
echo "  5. kubectl port-forward svc/matching-service 8005:8005 -n lastmile"
echo "  6. python demo/seed_and_simulate.py"

