# LastMile - Metro Feeder Ride-Sharing Application

> A production-grade microservices application demonstrating auto-scaling, message queuing, and real-time geospatial matching.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.2+-green.svg)](https://djangoproject.com)
[![React](https://img.shields.io/badge/React-18.2+-61dafb.svg)](https://reactjs.org)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-326ce5.svg)](https://kubernetes.io)

## What is LastMile?

LastMile connects **drivers** with **riders** at metro stations through intelligent geospatial matching. When a driver approaches a metro station, the system automatically matches them with riders heading in similar directions.

### The "Golden Logic"

```
Driver Route: Hosur → Electronic City → HSR Layout → Koromangala
Station: Bommanahalli (near HSR Layout)
Rider: Waiting at Bommanahalli, ETA 10:05

10:00 - Driver starts at Hosur
10:01 - Moves to Electronic City
10:02 - Reaches HSR Layout (near Bommanahalli)
        → System detects proximity
        → Matches with rider
        → Reroutes driver to station
10:03 - Driver arrives at Bommanahalli
10:03-10:07 - Driver waits for rider (5 simulation ticks)
10:08 - Rider picked up, continue to Koromangala
```

##  Quick Start (2 minutes)

### Option 1: Docker Compose (Recommended)

```bash
# 1. Start all backend services
cd backend
docker-compose up -d

# 2. Start frontend (new terminal)
cd frontend
npm install
npm start

# 3. Run the demo
python demo/seed_and_simulate.py
```

**Open**: http://localhost:3000

### Option 2: Kubernetes

```bash
# Deploy everything with one command
chmod +x deploy-k8s.sh
./deploy-k8s.sh

# Port forward services (new terminals)
kubectl port-forward svc/frontend 3000:3000 -n lastmile
kubectl port-forward svc/user-service 8001:8001 -n lastmile
kubectl port-forward svc/station-service 8002:8002 -n lastmile
kubectl port-forward svc/rider-service 8003:8003 -n lastmile
kubectl port-forward svc/driver-service 8004:8004 -n lastmile
kubectl port-forward svc/matching-service 8005:8005 -n lastmile

# Run demo
python demo/seed_and_simulate.py
```

##  Architecture

```
┌──────────────┐
│   Frontend   │ React + Leaflet + OpenStreetMap
│  (Port 3000) │
└──────┬───────┘
       │ REST API
       │
┌──────┴────────────────────────────────────────┐
│           Microservices Layer                 │
├───────────┬──────────┬──────────┬────────────┤
│  User     │ Station  │  Rider   │  Driver    │
│  (8001)   │ (8002)   │ (8003)   │ (8004)     │
├───────────┴──────────┴──────────┴────────────┤
│        Location (gRPC) │ Matching (8005)     │
│                        │ [Auto-scaling 1-5]  │
└────────────────────────┴──────────┬──────────┘
                                    │
                              ┌─────┴─────┐
                              │ RabbitMQ  │
                              └───────────┘
```

###  Services

| Service | Port | Purpose | Key Feature |
|---------|------|---------|-------------|
| User Service | 8001 | Authentication | JWT tokens |
| Station Service | 8002 | Metro stations | Geospatial indexing |
| Rider Service | 8003 | Ride requests | ETA tracking |
| Driver Service | 8004 | Driver & simulation | Route queue |
| Location Service | gRPC 50056 | Distance calc | 100m proximity |
| Matching Service | 8005 | Match algorithm | **Auto-scales 1-5** |

##  Key Features

### ✅ Implemented Requirements
- ✅ **Microservices**: 6 independent services with database-per-service
- ✅ **gRPC**: All inter-service communication
- ✅ **RabbitMQ**: Asynchronous matching queue
- ✅ **Kubernetes**: Complete deployment manifests
- ✅ **HPA**: Auto-scaling from 1 to 5 replicas
- ✅ **Django Backend**: Python with REST + gRPC
- ✅ **React Frontend**: JavaScript (NO TypeScript)
- ✅ **Leaflet Maps**: OpenStreetMap integration
- ✅ **Real-time Simulation**: Driver movement engine
- ✅ **Golden Logic**: Exact trace implementation

###  Technical Highlights
- **Auto-scaling Demo**: Matching service scales based on CPU
- **Fault Tolerance**: RabbitMQ ensures no lost matches
- **Real-time Updates**: Live driver tracking on map
- **Geospatial Matching**: 100m proximity detection
- **Interactive UI**: Click-to-draw routes on map
- **Production Ready**: Health checks, resource limits, HPA

##  Demo Output

```
==============================================================
  STEP 1: Creating Test Users
==============================================================
✓ Driver user created successfully
✓ Rider user created successfully

==============================================================
  STEP 2: Creating Metro Station
==============================================================
✓ Station created: Bommanahalli Metro Station

==============================================================
  STEP 5: Starting Simulation
==============================================================
✓ Simulation started!

==============================================================
  STEP 6: Monitoring Simulation
==============================================================
[10:00] Driver at: (12.7340, 77.6197) | Queue: 3 waypoints
[10:01] Driver at: (12.8457, 77.6609) | Queue: 2 waypoints
[10:02] Driver at: (12.9165, 77.6233) | Queue: 1 waypoints

🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉
  MATCH FOUND!
🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉

✓ The Golden Logic worked! Driver will wait at station.
```

##  Using the Application

### As a Driver
1. Register with role: `DRIVER`
2. Click on map to draw your route (min 2 points)
3. Click "Create Driver"
4. Click "Start Simulation"
5. Watch your car move on the map in real-time!

### As a Rider
1. Register with role: `RIDER`
2. Select your target metro station
3. Enter your ETA (when you'll reach the station)
4. Click on map to set your destination
5. Click "Request Ride"
6. Get matched when a driver passes nearby!

### As Admin
1. Go to `/admin` route
2. Click on map to add new metro stations
3. Monitor all active drivers

##  Deployment Options

### Local Development (Docker Compose)
```bash
cd backend
docker-compose up -d
cd ../frontend
npm start
```

### Kubernetes (with Auto-scaling)
```bash
./deploy-k8s.sh

# Watch auto-scaling in action
kubectl get hpa -n lastmile -w
kubectl get pods -n lastmile -w
```

### Generate Load (to see auto-scaling)
```bash
# Run 5 simulations simultaneously
for i in {1..5}; do python demo/seed_and_simulate.py & done

# Watch matching service scale from 1 to 5 replicas
kubectl get hpa -n lastmile -w
```

##  Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment instructions
- **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** - Architecture deep-dive
- **[k8s/README.md](k8s/README.md)** - Kubernetes-specific guide

##  Monitoring

### Check Service Health
```bash
# Docker Compose
docker-compose ps
docker-compose logs -f matching_service

# Kubernetes
kubectl get pods -n lastmile
kubectl logs -f deployment/matching-service -n lastmile
```

### RabbitMQ Management
```bash
# Docker Compose
http://localhost:15672 (admin/admin)

# Kubernetes
kubectl port-forward svc/rabbitmq 15672:15672 -n lastmile
```

### Auto-scaling Status
```bash
kubectl get hpa -n lastmile
kubectl describe hpa matching-service-hpa -n lastmile
```

## 🛠️ Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React.js 18.2, Leaflet.js, React-Router |
| Backend | Django 4.2, Django REST Framework |
| Inter-service | gRPC (grpcio, protobuf) |
| Message Queue | RabbitMQ 3.12 |
| Database | PostgreSQL 15 (per-service) |
| Geospatial | geopy (geodesic distance) |
| Orchestration | Kubernetes, HPA |
| Containerization | Docker, Docker Compose |

##  Project Structure

```
LastMile/
├── backend/
│   ├── user_service/          # Django + gRPC
│   ├── station_service/       # Django + gRPC
│   ├── rider_service/         # Django + gRPC
│   ├── driver_service/        # Django + gRPC + Simulator
│   ├── matching_service/      # Django + RabbitMQ Consumer
│   ├── location_service/      # gRPC (stateless)
│   └── proto/                 # Protocol buffer definitions
├── frontend/                  # React + Leaflet
├── k8s/                       # Kubernetes manifests + HPA
└── demo/                      # Demo script
```

##  Learning Outcomes

This project demonstrates:
- Microservices architecture
- gRPC communication
- Message queue patterns
- Kubernetes orchestration
- Horizontal pod autoscaling
- Real-time simulations
- Geospatial computing
- Event-driven architecture

##  Development

### Prerequisites
- Python 3.9+
- Node.js 16+
- Docker & Docker Compose
- kubectl (for K8s deployment)

### Setup
```bash
# Backend
cd backend
pip install -r requirements.txt
./compile_protos.sh

# Frontend
cd frontend
npm install
```

## 🧪 Testing

```bash
# Run demo to verify everything works
python demo/seed_and_simulate.py

# Expected output: Match found within 90 seconds
```

## Contributing

This is an academic project demonstrating cloud computing concepts.

##  License

Educational use only.

##  Author

Built for Cloud Computing course project.
Aadil Mohammad Husain (MT2024001)
Prabal Singh (MT2024172)

** Star this repo if you found it helpful!**

For questions: Check `DEPLOYMENT_GUIDE.md` or `PROJECT_OVERVIEW.md`

