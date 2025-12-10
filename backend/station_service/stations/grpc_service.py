import sys
import os
import django

# Add parent directory to path for Django app imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'station_service.settings')
django.setup()

from stations.models import Station
import grpc
from concurrent import futures

# Import generated proto files
from proto_generated import station_pb2, station_pb2_grpc


class StationServiceServicer(station_pb2_grpc.StationServiceServicer):
    
    def CreateStation(self, request, context):
        try:
            station = Station.objects.create(
                name=request.name,
                latitude=request.latitude,
                longitude=request.longitude
            )
            
            return station_pb2.StationResponse(
                success=True,
                station_id=station.id,
                name=station.name,
                latitude=station.latitude,
                longitude=station.longitude,
                message="Station created successfully"
            )
        except Exception as e:
            return station_pb2.StationResponse(
                success=False,
                message=str(e)
            )
    
    def GetStation(self, request, context):
        try:
            station = Station.objects.get(id=request.station_id)
            return station_pb2.StationResponse(
                success=True,
                station_id=station.id,
                name=station.name,
                latitude=station.latitude,
                longitude=station.longitude,
                message="Station retrieved successfully"
            )
        except Station.DoesNotExist:
            return station_pb2.StationResponse(
                success=False,
                message="Station not found"
            )
        except Exception as e:
            return station_pb2.StationResponse(
                success=False,
                message=str(e)
            )
    
    def ListStations(self, request, context):
        try:
            limit = request.limit if request.limit > 0 else 100
            offset = request.offset if request.offset > 0 else 0
            
            stations = Station.objects.all()[offset:offset+limit]
            total = Station.objects.count()
            
            station_responses = []
            for station in stations:
                station_responses.append(
                    station_pb2.StationResponse(
                        success=True,
                        station_id=station.id,
                        name=station.name,
                        latitude=station.latitude,
                        longitude=station.longitude
                    )
                )
            
            return station_pb2.StationListResponse(
                success=True,
                stations=station_responses,
                total=total
            )
        except Exception as e:
            return station_pb2.StationListResponse(
                success=False,
                total=0
            )
    
    def GetStationsByIds(self, request, context):
        try:
            stations = Station.objects.filter(id__in=request.station_ids)
            
            station_responses = []
            for station in stations:
                station_responses.append(
                    station_pb2.StationResponse(
                        success=True,
                        station_id=station.id,
                        name=station.name,
                        latitude=station.latitude,
                        longitude=station.longitude
                    )
                )
            
            return station_pb2.StationListResponse(
                success=True,
                stations=station_responses,
                total=len(station_responses)
            )
        except Exception as e:
            return station_pb2.StationListResponse(
                success=False,
                total=0
            )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    station_pb2_grpc.add_StationServiceServicer_to_server(StationServiceServicer(), server)
    server.add_insecure_port('[::]:50052')
    print("Station gRPC server starting on port 50052...")
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()

