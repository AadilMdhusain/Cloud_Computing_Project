#!/bin/sh
set -e

python manage.py migrate

# Start Django HTTP server in background
nohup python manage.py runserver 0.0.0.0:8002 > /tmp/django.log 2>&1 &
HTTP_PID=$!
echo "Django HTTP server started with PID $HTTP_PID"

# Give Django a moment to start
sleep 3

# Start gRPC server in foreground (this keeps the container running)
echo "Starting Station gRPC server on port 50052..."
python stations/grpc_service.py 2>&1 | tee /tmp/grpc.log
echo "gRPC server exited with code: $?"

