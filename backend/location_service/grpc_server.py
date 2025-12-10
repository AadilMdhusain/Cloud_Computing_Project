import sys
import os
import grpc
from concurrent import futures
from geopy.distance import geodesic

# Import generated proto files
# Import generated proto files
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'proto_generated'))
from proto_generated import location_pb2
from proto_generated import location_pb2_grpc


class LocationServiceServicer(location_pb2_grpc.LocationServiceServicer):
    """
    Stateless Location Service for geospatial calculations.
    """
    
    def IsNearby(self, request, context):
        """
        Check if two coordinates are within a threshold distance.
        Default threshold: 100 meters
        """
        try:
            coord1 = (request.lat1, request.lng1)
            coord2 = (request.lat2, request.lng2)
            
            # Calculate distance in meters
            distance_meters = geodesic(coord1, coord2).meters
            
            # Default threshold is 100 meters
            threshold = request.threshold_meters if request.threshold_meters > 0 else 100.0
            
            is_nearby = distance_meters <= threshold
            
            return location_pb2.ProximityResponse(
                is_nearby=is_nearby,
                distance_meters=distance_meters
            )
        except Exception as e:
            print(f"Error in IsNearby: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return location_pb2.ProximityResponse(
                is_nearby=False,
                distance_meters=-1.0
            )
    
    def CalculateDistance(self, request, context):
        """
        Calculate distance between two coordinates in meters.
        """
        try:
            coord1 = (request.lat1, request.lng1)
            coord2 = (request.lat2, request.lng2)
            
            distance_meters = geodesic(coord1, coord2).meters
            
            return location_pb2.DistanceResponse(
                distance_meters=distance_meters
            )
        except Exception as e:
            print(f"Error in CalculateDistance: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return location_pb2.DistanceResponse(
                distance_meters=-1.0
            )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    location_pb2_grpc.add_LocationServiceServicer_to_server(LocationServiceServicer(), server)
    server.add_insecure_port('[::]:50056')
    print("Location gRPC server starting on port 50056...")
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()

