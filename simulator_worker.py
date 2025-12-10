"""
Driver Simulation Worker - Implements the "Golden Logic"

This worker runs a simulation loop for all active drivers.
It follows the exact trace specified:
1. Driver moves through route coordinates
2. When near a station, publishes to RabbitMQ
3. If matched, waits at station for 5 simulation ticks
4. Then continues to next waypoint
"""

import os
import sys
import time
import json
import django
import grpc
import pika
import requests
from datetime import datetime, timedelta

print("[SIMULATOR] ===== STARTING DRIVER SIMULATOR =====", flush=True)
print(f"[SIMULATOR] Python: {sys.version}", flush=True)
print(f"[SIMULATOR] Working dir: {os.getcwd()}", flush=True)

# Setup Django
print("[SIMULATOR] Setting up Django...", flush=True)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'driver_service.settings')
django.setup()
print("[SIMULATOR] Django setup complete!", flush=True)

from drivers.models import Driver
from django.conf import settings
print("[SIMULATOR] Django models imported!", flush=True)

# Import proto files
print("[SIMULATOR] Importing proto files...", flush=True)
sys.path.insert(0, os.path.dirname(__file__))
from proto_generated import location_pb2, location_pb2_grpc
from proto_generated import station_pb2, station_pb2_grpc
print("[SIMULATOR] Proto files imported!", flush=True)


class SimulationWorker:
    
    def __init__(self):
        self.rabbitmq_url = settings.RABBITMQ_URL
        self.location_service_host = settings.LOCATION_SERVICE_HOST
        self.location_service_port = settings.LOCATION_SERVICE_PORT
        self.station_service_host = settings.STATION_SERVICE_HOST
        self.station_service_port = settings.STATION_SERVICE_PORT
        
        # Setup gRPC clients
        self.setup_grpc_clients()
        
        print("[SIMULATOR] Worker initialized (RabbitMQ: fresh connection per publish)")
    
    def setup_grpc_clients(self):
        """Setup gRPC clients for Location and Station services"""
        try:
            # Location Service
            location_address = f"{self.location_service_host}:{self.location_service_port}"
            location_channel = grpc.insecure_channel(location_address)
            self.location_stub = location_pb2_grpc.LocationServiceStub(location_channel)
            
            # Station Service
            station_address = f"{self.station_service_host}:{self.station_service_port}"
            station_channel = grpc.insecure_channel(station_address)
            self.station_stub = station_pb2_grpc.StationServiceStub(station_channel)
            
            print("[SIMULATOR] gRPC clients initialized")
        except Exception as e:
            print(f"[SIMULATOR] gRPC client setup failed: {e}")
            self.location_stub = None
            self.station_stub = None
    
    def get_all_stations(self):
        """Fetch all stations from Station Service"""
        try:
            request = station_pb2.ListStationsRequest(limit=1000, offset=0)
            response = self.station_stub.ListStations(request)
            
            stations = []
            for station in response.stations:
                stations.append({
                    'id': station.station_id,
                    'name': station.name,
                    'lat': station.latitude,
                    'lng': station.longitude
                })
            
            return stations
        except Exception as e:
            print(f"[SIMULATOR] Failed to fetch stations: {e}")
            return []
    
    def is_near_station(self, driver_lat, driver_lng, station_lat, station_lng):
        """Check if driver is near a station (within 100m)"""
        try:
            request = location_pb2.ProximityRequest(
                lat1=driver_lat,
                lng1=driver_lng,
                lat2=station_lat,
                lng2=station_lng,
                threshold_meters=100.0
            )
            response = self.location_stub.IsNearby(request)
            return response.is_nearby, response.distance_meters
        except Exception as e:
            print(f"[SIMULATOR] Location check failed: {e}")
            return False, -1.0
    
    def is_coordinate_a_station(self, coord, stations):
        """Check if a coordinate matches any station"""
        # First, simple Euclidian distance check locally to save gRPC calls
        # and handle floating point jitter better
        
        for station in stations:
            # Simple approx distance check (lat/lng degrees)
            # 0.0001 deg is approx 11 meters
            lat_diff = abs(coord['lat'] - station['lat'])
            lng_diff = abs(coord['lng'] - station['lng'])
            
            if lat_diff < 0.0005 and lng_diff < 0.0005:  # ~50m threshold
                return True, station
        return False, None
    
    def complete_driver_trips(self, driver_id):
        """Complete all active trips for a driver when they reach destination"""
        try:
            trip_host = os.environ.get('TRIP_SERVICE_HOST', 'localhost')
            trip_port = os.environ.get('TRIP_SERVICE_PORT', '8008')
            headers = {'Host': 'localhost'}  # trip_service host has underscore; force safe Host
            
            # Get active trips for this driver
            url = f"http://{trip_host}:{trip_port}/api/trips/by_driver/?driver_id={driver_id}"
            response = requests.get(url, headers=headers, timeout=3)
            
            if response.status_code == 200:
                trips = response.json()
                
                # Complete all ACTIVE or SCHEDULED trips
                for trip in trips:
                    trip_status = trip.get('status')
                    if trip_status in ['ACTIVE', 'SCHEDULED']:
                        trip_id = trip['id']
                        
                        # If SCHEDULED, start it first to follow state machine
                        if trip_status == 'SCHEDULED':
                            print(f"[SIMULATOR] Trip {trip_id} is SCHEDULED. Starting it before completion...")
                            start_url = f"http://{trip_host}:{trip_port}/api/trips/{trip_id}/start/"
                            requests.post(start_url, headers=headers, timeout=3)
                            
                        complete_url = f"http://{trip_host}:{trip_port}/api/trips/{trip_id}/complete/"
                        
                        complete_response = requests.post(complete_url, headers=headers, timeout=3)
                        
                        if complete_response.status_code == 200:
                            print(f"[SIMULATOR] ✅ Trip {trip_id} completed for driver {driver_id}")
                        else:
                            print(f"[SIMULATOR] ⚠️ Failed to complete trip {trip_id}: {complete_response.status_code} - {complete_response.text}")
            else:
                print(f"[SIMULATOR] ⚠️ Failed to fetch trips for driver {driver_id}: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"[SIMULATOR] ❌ Error completing trips for driver {driver_id}: {e}", flush=True)
    
    def start_driver_trips(self, driver_id):
        """Start all SCHEDULED trips for a driver (when they pick up rider)"""
        try:
            trip_host = os.environ.get('TRIP_SERVICE_HOST', 'localhost')
            trip_port = os.environ.get('TRIP_SERVICE_PORT', '8008')
            headers = {'Host': 'localhost'}
            
            # Get active trips for this driver
            url = f"http://{trip_host}:{trip_port}/api/trips/by_driver/?driver_id={driver_id}"
            response = requests.get(url, headers=headers, timeout=3)
            
            if response.status_code == 200:
                trips = response.json()
                
                # Start all SCHEDULED trips
                for trip in trips:
                    if trip.get('status') == 'SCHEDULED':
                        trip_id = trip['id']
                        start_url = f"http://{trip_host}:{trip_port}/api/trips/{trip_id}/start/"
                        
                        start_response = requests.post(start_url, headers=headers, timeout=3)
                        
                        if start_response.status_code == 200:
                            print(f"[SIMULATOR] ✅ Trip {trip_id} STARTED for driver {driver_id}")
                        else:
                            print(f"[SIMULATOR] ⚠️ Failed to start trip {trip_id}: {start_response.status_code} - {start_response.text}")
            else:
                print(f"[SIMULATOR] ⚠️ Failed to fetch trips (start phase) for driver {driver_id}: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"[SIMULATOR] ❌ Error starting trips for driver {driver_id}: {e}", flush=True)
    
    def publish_to_matching_queue(self, driver, nearby_station):
        """Publish driver location to RabbitMQ matching queue"""
        try:
            # Create fresh connection for each publish (like your reference code)
            connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
            channel = connection.channel()
            
            # Declare queue (idempotent)
            channel.queue_declare(queue='matching_queue', durable=True)
            
            message = {
                'driver_id': driver.id,
                'user_id': driver.user_id,
                'nearby_station_id': nearby_station['id'],
                'nearby_station_name': nearby_station['name'],
                'current_lat': driver.current_lat,
                'current_lng': driver.current_lng,
                'timestamp': driver.sim_timestamp,
                'free_seats': driver.free_seats,
                'destination_lat': driver.current_lat,
                'destination_lng': driver.current_lng
            }
            
            channel.basic_publish(
                exchange='',
                routing_key='matching_queue',
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                )
            )
            
            # Close connection after publishing (like your reference code)
            connection.close()
            
            print(f"[SIMULATOR] Published to queue: Driver {driver.id} near Station {nearby_station['id']}")
            return True
        except Exception as e:
            print(f"[SIMULATOR] Failed to publish to queue: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def increment_sim_time(self, current_time_str):
        """Increment simulation time by 1 minute"""
        try:
            # Parse HH:MM format
            hour, minute = map(int, current_time_str.split(':'))
            
            # Create datetime and add 1 minute
            dt = datetime(2024, 1, 1, hour, minute)
            dt += timedelta(minutes=1)
            
            # Return as HH:MM string
            return dt.strftime('%H:%M')
        except:
            return "10:00"
    
    def simulate_driver_tick(self, driver, stations):
        """
        Simulate one tick for a driver following the Golden Logic:
        
        1. Check Head of Route Queue
        2. If head is a Station:
           - Do NOT pop immediately
           - Increment wait_counter
           - If wait_counter < 5: Stay at station
           - If wait_counter == 5: Pop station, reset counter, move next
        3. If head is NOT a station:
           - Pop coordinate
           - Update current_location
           - Check proximity to any station
           - If NEAR station: Publish to RabbitMQ
        """
        
        next_coord = driver.peek_route()
        
        if not next_coord:
            # No more waypoints, route complete - COMPLETE TRIP, STOP SIMULATION & DELETE DRIVER
            print(f"[SIMULATOR] Driver {driver.id} - Route complete!")
            
            # Complete any active trips for this driver
            self.complete_driver_trips(driver.id)
            
            driver.is_simulating = False
            driver.save()
            print(f"[SIMULATOR] Driver {driver.id} - Simulation stopped")
            driver.delete()
            print(f"[SIMULATOR] Driver {driver.id} - Deleted successfully")
            return
        
        # Check if next coordinate is a matched station
        is_station, station_info = self.is_coordinate_a_station(next_coord, stations)
        
        if is_station and driver.matched_station_id == station_info['id']:
            # GOLDEN LOGIC: We're at a matched station, WAIT
            print(f"[SIMULATOR] Driver {driver.id} - Waiting at station {station_info['name']} "
                  f"(counter: {driver.wait_counter}/5)")
            
            if driver.wait_counter < 5:
                # Still waiting
                driver.wait_counter += 1
                driver.save()
                return
            else:
                # Wait complete, pop the station and move on
                print(f"[SIMULATOR] Driver {driver.id} - Wait complete at {station_info['name']}, moving on")
                
                # CRITICAL: Start the trip now (Pickup happened)
                self.start_driver_trips(driver.id)
                
                driver.pop_route()
                driver.matched_station_id = None
                driver.wait_counter = 0
                driver.save()
                return
        
        # NOT at a matched station (or not a station at all)
        # Pop the coordinate and move
        coord = driver.pop_route()
        driver.current_lat = coord['lat']
        driver.current_lng = coord['lng']
        driver.sim_timestamp = self.increment_sim_time(driver.sim_timestamp)
        driver.save()
        
        print(f"[SIMULATOR] T={driver.sim_timestamp} Driver {driver.id} moved to "
              f"({driver.current_lat:.4f}, {driver.current_lng:.4f})")
        
        # Check if we're now near any station
        for station in stations:
            is_nearby, distance = self.is_near_station(
                driver.current_lat, driver.current_lng,
                station['lat'], station['lng']
            )
            
            if is_nearby:
                print(f"[SIMULATOR] Driver {driver.id} is near {station['name']} "
                      f"({distance:.2f}m) - Publishing to matching queue")
                self.publish_to_matching_queue(driver, station)
                break  # Only publish once per tick
    
    def run(self):
        """Main simulation loop"""
        print("[SIMULATOR] Starting simulation loop...", flush=True)
        
        tick_interval = 3  # seconds (each tick = 1 simulation minute)
        
        print("[SIMULATOR] Entering while loop...", flush=True)
        while True:
            try:
                print("[SIMULATOR] Tick start...", flush=True)
                # Get all stations (cache this in production)
                stations = self.get_all_stations()
                print(f"[SIMULATOR] Fetched {len(stations)} stations", flush=True)
                
                # Get all active drivers
                active_drivers = Driver.objects.filter(is_simulating=True)
                print(f"[SIMULATOR] Found {active_drivers.count()} active drivers", flush=True)
                
                if active_drivers.count() > 0:
                    print(f"\n[SIMULATOR] Tick - {active_drivers.count()} active driver(s)", flush=True)
                
                # Simulate each driver
                for driver in active_drivers:
                    self.simulate_driver_tick(driver, stations)
                
                # Wait before next tick
                print(f"[SIMULATOR] Sleeping {tick_interval}s...", flush=True)
                time.sleep(tick_interval)
                
            except KeyboardInterrupt:
                print("\n[SIMULATOR] Shutting down...", flush=True)
                break
            except Exception as e:
                print(f"[SIMULATOR] Error in simulation loop: {e}", flush=True)
                import traceback
                traceback.print_exc()
                time.sleep(tick_interval)


if __name__ == '__main__':
    print("[SIMULATOR] Creating SimulationWorker instance...", flush=True)
    try:
        worker = SimulationWorker()
        print("[SIMULATOR] Worker created! Starting simulation loop...", flush=True)
        print(f"[SIMULATOR] Worker object: {worker}", flush=True)
        print(f"[SIMULATOR] About to call worker.run()...", flush=True)
        worker.run()
        print("[SIMULATOR] worker.run() returned!", flush=True)
    except Exception as e:
        print(f"[SIMULATOR] FATAL ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    print("[SIMULATOR] Main block completed!", flush=True)

