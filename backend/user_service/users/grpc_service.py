import sys
import os
import django

# Add parent directory to path for Django app imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_service.settings')
django.setup()

from users.models import User
import grpc
from concurrent import futures

# Import generated proto files
from proto_generated import user_pb2, user_pb2_grpc


class UserServiceServicer(user_pb2_grpc.UserServiceServicer):
    
    def CreateUser(self, request, context):
        try:
            user = User(
                username=request.username,
                email=request.email,
                role=request.role
            )
            user.set_password(request.password)
            user.save()
            
            return user_pb2.UserResponse(
                success=True,
                user_id=user.id,
                username=user.username,
                email=user.email,
                role=user.role,
                message="User created successfully"
            )
        except Exception as e:
            return user_pb2.UserResponse(
                success=False,
                message=str(e)
            )
    
    def AuthenticateUser(self, request, context):
        try:
            user = User.objects.get(username=request.username)
            if user.check_password(request.password):
                import uuid
                token = str(uuid.uuid4())
                return user_pb2.AuthResponse(
                    success=True,
                    token=token,
                    user_id=user.id,
                    role=user.role,
                    message="Authentication successful"
                )
            else:
                return user_pb2.AuthResponse(
                    success=False,
                    message="Invalid credentials"
                )
        except User.DoesNotExist:
            return user_pb2.AuthResponse(
                success=False,
                message="User not found"
            )
        except Exception as e:
            return user_pb2.AuthResponse(
                success=False,
                message=str(e)
            )
    
    def GetUser(self, request, context):
        try:
            user = User.objects.get(id=request.user_id)
            return user_pb2.UserResponse(
                success=True,
                user_id=user.id,
                username=user.username,
                email=user.email,
                role=user.role,
                message="User retrieved successfully"
            )
        except User.DoesNotExist:
            return user_pb2.UserResponse(
                success=False,
                message="User not found"
            )
        except Exception as e:
            return user_pb2.UserResponse(
                success=False,
                message=str(e)
            )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("User gRPC server starting on port 50051...")
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()

