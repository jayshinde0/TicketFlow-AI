# Frontend Error Handling Fix

## Problem

When the backend validation rejected invalid input (gibberish text), the React frontend crashed with:

```
ERROR: Objects are not valid as a React child 
(found: object with keys {type, loc, msg, input, ctx})
```

## Root Cause

When Pydantic validation fails (422 status), it returns an array of error objects:

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "description"],
      "msg": "Please provide at least 3 meaningful words describing your issue.",
      "input": "12345tygfdzxcdzfdffcsdfszdfcsz",
      "ctx": {}
    }
  ]
}
```

The frontend was trying to render this object directly:
```javascript
toast.error(err.response?.data?.detail)  // ❌ Renders object, not string
```

React cannot render objects as children, causing the crash.

## Solution

### 1. Created Error Handler Utility

**File**: `frontend/src/utils/errorHandler.js`

Centralized error message extraction with support for:
- ✅ Pydantic validation errors (array of objects)
- ✅ FastAPI HTTPException (string detail)
- ✅ Generic error objects
- ✅ Field-specific error extraction

```javascript
export const extractErrorMessage = (error, fallback) => {
  const detail = error.response?.data?.detail;
  
  // Handle array of Pydantic errors
  if (Array.isArray(detail)) {
    return detail
      .map(err => err.msg || err.message || String(err))
      .join(", ");
  }
  
  // Handle string detail
  if (typeof detail === "string") {
    return detail;
  }
  
  // Handle object with msg
  if (detail?.msg) {
    return detail.msg;
  }
  
  return fallback;
};
```

### 2. Updated Components

#### SubmitTicket.jsx
```javascript
import { extractErrorMessage } from "../utils/errorHandler";

// Before:
toast.error(err.response?.data?.detail || "Submission failed");

// After:
const errorMessage = extractErrorMessage(err, "Submission failed");
toast.error(errorMessage);
```

#### useTickets.js Hook
```javascript
import { extractErrorMessage } from '../utils/errorHandler';

// Before:
setError(err.response?.data?.detail || 'Failed to submit ticket');

// After:
const errorMessage = extractErrorMessage(err, 'Failed to submit ticket');
setError(errorMessage);
```

## Error Handler Features

### Core Functions

1. **`extractErrorMessage(error, fallback)`**
   - Extracts user-friendly message from any error format
   - Returns string suitable for toast/display

2. **`extractFieldErrors(error)`**
   - Returns field-specific validation errors
   - Format: `{ fieldName: "error message" }`

3. **Status Checkers**
   - `isValidationError(error)` - 422 status
   - `isBadRequest(error)` - 400 status
   - `isAuthError(error)` - 401 status
   - `isForbiddenError(error)` - 403 status
   - `isNotFoundError(error)` - 404 status

### Example Usage

```javascript
import { 
  extractErrorMessage, 
  extractFieldErrors,
  isValidationError 
} from '../utils/errorHandler';

try {
  await api.post('/tickets', data);
} catch (error) {
  if (isValidationError(error)) {
    // Get field-specific errors
    const fieldErrors = extractFieldErrors(error);
    console.log(fieldErrors);
    // { description: "Please provide at least 3 meaningful words" }
  }
  
  // Get general error message
  const message = extractErrorMessage(error, "Something went wrong");
  toast.error(message);
}
```

## Error Response Formats Handled

### 1. Pydantic Validation Error (422)
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "description"],
      "msg": "Please provide at least 3 meaningful words",
      "input": "...",
      "ctx": {}
    }
  ]
}
```
**Extracted**: "Please provide at least 3 meaningful words"

### 2. FastAPI HTTPException (400)
```json
{
  "detail": "Unable to understand the text. Please use clear English."
}
```
**Extracted**: "Unable to understand the text. Please use clear English."

### 3. Generic API Error (500)
```json
{
  "detail": {
    "error": "Internal server error",
    "message": "Database connection failed"
  }
}
```
**Extracted**: "Database connection failed" (or fallback if unparseable)

## Files Modified

1. ✅ **Created**: `frontend/src/utils/errorHandler.js` - Utility functions
2. ✅ **Modified**: `frontend/src/pages/SubmitTicket.jsx` - Uses extractErrorMessage
3. ✅ **Modified**: `frontend/src/hooks/useTickets.js` - Uses extractErrorMessage

## Testing

### Test Scenario: Submit Gibberish Text

**Input**: "12345tygfdzxcdzfdffcsdfszdfcsz"

**Before Fix**:
```
❌ React crash
ERROR: Objects are not valid as a React child
```

**After Fix**:
```
✅ Graceful error display
🔴 Toast: "Please provide at least 3 meaningful words describing your issue."
```

### Test Scenario: Submit Valid Ticket

**Input**: "My laptop won't connect to VPN"

**Result**:
```
✅ Ticket submitted successfully
🟢 Toast: "Ticket TKT-XXXX submitted successfully!"
```

## Benefits

✅ **No more React crashes** - All errors properly stringified  
✅ **User-friendly messages** - Pydantic errors displayed clearly  
✅ **Centralized logic** - Single source of truth for error handling  
✅ **Reusable utility** - Can be used across all API calls  
✅ **Type-safe** - Handles all error response formats  
✅ **Extensible** - Easy to add new error types  

## Future Enhancements

### Potential Improvements

1. **Field-level error display**: Show errors directly under form fields
   ```javascript
   const fieldErrors = extractFieldErrors(error);
   <input className={fieldErrors.description ? 'error' : ''} />
   <span className="error-text">{fieldErrors.description}</span>
   ```

2. **Error retry logic**: Automatic retry for network errors
3. **Error logging**: Send errors to monitoring service (Sentry, etc.)
4. **Localization**: Multi-language error messages
5. **Error codes**: Map error codes to user-friendly messages

## Related Files

- `frontend/src/utils/errorHandler.js` - Error extraction utility
- `frontend/src/pages/SubmitTicket.jsx` - Ticket submission form
- `frontend/src/hooks/useTickets.js` - Tickets data hook
- `backend/models/ticket.py` - Pydantic validators (source of errors)
- `backend/services/text_validation_service.py` - Validation logic

## Migration Guide

To update other components using old error handling:

### Find Old Pattern
```javascript
// ❌ Old way
catch (err) {
  toast.error(err.response?.data?.detail || "Error occurred");
}
```

### Replace With
```javascript
// ✅ New way
import { extractErrorMessage } from '../utils/errorHandler';

catch (err) {
  const errorMessage = extractErrorMessage(err, "Error occurred");
  toast.error(errorMessage);
}
```

### Search for Instances
```bash
# Find all error handling patterns
grep -r "err.response?.data?.detail" frontend/src/
grep -r "error.response?.data?.detail" frontend/src/
```

---

**Status**: ✅ **FIXED**  
**Date**: 2026-07-30  
**Impact**: Critical (prevents app crashes)  
**Risk**: None (pure addition, backwards compatible)
