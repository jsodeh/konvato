/**
 * Form validation and data validation utilities for betslip conversion frontend.
 * 
 * This file provides:
 * - Form validation schemas and functions
 * - Data type validation utilities
 * - Input sanitization functions
 */

// Constants
const BOOKMAKER_IDS = {
  BET9JA: 'bet9ja',
  SPORTYBET: 'sportybet',
  BETWAY: 'betway',
  BET365: 'bet365'
};

const SELECTION_STATUS = {
  CONVERTED: 'converted',
  PARTIAL: 'partial',
  UNAVAILABLE: 'unavailable'
};

const API_ENDPOINTS = {
  CONVERT: '/api/convert',
  BOOKMAKERS: '/api/bookmakers'
};

// Validation Rules
const VALIDATION_RULES = {
  betslipCode: {
    required: true,
    minLength: 6,
    maxLength: 20,
    pattern: /^[A-Za-z0-9_-]+$/,
    custom: (value) => {
      if (!value || typeof value !== 'string') {
        return 'Betslip code is required';
      }
      const trimmed = value.trim();
      if (trimmed.length < 6) {
        return 'Betslip code must be at least 6 characters';
      }
      if (trimmed.length > 20) {
        return 'Betslip code must be no more than 20 characters';
      }
      if (!VALIDATION_RULES.betslipCode.pattern.test(trimmed)) {
        return 'Betslip code can only contain letters, numbers, hyphens, and underscores';
      }
      return null;
    }
  },
  sourceBookmaker: {
    required: true,
    custom: (value) => {
      if (!value || typeof value !== 'string') {
        return 'Source bookmaker is required';
      }
      if (!Object.values(BOOKMAKER_IDS).includes(value)) {
        return 'Please select a valid source bookmaker';
      }
      return null;
    }
  },
  destinationBookmaker: {
    required: true,
    custom: (value) => {
      if (!value || typeof value !== 'string') {
        return 'Destination bookmaker is required';
      }
      if (!Object.values(BOOKMAKER_IDS).includes(value)) {
        return 'Please select a valid destination bookmaker';
      }
      return null;
    }
  }
};

/**
 * Validate a single form field
 * @param {string} fieldName - Name of the field to validate
 * @param {string} value - Value to validate
 * @param {Object} allValues - All form values for cross-field validation
 * @returns {string|null} Error message or null if valid
 */
function validateField(fieldName, value, allValues = {}) {
  const rule = VALIDATION_RULES[fieldName];
  if (!rule) {
    return null;
  }

  // Required validation
  if (rule.required && (!value || value.trim() === '')) {
    return `${fieldName.charAt(0).toUpperCase() + fieldName.slice(1)} is required`;
  }

  // Skip other validations if field is empty and not required
  if (!value || value.trim() === '') {
    return null;
  }

  // Length validations
  if (rule.minLength && value.length < rule.minLength) {
    return `${fieldName} must be at least ${rule.minLength} characters`;
  }

  if (rule.maxLength && value.length > rule.maxLength) {
    return `${fieldName} must be no more than ${rule.maxLength} characters`;
  }

  // Pattern validation
  if (rule.pattern && !rule.pattern.test(value)) {
    return `${fieldName} format is invalid`;
  }

  // Custom validation
  if (rule.custom) {
    const customError = rule.custom(value, allValues);
    if (customError) {
      return customError;
    }
  }

  return null;
}

/**
 * Validate the entire conversion form
 * @param {Object} formData - Form data to validate
 * @param {string} formData.betslipCode - Betslip code
 * @param {string} formData.sourceBookmaker - Source bookmaker ID
 * @param {string} formData.destinationBookmaker - Destination bookmaker ID
 * @returns {Object} Validation result with isValid flag and errors object
 */
function validateConversionForm(formData) {
  const errors = {};
  let isValid = true;

  // Validate individual fields
  Object.keys(VALIDATION_RULES).forEach(fieldName => {
    const error = validateField(fieldName, formData[fieldName], formData);
    if (error) {
      errors[fieldName] = error;
      isValid = false;
    }
  });

  // Cross-field validation
  if (formData.sourceBookmaker && formData.destinationBookmaker) {
    if (formData.sourceBookmaker === formData.destinationBookmaker) {
      errors.general = 'Source and destination bookmakers must be different';
      isValid = false;
    }
  }

  return {
    isValid,
    errors
  };
}

/**
 * Sanitize input string
 * @param {string} input - Input string to sanitize
 * @returns {string} Sanitized string
 */
function sanitizeInput(input) {
  if (typeof input !== 'string') {
    return '';
  }
  
  return input
    .trim()
    .replace(/[<>\"'&]/g, '') // Remove potentially dangerous characters
    .substring(0, 1000); // Limit length
}

/**
 * Validate API response structure
 * @param {any} response - Response to validate
 * @returns {boolean} True if valid ConversionResponse
 */
function isValidConversionResponse(response) {
  return (
    typeof response === 'object' &&
    response !== null &&
    typeof response.success === 'boolean' &&
    Array.isArray(response.selections) &&
    Array.isArray(response.warnings) &&
    typeof response.processingTime === 'number'
  );
}

/**
 * Validate selection object structure
 * @param {any} selection - Selection to validate
 * @returns {boolean} True if valid Selection
 */
function isValidSelection(selection) {
  return (
    typeof selection === 'object' &&
    selection !== null &&
    typeof selection.game === 'string' &&
    typeof selection.market === 'string' &&
    typeof selection.odds === 'number' &&
    typeof selection.originalOdds === 'number' &&
    Object.values(SELECTION_STATUS).includes(selection.status)
  );
}

/**
 * Validate bookmaker object structure
 * @param {any} bookmaker - Bookmaker to validate
 * @returns {boolean} True if valid Bookmaker
 */
function isValidBookmaker(bookmaker) {
  return (
    typeof bookmaker === 'object' &&
    bookmaker !== null &&
    typeof bookmaker.id === 'string' &&
    typeof bookmaker.name === 'string' &&
    typeof bookmaker.baseUrl === 'string' &&
    typeof bookmaker.supported === 'boolean'
  );
}

/**
 * Validate betslip code format
 * @param {string} betslipCode - Betslip code to validate
 * @returns {boolean} True if valid format
 */
function isValidBetslipCode(betslipCode) {
  if (typeof betslipCode !== 'string') {
    return false;
  }
  
  const trimmed = betslipCode.trim();
  return (
    trimmed.length >= 6 &&
    trimmed.length <= 20 &&
    /^[A-Za-z0-9_-]+$/.test(trimmed)
  );
}

/**
 * Format error message for display
 * @param {string|Object} error - Error to format
 * @returns {string} Formatted error message
 */
function formatErrorMessage(error) {
  if (typeof error === 'string') {
    return error;
  }
  
  if (error && error.message) {
    return error.message;
  }
  
  if (error && error.response && error.response.data && error.response.data.message) {
    return error.response.data.message;
  }
  
  return 'An unexpected error occurred. Please try again.';
}

/**
 * Create initial form state
 * @returns {Object} Initial form state
 */
function createInitialFormState() {
  return {
    betslipCode: '',
    sourceBookmaker: '',
    destinationBookmaker: '',
    result: null,
    loading: false,
    error: null,
    bookmakers: [],
    bookmarkersLoading: false
  };
}

/**
 * Create validation errors object
 * @returns {Object} Empty validation errors object
 */
function createValidationErrors() {
  return {
    betslipCode: null,
    sourceBookmaker: null,
    destinationBookmaker: null,
    general: null
  };
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    BOOKMAKER_IDS,
    SELECTION_STATUS,
    API_ENDPOINTS,
    VALIDATION_RULES,
    validateField,
    validateConversionForm,
    sanitizeInput,
    isValidConversionResponse,
    isValidSelection,
    isValidBookmaker,
    isValidBetslipCode,
    formatErrorMessage,
    createInitialFormState,
    createValidationErrors
  };
}

// Make available globally for CDN usage
if (typeof window !== 'undefined') {
  window.BetslipValidation = {
    BOOKMAKER_IDS,
    SELECTION_STATUS,
    API_ENDPOINTS,
    VALIDATION_RULES,
    validateField,
    validateConversionForm,
    sanitizeInput,
    isValidConversionResponse,
    isValidSelection,
    isValidBookmaker,
    isValidBetslipCode,
    formatErrorMessage,
    createInitialFormState,
    createValidationErrors
  };
}