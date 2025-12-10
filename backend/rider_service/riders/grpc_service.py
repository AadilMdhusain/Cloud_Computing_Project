import sys
import os
import django

# Add parent directory to path for Django app imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rider_service.settings')
django.setup()

from riders.models import RideRequest
import grpc
from concurrent import futures
from datetime import datetime

# Import generated proto files
from proto_generated import rider_pb2, rider_pb2_grpc


class RiderServiceServicer(rider_pb2_grpc.RiderServiceServicer):
    
    def CreateRideRequest(self, request, context):
        try:
            ride_request = RideRequest.objects.create(
                rider_id=request.rider_id,
                station_id=request.station_id,
                eta=request.eta,
                destination_lat=request.destination_lat,
                destination_lng=request.destination_lng,
                status='LOOKING'
            )
            
            return rider_pb2.RideResponse(
                success=True,
                ride_request_id=ride_request.id,
                rider_id=ride_request.rider_id,
                station_id=ride_request.station_id,
                eta=ride_request.eta,
                destination_lat=ride_request.destination_lat,
                destination_lng=ride_request.destination_lng,
                status=ride_request.status,
                message="Ride request created successfully"
            )
        except Exception as e:
            return rider_pb2.RideResponse(
                success=False,
                message=str(e)
            )
    
    def GetRideRequest(self, request, context):
        try:
            ride_request = RideRequest.objects.get(id=request.ride_request_id)
            return rider_pb2.RideResponse(
                success=True,
                ride_request_id=ride_request.id,
                rider_id=ride_request.rider_id,
                station_id=ride_request.station_id,
                eta=ride_request.eta,
                destination_lat=ride_request.destination_lat,
                destination_lng=ride_request.destination_lng,
                status=ride_request.status,
                message="Ride request retrieved successfully"
            )
        except RideRequest.DoesNotExist:
            return rider_pb2.RideResponse(
                success=False,
                message="Ride request not found"
            )
        except Exception as e:
            return rider_pb2.RideResponse(
                success=False,
                message=str(e)
            )
    
    def UpdateRideStatus(self, request, context):
        try:
            ride_request = RideRequest.objects.get(id=request.ride_request_id)
            ride_request.status = request.status
            ride_request.save()
            
            return rider_pb2.RideResponse(
                success=True,
                ride_request_id=ride_request.id,
                rider_id=ride_request.rider_id,
                station_id=ride_request.station_id,
                eta=ride_request.eta,
                destination_lat=ride_request.destination_lat,
                destination_lng=ride_request.destination_lng,
                status=ride_request.status,
                message="Ride status updated successfully"
            )
        except RideRequest.DoesNotExist:
            return rider_pb2.RideResponse(
                success=False,
                message="Ride request not found"
            )
        except Exception as e:
            return rider_pb2.RideResponse(
                success=False,
                message=str(e)
            )
    
    def GetRidersByStation(self, request, context):
        try:
            # Get all riders looking for a ride at this station
            ride_requests = RideRequest.objects.filter(
                station_id=request.station_id,
                status='LOOKING'
            )
            
            # Filter by max ETA if provided
            if request.max_eta:
                # Convert max_eta string (HH:MM) to comparable format
                # In production, you'd want more sophisticated time comparison
                ride_requests = ride_requests.filter(eta__lte=request.max_eta)
            
            ride_responses = []
            for ride_request in ride_requests:
                ride_responses.append(
                    rider_pb2.RideResponse(
                        success=True,
                        ride_request_id=ride_request.id,
                        rider_id=ride_request.rider_id,
                        station_id=ride_request.station_id,
                        eta=ride_request.eta,
                        destination_lat=ride_request.destination_lat,
                        destination_lng=ride_request.destination_lng,
                        status=ride_request.status
                    )
                )
            
            return rider_pb2.RideListResponse(
                success=True,
                rides=ride_responses,
                count=len(ride_responses)
            )
        except Exception as e:
            return rider_pb2.RideListResponse(
                success=False,
                count=0
            )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rider_pb2_grpc.add_RiderServiceServicer_to_server(RiderServiceServicer(), server)
    server.add_insecure_port('[::]:50053')
    print("Rider gRPC server starting on port 50053...")
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()

