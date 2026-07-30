/**
 * utils/errorHandler.js — Centralized error message extraction
 * 
 * Handles different error response formats:
 * - Pydantic validation errors (array of objects with {type, loc, msg, input, ctx})
 * - FastAPI HTTPException (string detail)
 * - Generic error objects
 */

/**
 * Extract a user-friendly error message from an API error response
 * @param {Error} error - The error object from axios/fetch
 * @param {string} fallback - Default message if extraction fails
 * @returns {string} User-friendly error message
 */
export const extractErrorMessage = (error, fallback = "An error occurred") => {
  if (!error) return fallback;

  // Try to get the detail from response
  const detail = error.response?.data?.detail;

  if (!detail) {
    // Check for generic error message
    return error.message || fallback;
  }

  // Handle array of Pydantic validation errors
  if (Array.isArray(detail)) {
    return detail
      .map(err => {
        // Extract the most useful information
        if (err.msg) return err.msg;
        if (err.message) return err.message;
        return String(err);
      })
      .filter(Boolean)
      .join(", ");
  }

  // Handle string detail (FastAPI HTTPException)
  if (typeof detail === "string") {
    return detail;
  }

  // Handle object with msg property
  if (detail && typeof detail === "object") {
    if (detail.msg) return detail.msg;
    if (detail.message) return detail.message;
    
    // Try to stringify if it's a simple object
    try {
      const str = JSON.stringify(detail);
      // Only return stringified version if it's not too long
      if (str.length < 200) return str;
    } catch (e) {
      // Ignore stringify errors
    }
  }

  return fallback;
};

/**
 * Extract field-specific validation errors from Pydantic response
 * @param {Error} error - The error object from axios/fetch
 * @returns {Object} Object mapping field names to error messages
 */
export const extractFieldErrors = (error) => {
  const detail = error.response?.data?.detail;
  const fieldErrors = {};

  if (!Array.isArray(detail)) {
    return fieldErrors;
  }

  detail.forEach(err => {
    // loc is an array like ["body", "description"] or ["query", "page"]
    if (err.loc && Array.isArray(err.loc) && err.loc.length > 0) {
      // Get the field name (last item in loc)
      const fieldName = err.loc[err.loc.length - 1];
      const message = err.msg || err.message || "Invalid value";
      
      if (!fieldErrors[fieldName]) {
        fieldErrors[fieldName] = [];
      }
      fieldErrors[fieldName].push(message);
    }
  });

  // Flatten arrays with single items
  Object.keys(fieldErrors).forEach(key => {
    if (fieldErrors[key].length === 1) {
      fieldErrors[key] = fieldErrors[key][0];
    }
  });

  return fieldErrors;
};

/**
 * Check if error is a validation error
 * @param {Error} error - The error object
 * @returns {boolean} True if it's a validation error (422 status)
 */
export const isValidationError = (error) => {
  return error.response?.status === 422;
};

/**
 * Check if error is a bad request
 * @param {Error} error - The error object
 * @returns {boolean} True if it's a bad request (400 status)
 */
export const isBadRequest = (error) => {
  return error.response?.status === 400;
};

/**
 * Check if error is authentication related
 * @param {Error} error - The error object
 * @returns {boolean} True if it's an auth error (401 status)
 */
export const isAuthError = (error) => {
  return error.response?.status === 401;
};

/**
 * Check if error is authorization related
 * @param {Error} error - The error object
 * @returns {boolean} True if it's a forbidden error (403 status)
 */
export const isForbiddenError = (error) => {
  return error.response?.status === 403;
};

/**
 * Check if error is a not found error
 * @param {Error} error - The error object
 * @returns {boolean} True if resource not found (404 status)
 */
export const isNotFoundError = (error) => {
  return error.response?.status === 404;
};
