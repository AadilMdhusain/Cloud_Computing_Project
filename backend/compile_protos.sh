#!/bin/bash

# Script to compile all proto files for each service

PROTO_DIR="./proto"
SERVICES=("user_service" "station_service" "rider_service" "driver_service" "matching_service" "location_service")

# Compile protos for each service
for service in "${SERVICES[@]}"; do
    echo "Compiling protos for $service..."
    mkdir -p "$service/proto_generated"
    
    python -m grpc_tools.protoc \
        -I"$PROTO_DIR" \
        --python_out="$service/proto_generated" \
        --grpc_python_out="$service/proto_generated" \
        "$PROTO_DIR"/*.proto
    
    # Create __init__.py
    touch "$service/proto_generated/__init__.py"
done

echo "Proto compilation complete!"

