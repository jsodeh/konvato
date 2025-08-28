/**
 * Configuration file for API endpoints and environment variables
 */

// Helper function to detect environment
const getEnvironment = () => {
  const hostname = window.location.hostname;
  
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'development';
  } else if (hostname.includes('onrender.com')) {
    return 'production';
  } else {
    return 'unknown';
  }
};

// Helper function to get API base URL
const getApiBaseUrl = () => {
  const env = getEnvironment();
  
  switch (env) {
    case 'development':
      return 'http://localhost:5000';
    case 'production':
      return 'https://konvato-server.onrender.com';
    default:
      // Fallback: try to infer from current hostname
      if (window.location.hostname.includes('konvato-client')) {
        return 'https://konvato-server.onrender.com';
      }
      return 'http://localhost:5000'; // Ultimate fallback
  }
};

// Configuration object
window.Config = {
  // API base URL - dynamically determined
  API_BASE_URL: getApiBaseUrl(),
  
  // Environment detection
  environment: getEnvironment(),
  isDevelopment: getEnvironment() === 'development',
  isProduction: getEnvironment() === 'production',
  
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