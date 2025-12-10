import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import { riderAPI, stationAPI, matchingAPI } from '../../services/api';
import '../../App.css';

// Fix for default marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

const stationIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

const destinationIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

function MapClickHandler({ onMapClick, isSelectingDestination }) {
  useMapEvents({
    click: (e) => {
      if (isSelectingDestination) {
        onMapClick(e.latlng);
      }
    },
  });
  return null;
}

function RiderDashboard({ user, onLogout }) {
  const [stations, setStations] = useState([]);
  const [selectedStation, setSelectedStation] = useState('');
  const [eta, setEta] = useState('10:00');
  const [destination, setDestination] = useState(null);
  const [isSelectingDestination, setIsSelectingDestination] = useState(false);
  const [rideRequests, setRideRequests] = useState([]);
  const [matches, setMatches] = useState([]);
  const [error, setError] = useState('');

  const center = [12.9716, 77.5946];

  useEffect(() => {
    loadStations();
    loadRideRequests();
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      loadRideRequests();
      loadMatches();
    }, 3000);
    return () => clearInterval(interval);
  }, []);

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

  const loadRideRequests = async () => {
    try {
      const response = await riderAPI.getRidesByRider(user.userId);
      if (response.data.success) {
        setRideRequests(response.data.rides);
      }
    } catch (err) {
      console.error('Failed to load ride requests:', err);
    }
  };

  const loadMatches = async () => {
    try {
      const response = await matchingAPI.getMatchesByRider(user.userId);
      if (response.data.success) {
        setMatches(response.data.matches);
      }
    } catch (err) {
      console.error('Failed to load matches:', err);
    }
  };

  const handleMapClick = (latlng) => {
    setDestination({ lat: latlng.lat, lng: latlng.lng });
    setIsSelectingDestination(false);
  };

  const createRideRequest = async () => {
    if (!selectedStation) {
      setError('Please select a metro station');
      return;
    }
    if (!destination) {
      setError('Please select a destination on the map');
      return;
    }
    if (!eta) {
      setError('Please enter your ETA');
      return;
    }

    try {
      const response = await riderAPI.createRideRequest(
        user.userId,
        parseInt(selectedStation),
        eta,
        destination.lat,
        destination.lng
      );

      if (response.data.success) {
        setError('');
        loadRideRequests();
        // Reset form
        setSelectedStation('');
        setDestination(null);
        setEta('10:00');
      } else {
        setError(response.data.message);
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to create ride request');
    }
  };

  const getStationName = (stationId) => {
    const station = stations.find(s => s.id === stationId);
    return station ? station.name : `Station ${stationId}`;
  };

  const cancelRideRequest = async (rideId) => {
    try {
      await riderAPI.deleteRideRequest(rideId);
      setError('');
      loadRideRequests();
    } catch (err) {
      setError('Failed to cancel ride request');
    }
  };

  return (
    <div className="dashboard">
      <div className="sidebar">
        <div className="sidebar-header">
          <h2>Rider Dashboard</h2>
          <button onClick={onLogout} className="logout-btn">Logout</button>
        </div>

        <div className="user-info">
          <p><strong>Username:</strong> {user.username}</p>
          <p><strong>Role:</strong> {user.role}</p>
        </div>

        <div className="instructions">
          <h3>Request a Ride</h3>
          <p>1. Select your target metro station</p>
          <p>2. Set your arrival time (ETA)</p>
          <p>3. Click destination on map</p>
          <p>4. Submit request</p>
        </div>

        <div className="form-group">
          <label>Target Metro Station</label>
          <select
            value={selectedStation}
            onChange={(e) => setSelectedStation(e.target.value)}
          >
            <option value="">Select Station</option>
            {stations.map(station => (
              <option key={station.id} value={station.id}>
                {station.name}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Your ETA (HH:MM)</label>
          <input
            type="time"
            value={eta}
            onChange={(e) => setEta(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>Destination</label>
          {!destination ? (
            <button
              onClick={() => setIsSelectingDestination(true)}
              className="btn btn-primary"
            >
              {isSelectingDestination ? 'Click on Map...' : 'Select on Map'}
            </button>
          ) : (
            <div>
              <p style={{fontSize: '12px', marginBottom: '5px'}}>
                ({destination.lat.toFixed(4)}, {destination.lng.toFixed(4)})
              </p>
              <button
                onClick={() => setDestination(null)}
                className="btn btn-danger"
                style={{padding: '6px 12px', fontSize: '12px'}}
              >
                Clear
              </button>
            </div>
          )}
        </div>

        <button
          onClick={createRideRequest}
          className="btn btn-success"
          disabled={!selectedStation || !destination}
        >
          Request Ride
        </button>

        {error && <div style={{color: '#ff6b6b', marginTop: '10px', fontSize: '13px'}}>{error}</div>}

        {rideRequests.length > 0 && (
          <div className="status-card">
            <h3>My Ride Requests ({rideRequests.length})</h3>
            {rideRequests.map((ride, idx) => (
              <div key={idx} style={{
                marginBottom: '15px', 
                padding: '10px',
                background: 'rgba(255,255,255,0.05)',
                borderRadius: '5px'
              }}>
                <p><strong>Station:</strong> {getStationName(ride.station_id)}</p>
                <p><strong>ETA:</strong> {ride.eta}</p>
                <p><strong>Status:</strong> {ride.status}</p>
                {ride.status === 'LOOKING' && (
                  <button
                    onClick={() => cancelRideRequest(ride.id)}
                    className="btn btn-danger"
                    style={{
                      padding: '5px 10px',
                      fontSize: '12px',
                      marginTop: '8px',
                      width: 'auto'
                    }}
                  >
                    Cancel Request
                  </button>
                )}
              </div>
            ))}
          </div>
        )}

        {matches.length > 0 && (
          <div className="status-card">
            <h3>✓ Matched! ({matches.length})</h3>
            {matches.map((match, idx) => (
              <div key={idx} style={{marginBottom: '10px'}}>
                <p><strong>Driver ID:</strong> {match.driver_id}</p>
                <p><strong>Station:</strong> {getStationName(match.station_id)}</p>
                <p><strong>Time:</strong> {match.match_timestamp}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="map-container">
        <MapContainer center={center} zoom={12} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <MapClickHandler 
            onMapClick={handleMapClick} 
            isSelectingDestination={isSelectingDestination} 
          />

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

          {/* Show selected destination */}
          {destination && (
            <Marker
              position={[destination.lat, destination.lng]}
              icon={destinationIcon}
            >
              <Popup>
                <strong>Your Destination</strong>
              </Popup>
            </Marker>
          )}
        </MapContainer>
      </div>
    </div>
  );
}

export default RiderDashboard;

