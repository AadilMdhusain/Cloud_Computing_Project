#!/bin/bash

# Script to build all Docker images for LastMile application

echo "Building LastMile Docker Images..."
echo "=================================="

cd backend

# Build User Service
echo "Building User Service..."
docker build -t backend-user_service:latest ./user_service

# Build Station Service
echo "Building Station Service..."
docker build -t backend-station_service:latest ./station_service

# Build Rider Service
echo "Building Rider Service..."
docker build -t backend-rider_service:latest ./rider_service

# Build Driver Service
echo "Building Driver Service..."
docker build -t backend-driver_service:latest ./driver_service

# Build Matching Service
echo "Building Matching Service..."
docker build -t backend-matching_service:latest ./matching_service

# Build Location Service
echo "Building Location Service..."
docker build -t backend-location_service:latest ./location_service

# Build Trip Service
echo "Building Trip Service..."
docker build -t backend-trip_service:latest ./trip_service

# Build Notification Service
echo "Building Notification Service..."
docker build -t backend-notification_service:latest ./notification_service

# Build Driver Simulator
echo "Building Driver Simulator..."
docker build -t backend-driver_simulator:latest -f driver_service/Dockerfile.simulator .

# Build Frontend
echo "Building Frontend..."
cd ../frontend
docker build -t frontend:latest .

cd ..

echo ""
echo "✓ All images built successfully!"
echo ""
echo "Built images:"
docker images | grep -E "backend-|frontend"

echo ""
echo "Next steps:"
echo "  1. Deploy to Kubernetes: ./deploy-k8s.sh"
echo "  2. Or start with Docker Compose: cd backend && docker-compose up"

