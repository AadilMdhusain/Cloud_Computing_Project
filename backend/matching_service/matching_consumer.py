"""
Matching Service RabbitMQ Consumer

This consumer listens to the matching_queue and performs the matching logic:
1. Receives driver location near a station
2. Queries Rider Service for riders at that station
3. Performs matching based on ETA and destination proximity
4. Updates Driver route via gRPC (pushes station to front of queue)
5. Updates Rider status to MATCHED
6. Creates Match record

This service is designed to be auto-scaled by Kubernetes HPA.
"""

import os
import sys
import json
import django
import grpc
import pika
import requests
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'matching_service.settings')
django.setup()

from matching.models import Match
from django.conf import settings

# Import proto files
from proto_generated import rider_pb2, rider_pb2_grpc
from proto_generated import driver_pb2, driver_pb2_grpc


class MatchingConsumer:
    
    def __init__(self):
        self.rabbitmq_url = settings.RABBITMQ_URL
        self.rider_service_host = settings.RIDER_SERVICE_HOST
        self.rider_service_port = settings.RIDER_SERVICE_PORT
        self.driver_service_host = settings.DRIVER_SERVICE_HOST
        self.driver_service_port = settings.DRIVER_SERVICE_PORT
        
        # Setup gRPC clients
        self.setup_grpc_clients()
        
        print("[MATCHING] Consumer initialized")
    
    def setup_grpc_clients(self):
        """Setup gRPC clients for Rider and Driver services"""
        try:
            # Rider Service
            rider_address = f"{self.rider_service_host}:{self.rider_service_port}"
            rider_channel = grpc.insecure_channel(rider_address)
            self.rider_stub = rider_pb2_grpc.RiderServiceStub(rider_channel)
            
            # Driver Service
            driver_address = f"{self.driver_service_host}:{self.driver_service_port}"
            driver_channel = grpc.insecure_channel(driver_address)
            self.driver_stub = driver_pb2_grpc.DriverServiceStub(driver_channel)
            
            print("[MATCHING] gRPC clients initialized")
        except Exception as e:
            print(f"[MATCHING] gRPC client setup failed: {e}")
            self.rider_stub = None
            self.driver_stub = None
    
    def calculate_max_eta(self, driver_timestamp):
        """
        Calculate maximum ETA for matching.
        Driver timestamp + 5 minutes window
        """
        try:
            # Parse HH:MM format
            hour, minute = map(int, driver_timestamp.split(':'))
            
            # Create datetime and add 5 minutes
            dt = datetime(2024, 1, 1, hour, minute)
            dt += timedelta(minutes=5)
            
            # Return as HH:MM string
            return dt.strftime('%H:%M')
        except:
            return "23:59"
    
    def get_riders_at_station(self, station_id, max_eta):
        """Query Rider Service for riders at the station"""
        try:
            request = rider_pb2.GetRidersByStationMessage(
                station_id=station_id,
                max_eta=max_eta
            )
            response = self.rider_stub.GetRidersByStation(request)
            
            if response.success:
                riders = []
                for ride in response.rides:
                    riders.append({
                        'ride_request_id': ride.ride_request_id,
                        'rider_id': ride.rider_id,
                        'station_id': ride.station_id,
                        'eta': ride.eta,
                        'destination_lat': ride.destination_lat,
                        'destination_lng': ride.destination_lng,
                        'status': ride.status
                    })
                return riders
            return []
        except Exception as e:
            print(f"[MATCHING] Failed to get riders: {e}")
            return []
    
    def update_driver_route(self, driver_id, station_id, station_lat, station_lng):
        """
        CRITICAL: Update driver route by pushing station to front of queue
        This is the key interaction that makes the driver physically visit the station
        """
        try:
            request = driver_pb2.UpdateRouteRequest(
                driver_id=driver_id,
                station_id=station_id,
                station_lat=station_lat,
                station_lng=station_lng,
                action="PUSH_FRONT"
            )
            response = self.driver_stub.UpdateDriverRoute(request)
            
            if response.success:
                print(f"[MATCHING] Updated Driver {driver_id} route - Station {station_id} pushed to front")
                return True
            else:
                print(f"[MATCHING] Failed to update driver route: {response.message}")
                return False
        except Exception as e:
            print(f"[MATCHING] Error updating driver route: {e}")
            return False
    
    def update_rider_status(self, ride_request_id, status):
        """Update rider status to MATCHED"""
        try:
            request = rider_pb2.UpdateRideStatusMessage(
                ride_request_id=ride_request_id,
                status=status
            )
            response = self.rider_stub.UpdateRideStatus(request)
            
            if response.success:
                print(f"[MATCHING] Updated Ride {ride_request_id} status to {status}")
                return True
            else:
                print(f"[MATCHING] Failed to update rider status: {response.message}")
                return False
        except Exception as e:
            print(f"[MATCHING] Error updating rider status: {e}")
            return False
    
    def create_match_record(self, rider_id, driver_id, station_id, timestamp, dest_lat=0.0, dest_lng=0.0):
        """Create a match record in the database and create a trip"""
        try:
            match = Match.objects.create(
                rider_id=rider_id,
                driver_id=driver_id,
                station_id=station_id,
                match_timestamp=timestamp,
                status='ACTIVE'
            )
            print(f"[MATCHING] Created Match #{match.id}: Rider {rider_id} <-> Driver {driver_id}")
            
            # Create trip in Trip Service
            self.create_trip_for_match(match.id, rider_id, driver_id, station_id, dest_lat, dest_lng)
            
            return match
        except Exception as e:
            print(f"[MATCHING] Error creating match: {e}")
            return None
    
    def create_trip_for_match(self, match_id, rider_id, driver_id, station_id, dest_lat, dest_lng):
        """Create a trip in Trip Service when match is created"""
        try:
            trip_host = os.environ.get('TRIP_SERVICE_HOST', 'localhost')
            trip_port = os.environ.get('TRIP_SERVICE_PORT', '8008')
            url = f"http://{trip_host}:{trip_port}/api/trips/"
            
            trip_payload = {
                'match_id': match_id,
                'rider_id': rider_id,
                'driver_id': driver_id,
                'pickup_station_id': station_id,
                'pickup_station_id': station_id,
                'destination_lat': dest_lat,
                'destination_lng': dest_lng
            }
            
            # Django in trip_service rejects underscores in host header.
            # Force a safe Host header while still calling the service name.
            headers = {'Host': 'localhost'}
            response = requests.post(url, json=trip_payload, headers=headers, timeout=5)
            if response.status_code == 201:
                print(f"[MATCHING] ✅ Trip created for match {match_id}")
            else:
                print(f"[MATCHING] ⚠️ Failed to create trip: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"[MATCHING] ❌ Error creating trip: {e}")
    
    def process_matching_request(self, message_data):
        """
        Main matching logic:
        1. Get riders at the station
        2. Filter by ETA (within 5 minutes)
        3. Match first available rider
        4. Update driver route (push station to front)
        5. Update rider status to MATCHED
        6. Create match record
        """
        
        driver_id = message_data['driver_id']
        station_id = message_data['nearby_station_id']
        station_name = message_data['nearby_station_name']
        driver_timestamp = message_data['timestamp']
        driver_lat = message_data['current_lat']
        driver_lng = message_data['current_lng']
        
        print(f"\n[MATCHING] Processing: Driver {driver_id} near Station {station_id} ({station_name}) at {driver_timestamp}")
        
        # Calculate max ETA window
        max_eta = self.calculate_max_eta(driver_timestamp)
        print(f"[MATCHING] Looking for riders with ETA <= {max_eta}")
        
        # Get riders at this station
        riders = self.get_riders_at_station(station_id, max_eta)
        
        if not riders:
            print(f"[MATCHING] No riders found at Station {station_id}")
            return
        
        print(f"[MATCHING] Found {len(riders)} rider(s) at Station {station_id}")
        
        # Match with first available rider
        # In production, you'd implement more sophisticated matching logic
        # (destination proximity, capacity, etc.)
        rider = riders[0]
        
        print(f"[MATCHING] ✓ MATCH FOUND!", flush=True)
        print(f"[MATCHING]   Rider {rider['rider_id']} (ETA: {rider['eta']})", flush=True)
        print(f"[MATCHING]   Driver {driver_id} (Time: {driver_timestamp})", flush=True)
        print(f"[MATCHING]   Meeting Point: Station {station_id} ({station_name})", flush=True)
        
        # CRITICAL STEP: Update driver route to visit the station
        # We need to get the station coordinates - for now use driver's current location
        # In production, fetch from Station Service
        success = self.update_driver_route(driver_id, station_id, driver_lat, driver_lng)
        
        if not success:
            print(f"[MATCHING] Failed to update driver route, aborting match")
            return
        
        # Update rider status
        self.update_rider_status(rider['ride_request_id'], 'MATCHED')
        
        # Create match record
        self.create_match_record(
            rider_id=rider['rider_id'],
            driver_id=driver_id,
            station_id=station_id,
            timestamp=driver_timestamp,
            dest_lat=rider['destination_lat'],
            dest_lng=rider['destination_lng']
        )
        
        print(f"[MATCHING] Match complete!\n")
    
    def callback(self, ch, method, properties, body):
        """RabbitMQ message callback (auto_ack enabled, no manual ack needed)"""
        try:
            print(f"[MATCHING] 📨 Message received!", flush=True)
            message_data = json.loads(body)
            print(f"[MATCHING] Driver ID: {message_data.get('driver_id')}, Station: {message_data.get('nearby_station_name')}", flush=True)
            # Debug: log full message to catch missing fields
            print(f"[MATCHING] Payload: {message_data}", flush=True)
            self.process_matching_request(message_data)
        except Exception as e:
            print(f"[MATCHING] Error processing message: {e}", flush=True)
            import traceback
            traceback.print_exc()
    
    def start_consuming(self):
        """Start consuming messages from RabbitMQ"""
        print(f"[MATCHING] Connecting to RabbitMQ: {self.rabbitmq_url}", flush=True)
        
        try:
            # Connect to RabbitMQ
            connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
            print("[MATCHING] RabbitMQ connection established!", flush=True)
            
            channel = connection.channel()
            print("[MATCHING] Channel created!", flush=True)
            
            # Declare queue (idempotent)
            channel.queue_declare(queue='matching_queue', durable=True)
            print("[MATCHING] Queue declared!", flush=True)
            
            # Set QoS - prefetch only 1 message at a time for fair distribution
            channel.basic_qos(prefetch_count=1)
            print("[MATCHING] QoS configured!", flush=True)
            
            # Start consuming with auto_ack (like reference code)
            channel.basic_consume(
                queue='matching_queue',
                on_message_callback=self.callback,
                auto_ack=True  # Automatically acknowledge messages
            )
            print("[MATCHING] Consumer registered!", flush=True)
            
            print("[MATCHING] ✅ READY! Waiting for matching requests...", flush=True)
            print("[MATCHING] Press Ctrl+C to stop", flush=True)
            
            channel.start_consuming()
            
        except KeyboardInterrupt:
            print("\n[MATCHING] Shutting down...")
        except Exception as e:
            print(f"[MATCHING] Connection error: {e}")
            print("[MATCHING] Retrying in 5 seconds...")
            import time
            time.sleep(5)
            self.start_consuming()  # Retry


if __name__ == '__main__':
    print("[MATCHING] ===== STARTING MATCHING CONSUMER =====", flush=True)
    print(f"[MATCHING] Python: {sys.version}", flush=True)
    print(f"[MATCHING] Working dir: {os.getcwd()}", flush=True)
    
    try:
        print("[MATCHING] Creating MatchingConsumer instance...", flush=True)
        consumer = MatchingConsumer()
        print("[MATCHING] Consumer created! Starting to consume...", flush=True)
        print(f"[MATCHING] Consumer object: {consumer}", flush=True)
        print(f"[MATCHING] About to call start_consuming()...", flush=True)
        consumer.start_consuming()
        print("[MATCHING] start_consuming() returned!", flush=True)
    except Exception as e:
        print(f"[MATCHING] FATAL ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    print("[MATCHING] Main block completed!", flush=True)

