#!/bin/sh
python manage.py migrate
python manage.py runserver 0.0.0.0:8001 &
python users/grpc_service.py

