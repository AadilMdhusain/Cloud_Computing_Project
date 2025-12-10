#!/bin/bash

# Script to set up port forwarding for all services

echo "Setting up port forwarding for LastMile services..."
echo "===================================================="
echo ""
echo "Press Ctrl+C to stop all port forwards"
echo ""

# Kill any existing port forwards
pkill -f "kubectl port-forward" 2>/dev/null

# Start port forwarding in background
kubectl port-forward svc/frontend 3000:3000 -n lastmile &
kubectl port-forward svc/user-service 8001:8001 -n lastmile &
kubectl port-forward svc/station-service 8002:8002 -n lastmile &
kubectl port-forward svc/rider-service 8003:8003 -n lastmile &
kubectl port-forward svc/driver-service 8004:8004 -n lastmile &
kubectl port-forward svc/matching-service 8005:8005 -n lastmile &
kubectl port-forward svc/trip-service 8008:8008 -n lastmile &
kubectl port-forward svc/notification-service 8007:8007 -n lastmile &

sleep 2

echo ""
echo "✅ Port forwarding active!"
echo ""
echo "Access the application at:"
echo "  Frontend: http://localhost:3000"
echo "  User Service: http://localhost:8001"
echo "  Station Service: http://localhost:8002"
echo "  Rider Service: http://localhost:8003"
echo "  Driver Service: http://localhost:8004"
echo "  Matching Service: http://localhost:8005"
echo "  Trip Service: http://localhost:8008"
echo "  Notification Service: http://localhost:8007"
echo ""
echo "Press Ctrl+C to stop all port forwards"

# Wait for user interrupt
wait
