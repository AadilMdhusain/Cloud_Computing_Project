#!/bin/sh
python manage.py migrate
python manage.py runserver 0.0.0.0:8003 &
python riders/grpc_service.py

