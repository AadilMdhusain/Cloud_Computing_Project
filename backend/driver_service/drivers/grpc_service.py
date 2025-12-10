import sys
import os
import django

# Add parent directory to path for Django app imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'driver_service.settings')
django.setup()

from drivers.models import Driver
import grpc
from concurrent import futures

# Import generated proto files
from proto_generated import driver_pb2, driver_pb2_grpc


class DriverServiceServicer(driver_pb2_grpc.DriverServiceServicer):
    
    def CreateDriver(self, request, context):
        try:
            # Convert route from proto to JSON-serializable format
            route = []
            for coord in request.route:
                route.append({
                    'lat': coord.latitude,
                    'lng': coord.longitude
                })
            
            driver = Driver.objects.create(
                user_id=request.user_id,
                free_seats=request.free_seats
            )
            driver.route_queue = route
            
            # Set initial position to first coordinate
            if route:
                driver.current_lat = route[0]['lat']
                driver.current_lng = route[0]['lng']
            
            driver.save()
            
            # Convert route back to proto format for response
            route_coords = []
            for coord in driver.route_queue:
                route_coords.append(driver_pb2.Coordinate(
                    latitude=coord['lat'],
                    longitude=coord['lng']
                ))
            
            return driver_pb2.DriverResponse(
                success=True,
                driver_id=driver.id,
                user_id=driver.user_id,
                current_lat=driver.current_lat,
                current_lng=driver.current_lng,
                free_seats=driver.free_seats,
                route_queue=route_coords,
                sim_timestamp=driver.sim_timestamp,
                matched_station_id=driver.matched_station_id or 0,
                message="Driver created successfully"
            )
        except Exception as e:
            return driver_pb2.DriverResponse(
                success=False,
                message=str(e)
            )
    
    def GetDriver(self, request, context):
        try:
            driver = Driver.objects.get(id=request.driver_id)
            
            # Convert route to proto format
            route_coords = []
            for coord in driver.route_queue:
                route_coords.append(driver_pb2.Coordinate(
                    latitude=coord['lat'],
                    longitude=coord['lng']
                ))
            
            return driver_pb2.DriverResponse(
                success=True,
                driver_id=driver.id,
                user_id=driver.user_id,
                current_lat=driver.current_lat,
                current_lng=driver.current_lng,
                free_seats=driver.free_seats,
                route_queue=route_coords,
                sim_timestamp=driver.sim_timestamp,
                matched_station_id=driver.matched_station_id or 0,
                message="Driver retrieved successfully"
            )
        except Driver.DoesNotExist:
            return driver_pb2.DriverResponse(
                success=False,
                message="Driver not found"
            )
        except Exception as e:
            return driver_pb2.DriverResponse(
                success=False,
                message=str(e)
            )
    
    def UpdateDriverLocation(self, request, context):
        try:
            driver = Driver.objects.get(id=request.driver_id)
            driver.current_lat = request.latitude
            driver.current_lng = request.longitude
            driver.save()
            
            route_coords = []
            for coord in driver.route_queue:
                route_coords.append(driver_pb2.Coordinate(
                    latitude=coord['lat'],
                    longitude=coord['lng']
                ))
            
            return driver_pb2.DriverResponse(
                success=True,
                driver_id=driver.id,
                user_id=driver.user_id,
                current_lat=driver.current_lat,
                current_lng=driver.current_lng,
                free_seats=driver.free_seats,
                route_queue=route_coords,
                sim_timestamp=driver.sim_timestamp,
                matched_station_id=driver.matched_station_id or 0,
                message="Location updated successfully"
            )
        except Driver.DoesNotExist:
            return driver_pb2.DriverResponse(
                success=False,
                message="Driver not found"
            )
        except Exception as e:
            return driver_pb2.DriverResponse(
                success=False,
                message=str(e)
            )
    
    def UpdateDriverRoute(self, request, context):
        """
        CRITICAL: This is called by Matching Service to update driver route
        when a match is found. Push the station to the FRONT of the queue.
        """
        try:
            driver = Driver.objects.get(id=request.driver_id)
            
            if request.action == "PUSH_FRONT":
                # Push station coordinate to front of queue
                station_coord = {
                    'lat': request.station_lat,
                    'lng': request.station_lng
                }
                driver.push_front_route(station_coord)
                driver.matched_station_id = request.station_id
                driver.wait_counter = 0  # Reset wait counter
                driver.save()
                
                print(f"[ROUTE UPDATE] Driver {driver.id} - Pushed station {request.station_id} to front")
            
            route_coords = []
            for coord in driver.route_queue:
                route_coords.append(driver_pb2.Coordinate(
                    latitude=coord['lat'],
                    longitude=coord['lng']
                ))
            
            return driver_pb2.DriverResponse(
                success=True,
                driver_id=driver.id,
                user_id=driver.user_id,
                current_lat=driver.current_lat,
                current_lng=driver.current_lng,
                free_seats=driver.free_seats,
                route_queue=route_coords,
                sim_timestamp=driver.sim_timestamp,
                matched_station_id=driver.matched_station_id or 0,
                message="Route updated successfully"
            )
        except Driver.DoesNotExist:
            return driver_pb2.DriverResponse(
                success=False,
                message="Driver not found"
            )
        except Exception as e:
            return driver_pb2.DriverResponse(
                success=False,
                message=str(e)
            )
    
    def StartSimulation(self, request, context):
        try:
            driver = Driver.objects.get(id=request.driver_id)
            driver.is_simulating = True
            driver.save()
            
            return driver_pb2.SimulationResponse(
                success=True,
                message="Simulation started"
            )
        except Driver.DoesNotExist:
            return driver_pb2.SimulationResponse(
                success=False,
                message="Driver not found"
            )
        except Exception as e:
            return driver_pb2.SimulationResponse(
                success=False,
                message=str(e)
            )
    
    def StopSimulation(self, request, context):
        try:
            driver = Driver.objects.get(id=request.driver_id)
            driver.is_simulating = False
            driver.save()
            
            return driver_pb2.SimulationResponse(
                success=True,
                message="Simulation stopped"
            )
        except Driver.DoesNotExist:
            return driver_pb2.SimulationResponse(
                success=False,
                message="Driver not found"
            )
        except Exception as e:
            return driver_pb2.SimulationResponse(
                success=False,
                message=str(e)
            )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    driver_pb2_grpc.add_DriverServiceServicer_to_server(DriverServiceServicer(), server)
    server.add_insecure_port('[::]:50054')
    print("Driver gRPC server starting on port 50054...")
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()

