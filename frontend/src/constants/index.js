// API Endpoints
export const API_ENDPOINTS = {
  HEALTH: '/health',
  // Add more endpoints as needed
  // AUTH: '/auth',
  // ITEMS: '/items',
};

// App Constants
export const APP_NAME = import.meta.env.VITE_APP_NAME || 'Reclaim';

// Status Codes
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  SERVER_ERROR: 500,
};

