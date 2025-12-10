import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import { driverAPI, stationAPI, matchingAPI } from '../../services/api';
import '../../App.css';

// Fix for default marker icons in React-Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

// Custom marker icons
const driverIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

const stationIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

function MapClickHandler({ onMapClick, isDrawingRoute }) {
  useMapEvents({
    click: (e) => {
      if (isDrawingRoute) {
        onMapClick(e.latlng);
      }
    },
  });
  return null;
}

function DriverDashboard({ user, onLogout }) {
  const [driver, setDriver] = useState(null);
  const [stations, setStations] = useState([]);
  const [route, setRoute] = useState([]);
  const [isDrawingRoute, setIsDrawingRoute] = useState(false);
  const [freeSeats, setFreeSeats] = useState(4);
  const [matches, setMatches] = useState([]);
  const [error, setError] = useState('');

  // Bangalore coordinates (default center)
  const center = [12.9716, 77.5946];

  useEffect(() => {
    loadStations();
    loadDriver();
  }, []);

  useEffect(() => {
    if (driver && driver.driver.id) {
      const interval = setInterval(() => {
        loadDriver();
        loadMatches();
      }, 3000); // Poll every 3 seconds
      return () => clearInterval(interval);
    }
  }, [driver]);

  const loadStations = async () => {
    try {
      const response = await stationAPI.listStations();
      if (response.data.success) {
        setStations(response.data.stations);
      }
    } catch (err) {
      console.error('Failed to load stations:', err);
    }
  };

  const loadDriver = async () => {
    try {
      const response = await driverAPI.getDriverByUser(user.userId);
      if (response.data.success) {
        setDriver(response.data);
      }
    } catch (err) {
      // Driver deleted or doesn't exist - clear state to stop polling errors
      if (err.response?.status === 404 && driver) {
        console.log('Driver deleted - clearing state');
        setDriver(null);
        setMatches([]);
      }
    }
  };

  const loadMatches = async () => {
    if (!driver) return;
    try {
      const response = await matchingAPI.getMatchesByDriver(driver.driver.id);
      if (response.data.success) {
        setMatches(response.data.matches);
      }
    } catch (err) {
      console.error('Failed to load matches:', err);
    }
  };

  const handleMapClick = (latlng) => {
    setRoute([...route, { lat: latlng.lat, lng: latlng.lng }]);
  };

  const clearRoute = () => {
    setRoute([]);
  };

  const createDriver = async () => {
    if (route.length < 2) {
      setError('Please draw a route with at least 2 points');
      return;
    }

    try {
      const response = await driverAPI.createDriver(user.userId, freeSeats, route);
      if (response.data.success) {
        setDriver({ driver: response.data });
        setIsDrawingRoute(false);
        setError('');
        // Reload page to ensure all data is fresh
        window.location.reload();
      } else {
        setError(response.data.message);
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to create driver');
    }
  };

  const startSimulation = async () => {
    try {
      const response = await driverAPI.startSimulation(driver.driver.id);
      if (response.data.success) {
        loadDriver();
      }
    } catch (err) {
      setError('Failed to start simulation');
    }
  };

  const stopSimulation = async () => {
    try {
      const response = await driverAPI.stopSimulation(driver.driver.id);
      if (response.data.success) {
        loadDriver();
      }
    } catch (err) {
      setError('Failed to stop simulation');
    }
  };

  // Driver will be automatically deleted when route completes (handled by simulator)

  return (
    <div className="dashboard">
      <div className="sidebar">
        <div className="sidebar-header">
          <h2>Driver Dashboard</h2>
          <button onClick={onLogout} className="logout-btn">Logout</button>
        </div>

        <div className="user-info">
          <p><strong>Username:</strong> {user.username}</p>
          <p><strong>Role:</strong> {user.role}</p>
        </div>

        {!driver ? (
          <div>
            <div className="instructions">
              <h3>Setup Instructions</h3>
              <p>1. Click "Start Drawing Route"</p>
              <p>2. Click on the map to add waypoints</p>
              <p>3. Add at least 2 points</p>
              <p>4. Click "Create Driver" to save</p>
            </div>

            <div className="form-group">
              <label>Free Seats</label>
              <input
                type="number"
                min="1"
                max="8"
                value={freeSeats}
                onChange={(e) => setFreeSeats(parseInt(e.target.value))}
              />
            </div>

            {!isDrawingRoute ? (
              <button
                onClick={() => setIsDrawingRoute(true)}
                className="btn btn-primary"
              >
                Start Drawing Route
              </button>
            ) : (
              <>
                <button onClick={clearRoute} className="btn btn-danger">
                  Clear Route ({route.length} points)
                </button>
                <button
                  onClick={createDriver}
                  className="btn btn-success"
                  disabled={route.length < 2}
                >
                  Create Driver
                </button>
              </>
            )}

            {error && <div style={{color: '#ff6b6b', marginTop: '10px'}}>{error}</div>}
          </div>
        ) : (
          <div>
            <div className="status-card">
              <h3>Driver Status</h3>
              <p><strong>Current Location:</strong></p>
              <p>Lat: {driver.driver.current_lat?.toFixed(4)}</p>
              <p>Lng: {driver.driver.current_lng?.toFixed(4)}</p>
              <p><strong>Free Seats:</strong> {driver.driver.free_seats}</p>
              <p><strong>Simulation:</strong> {driver.driver.is_simulating ? '🟢 Active' : '🔴 Inactive'}</p>
              <p><strong>Sim Time:</strong> {driver.driver.sim_timestamp}</p>
            </div>

            <div className="route-list">
              <h3>Route Queue ({driver.driver.route_queue?.length || 0})</h3>
              <ul style={{ maxHeight: '200px', overflowY: 'auto' }}>
                {driver.driver.route_queue?.map((coord, idx) => (
                  <li key={idx}>
                    {idx + 1}. ({coord.lat.toFixed(4)}, {coord.lng.toFixed(4)})
                  </li>
                ))}
              </ul>
            </div>

            {matches.length > 0 && (
              <div className="status-card">
                <h3>Matches ({matches.length})</h3>
                {matches.map((match, idx) => (
                  <p key={idx}>
                    Rider {match.rider_id} @ Station {match.station_id}
                  </p>
                ))}
              </div>
            )}

            {!driver.driver.is_simulating ? (
              <button onClick={startSimulation} className="btn btn-success">
                Start Simulation
              </button>
            ) : (
              <button onClick={stopSimulation} className="btn btn-danger">
                Stop Simulation
              </button>
            )}

            {driver.driver.route_queue?.length === 0 && !driver.driver.is_simulating && (
              <div className="info-section" style={{marginTop: '15px'}}>
                <h3>Route Completed</h3>
                <p style={{fontSize: '13px', marginBottom: '10px'}}>
                  Your route has been completed! The driver profile will be automatically removed.
                  Create a new driver profile to start a new route.
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="map-container">
        <MapContainer center={center} zoom={12} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <MapClickHandler onMapClick={handleMapClick} isDrawingRoute={isDrawingRoute} />

          {/* Draw route points */}
          {route.map((point, idx) => (
            <Marker key={`route-${idx}`} position={[point.lat, point.lng]}>
              <Popup>Waypoint {idx + 1}</Popup>
            </Marker>
          ))}

          {/* Draw route line */}
          {route.length > 1 && (
            <Polyline positions={route.map(p => [p.lat, p.lng])} color="blue" />
          )}

          {/* Show stations */}
          {stations.map((station) => (
            <Marker
              key={station.id}
              position={[station.latitude, station.longitude]}
              icon={stationIcon}
            >
              <Popup>
                <strong>{station.name}</strong><br />
                Metro Station
              </Popup>
            </Marker>
          ))}

          {/* Show driver current location */}
          {driver && (
            <Marker
              position={[driver.driver.current_lat, driver.driver.current_lng]}
              icon={driverIcon}
            >
              <Popup>
                <strong>Your Location</strong><br />
                Time: {driver.driver.sim_timestamp}
              </Popup>
            </Marker>
          )}
        </MapContainer>
      </div>
    </div>
  );
}

export default DriverDashboard;

