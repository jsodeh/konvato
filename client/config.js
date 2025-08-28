/**
 * Configuration file for API endpoints and environment variables
 */

// Configuration object
window.Config = {
  // API base URL - will be set during build time
  API_BASE_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? 'http://localhost:5000'  // Local development
    : 'https://konvato-server.onrender.com',  // Production - backend service URL
  
  // Environment detection
  isDevelopment: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1',
  isProduction: window.location.hostname.includes('onrender.com'),
  
  // API endpoints
  endpoints: {
    convert: '/api/convert',
    bookmakers: '/api/bookmakers',
    health: '/health',
    compliance: '/api/compliance/disclaimers'
  },
  
  // Get full API URL
  getApiUrl: function(endpoint) {
    return this.API_BASE_URL + endpoint;
  }
};

// Log configuration in development
if (window.Config.isDevelopment) {
  console.log('App Configuration:', window.Config);
}