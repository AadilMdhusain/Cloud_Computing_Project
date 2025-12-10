import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import { stationAPI, driverAPI } from '../../services/api';
import '../../App.css';

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

const driverIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

function MapClickHandler({ onMapClick, isAddingStation }) {
  useMapEvents({
    click: (e) => {
      if (isAddingStation) {
        onMapClick(e.latlng);
      }
    },
  });
  return null;
}

function AdminDashboard({ onLogout }) {
  const [stations, setStations] = useState([]);
  const [activeDrivers, setActiveDrivers] = useState([]);
  const [isAddingStation, setIsAddingStation] = useState(false);
  const [newStation, setNewStation] = useState(null);
  const [stationName, setStationName] = useState('');
  const [error, setError] = useState('');

  const center = [12.9716, 77.5946];

  useEffect(() => {
    loadStations();
    loadActiveDrivers();
    
    const interval = setInterval(() => {
      loadActiveDrivers();
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

  const loadActiveDrivers = async () => {
    try {
      const response = await driverAPI.getActiveDrivers();
      if (response.data.success) {
        setActiveDrivers(response.data.drivers);
      }
    } catch (err) {
      console.error('Failed to load active drivers:', err);
    }
  };

  const handleMapClick = (latlng) => {
    setNewStation({ lat: latlng.lat, lng: latlng.lng });
  };

  const createStation = async () => {
    if (!stationName || !newStation) {
      setError('Please enter station name and click on map');
      return;
    }

    try {
      const response = await stationAPI.createStation(
        stationName,
        newStation.lat,
        newStation.lng
      );

      if (response.data.success) {
        setError('');
        setStationName('');
        setNewStation(null);
        setIsAddingStation(false);
        loadStations();
      } else {
        setError(response.data.message);
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to create station');
    }
  };

  return (
    <div className="dashboard">
      <div className="sidebar">
        <div className="sidebar-header">
          <h2>Admin Dashboard</h2>
          <button onClick={onLogout} className="logout-btn">Logout</button>
        </div>

        <div className="instructions">
          <h3>Add Metro Station</h3>
          <p>1. Enter station name</p>
          <p>2. Click "Add Station"</p>
          <p>3. Click on map to place station</p>
          <p>4. Click "Create Station"</p>
        </div>

        <div className="form-group">
          <label>Station Name</label>
          <input
            type="text"
            value={stationName}
            onChange={(e) => setStationName(e.target.value)}
            placeholder="e.g., Koramangala Metro"
          />
        </div>

        {!isAddingStation ? (
          <button
            onClick={() => setIsAddingStation(true)}
            className="btn btn-primary"
          >
            Add Station
          </button>
        ) : (
          <>
            {newStation && (
              <div style={{marginBottom: '10px', fontSize: '12px'}}>
                <p>Location: ({newStation.lat.toFixed(4)}, {newStation.lng.toFixed(4)})</p>
              </div>
            )}
            <button
              onClick={createStation}
              className="btn btn-success"
              disabled={!stationName || !newStation}
            >
              Create Station
            </button>
            <button
              onClick={() => {
                setIsAddingStation(false);
                setNewStation(null);
              }}
              className="btn btn-danger"
            >
              Cancel
            </button>
          </>
        )}

        {error && <div style={{color: '#ff6b6b', marginTop: '10px', fontSize: '13px'}}>{error}</div>}

        <div className="status-card">
          <h3>Stations ({stations.length})</h3>
          <div style={{maxHeight: '150px', overflowY: 'auto'}}>
            {stations.map((station, idx) => (
              <p key={idx} style={{fontSize: '12px', marginBottom: '5px'}}>
                {station.name}
              </p>
            ))}
          </div>
        </div>

        <div className="status-card">
          <h3>Active Drivers ({activeDrivers.length})</h3>
          {activeDrivers.map((driver, idx) => (
            <div key={idx} style={{marginBottom: '10px', fontSize: '12px'}}>
              <p><strong>Driver {driver.user_id}</strong></p>
              <p>Time: {driver.sim_timestamp}</p>
              <p>Queue: {driver.route_queue?.length || 0} waypoints</p>
            </div>
          ))}
        </div>
      </div>

      <div className="map-container">
        <MapContainer center={center} zoom={12} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <MapClickHandler 
            onMapClick={handleMapClick} 
            isAddingStation={isAddingStation} 
          />

          {/* Show existing stations */}
          {stations.map((station) => (
            <Marker
              key={station.id}
              position={[station.latitude, station.longitude]}
              icon={stationIcon}
            >
              <Popup>
                <strong>{station.name}</strong><br />
                ID: {station.id}
              </Popup>
            </Marker>
          ))}

          {/* Show new station being created */}
          {newStation && (
            <Marker position={[newStation.lat, newStation.lng]}>
              <Popup>
                <strong>{stationName || 'New Station'}</strong>
              </Popup>
            </Marker>
          )}

          {/* Show active drivers */}
          {activeDrivers.map((driver) => (
            <Marker
              key={driver.id}
              position={[driver.current_lat, driver.current_lng]}
              icon={driverIcon}
            >
              <Popup>
                <strong>Driver {driver.user_id}</strong><br />
                Time: {driver.sim_timestamp}<br />
                Seats: {driver.free_seats}
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}

export default AdminDashboard;

