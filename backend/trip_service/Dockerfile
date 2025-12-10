FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    django==4.2.7 \
    djangorestframework==3.14.0 \
    psycopg2-binary==2.9.9 \
    django-cors-headers==4.3.1 \
    requests==2.31.0

# Copy application
COPY . .

# Expose port
EXPOSE 8008

# Run migrations and start server
CMD python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:8008

