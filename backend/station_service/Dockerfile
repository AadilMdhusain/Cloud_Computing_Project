FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    Django==4.2.7 \
    djangorestframework==3.14.0 \
    psycopg2-binary==2.9.9 \
    grpcio==1.59.3 \
    grpcio-tools==1.59.3 \
    protobuf==4.25.1 \
    pika==1.3.2 \
    geopy==2.4.1 \
    django-cors-headers==4.3.1 \
    python-dotenv==1.0.0 \
    celery==5.3.4 \
    redis==5.0.1 \
    requests==2.31.0 \
    supervisor==4.2.5

# Copy service code
COPY . .

# Copy supervisor config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Compile proto files
RUN if [ -d "proto" ]; then \
    mkdir -p proto_generated && \
    python -m grpc_tools.protoc \
    -I./proto \
    --python_out=./proto_generated \
    --grpc_python_out=./proto_generated \
    ./proto/*.proto && \
    touch proto_generated/__init__.py && \
    sed -i 's/^import \(.*\)_pb2 as/from . import \1_pb2 as/g' proto_generated/*_grpc.py; \
    fi

# Expose ports
EXPOSE 8002 50052

# Run migrations and start supervisor
CMD ["sh", "-c", "python manage.py migrate && supervisord -c /etc/supervisor/conf.d/supervisord.conf"]

