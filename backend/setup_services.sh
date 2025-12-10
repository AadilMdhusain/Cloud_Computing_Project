#!/bin/bash

# Script to copy proto files to each service directory

echo "Setting up services with proto files..."

SERVICES=("user_service" "station_service" "rider_service" "driver_service" "matching_service" "location_service")

for service in "${SERVICES[@]}"; do
    echo "Copying proto files to $service..."
    mkdir -p "$service/proto"
    cp proto/*.proto "$service/proto/"
done

echo "✓ Proto files copied to all services!"

