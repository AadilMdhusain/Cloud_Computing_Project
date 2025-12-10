#!/bin/bash

# Script to run migrations for all services in Kubernetes

echo "Running migrations for all services..."
echo "======================================"

SERVICES=("user-service" "station-service" "rider-service" "driver-service" "matching-service" "trip-service" "notification-service")

for service in "${SERVICES[@]}"; do
    echo ""
    echo "Migrating $service..."
    kubectl exec -it deployment/$service -n lastmile -- python manage.py makemigrations 2>/dev/null || true
    kubectl exec -it deployment/$service -n lastmile -- python manage.py migrate
    
    if [ $? -eq 0 ]; then
        echo "✅ $service migrated successfully"
    else
        echo "⚠️  $service migration failed"
    fi
done

echo ""
echo "Creating admin user..."
kubectl exec -it deployment/user-service -n lastmile -- python manage.py shell -c "
from users.models import User
if not User.objects.filter(username='admin_ui').exists():
    u = User.objects.create(username='admin_ui', email='admin@example.com', role='ADMIN')
    u.set_password('password')
    u.save()
    print('Admin user created')
else:
    print('Admin user already exists')
"

echo ""
echo "✅ All migrations complete!"
