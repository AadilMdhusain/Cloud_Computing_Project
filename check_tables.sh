#!/bin/bash

echo "=== CHECKING ALL SERVICES ==="
echo ""

echo "1️⃣  DRIVERS (Active):"
curl -s http://localhost:8004/api/drivers/ | python3 -m json.tool
echo ""

echo "2️⃣  RIDE REQUESTS (Looking for drivers):"
curl -s http://localhost:8003/api/rides/ | python3 -m json.tool | grep -A 8 "LOOKING" || echo "No LOOKING rides"
echo ""

echo "3️⃣  STATIONS:"
curl -s http://localhost:8002/api/stations/ | python3 -m json.tool
echo ""

echo "4️⃣  MATCHES:"
curl -s http://localhost:8005/api/matches/ | python3 -m json.tool
echo ""

echo "5️⃣  TRIPS:"
curl -s http://localhost:8008/api/trips/ | python3 -m json.tool
echo ""

echo "6️⃣  NOTIFICATIONS (Last 5):"
curl -s http://localhost:8007/api/notifications/ | python3 -m json.tool | tail -50
echo ""
