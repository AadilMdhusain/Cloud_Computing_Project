import axios from 'axios';

// API Base URLs - Update these based on your deployment
const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost';

const API_URLS = {
  USER: `${API_BASE}:8001/api`,
  STATION: `${API_BASE}:8002/api`,
  RIDER: `${API_BASE}:8003/api`,
  DRIVER: `${API_BASE}:8004/api`,
  MATCHING: `${API_BASE}:8005/api`,
};

// User Service APIs
export const userAPI = {
  login: (username, password) => 
    axios.post(`${API_URLS.USER}/users/login/`, { username, password }),
  
  register: (username, email, password, role) =>
    axios.post(`${API_URLS.USER}/users/`, { username, email, password, role }),
  
  getUser: (userId) =>
    axios.get(`${API_URLS.USER}/users/${userId}/`),
};

// Station Service APIs
export const stationAPI = {
  listStations: () =>
    axios.get(`${API_URLS.STATION}/stations/`),
  
  createStation: (name, latitude, longitude) =>
    axios.post(`${API_URLS.STATION}/stations/`, { name, latitude, longitude }),
  
  getStation: (stationId) =>
    axios.get(`${API_URLS.STATION}/stations/${stationId}/`),
};

// Rider Service APIs
export const riderAPI = {
  createRideRequest: (riderId, stationId, eta, destinationLat, destinationLng) =>
    axios.post(`${API_URLS.RIDER}/rides/`, {
      rider_id: riderId,
      station_id: stationId,
      eta: eta,
      destination_lat: destinationLat,
      destination_lng: destinationLng,
    }),
  
  getRidesByRider: (riderId) =>
    axios.get(`${API_URLS.RIDER}/rides/by_rider/?rider_id=${riderId}`),
  
  getRidesByStation: (stationId, status = 'LOOKING') =>
    axios.get(`${API_URLS.RIDER}/rides/by_station/?station_id=${stationId}&status=${status}`),
  
  deleteRideRequest: (rideId) =>
    axios.delete(`${API_URLS.RIDER}/rides/${rideId}/`),
};

// Driver Service APIs
export const driverAPI = {
  createDriver: (userId, freeSeats, route) =>
    axios.post(`${API_URLS.DRIVER}/drivers/`, {
      user_id: userId,
      free_seats: freeSeats,
      route: route,
    }),
  
  getDriver: (driverId) =>
    axios.get(`${API_URLS.DRIVER}/drivers/${driverId}/`),
  
  getDriverByUser: (userId) =>
    axios.get(`${API_URLS.DRIVER}/drivers/by_user/?user_id=${userId}`),
  
  startSimulation: (driverId) =>
    axios.post(`${API_URLS.DRIVER}/drivers/${driverId}/start_simulation/`),
  
  stopSimulation: (driverId) =>
    axios.post(`${API_URLS.DRIVER}/drivers/${driverId}/stop_simulation/`),
  
  getActiveDrivers: () =>
    axios.get(`${API_URLS.DRIVER}/drivers/active_drivers/`),
  
  deleteDriver: (driverId) =>
    axios.delete(`${API_URLS.DRIVER}/drivers/${driverId}/`),
};

// Matching Service APIs
export const matchingAPI = {
  getMatchesByRider: (riderId) =>
    axios.get(`${API_URLS.MATCHING}/matches/by_rider/?rider_id=${riderId}`),
  
  getMatchesByDriver: (driverId) =>
    axios.get(`${API_URLS.MATCHING}/matches/by_driver/?driver_id=${driverId}`),
};

export default {
  userAPI,
  stationAPI,
  riderAPI,
  driverAPI,
  matchingAPI,
};

