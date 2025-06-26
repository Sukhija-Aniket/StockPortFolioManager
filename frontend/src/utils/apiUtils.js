import axios from 'axios';

const REACT_APP_BACKEND_SERVICE = process.env.REACT_APP_BACKEND_SERVICE;

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: `http://${REACT_APP_BACKEND_SERVICE}`,
  withCredentials: true,
  timeout: 30000, // 30 seconds timeout
});

// Response interceptor to handle 401 errors globally
apiClient.interceptors.response.use(
  (response) => {
    // Return successful responses as-is
    return response;
  },
  (error) => {
    // Handle 401 errors (authentication required)
    if (error.response && error.response.status === 401 && error.response.data.message === 'Authentication required') {
      console.warn('Authentication required - token expired');
      
      // Clear any stored user data
      localStorage.clear();
      sessionStorage.clear();
      
      // Redirect to login page
      window.location.reload();
      
      // Return a rejected promise to prevent further processing
      return Promise.reject(new Error('Authentication required'));
    }
    
    // For other errors, just pass them through
    return Promise.reject(error);
  }
);

// Helper function to make API calls with automatic 401 handling
export const apiCall = async (method, endpoint, data = null, config = {}) => {
  try {
    const response = await apiClient.request({
      method,
      url: endpoint,
      data,
      ...config
    });
    return response.data;
  } catch (error) {
    // If it's a 401 error, it's already handled by the interceptor
    if (error.message === 'Authentication required') {
      throw error;
    }
    
    // For other errors, re-throw with more context
    console.error(`API call failed (${method} ${endpoint}):`, error);
    throw error;
  }
};

// Convenience methods for common HTTP methods
export const apiGet = (endpoint, config = {}) => apiCall('GET', endpoint, null, config);
export const apiPost = (endpoint, data = null, config = {}) => apiCall('POST', endpoint, data, config);
export const apiPut = (endpoint, data = null, config = {}) => apiCall('PUT', endpoint, data, config);
export const apiDelete = (endpoint, config = {}) => apiCall('DELETE', endpoint, null, config);

// Export the axios instance for direct use if needed
export { apiClient }; 