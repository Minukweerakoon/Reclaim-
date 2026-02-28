# Error Handling Implementation Guide

## Files Created

1. **src/utils/exceptions.py** - Custom exception classes
   - `FileFormatError`, `FileSizeError`, `ModelLoadError`
   - `APIRateLimitError`, `NetworkError`, `DatabaseError`
   - `ImageValidationError`, `TextValidationError`, `VoiceValidationError`
   - User-friendly error messages dictionary

2. **src/utils/error_handler.py** - Error response helpers
   - `create_error_response()` - Standardized JSON error format
   - `handle_validation_error()` - Maps exceptions to HTTP responses
   - `validate_file_upload()` - Reusable file validation

## Implementation Pattern

### Backend Pattern (app.py endpoints):

```python
from src.utils.exceptions import FileFormatError, FileSizeError
from src.utils.error_handler import handle_validation_error, validate_file_upload

@app.post("/validate/image")
async def validate_image(image_file: UploadFile, ...):
    try:
        # Validate file
        validate_file_upload(image_file, ALLOWED_IMAGE_TYPES, max_size_mb=10)
        
        # Process validation
        result = await process_validation(image_file)
        
        return result
        
    except (FileFormatError, FileSizeError) as e:
        return handle_validation_error(e, context="image validation")
    except ModelLoadError as e:
        return handle_validation_error(e, context="image validation")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return create_error_response(
            status_code=500,
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred"
        )
```

### Frontend Pattern (useValidation.ts):

```typescript
// Enhanced error parsing
const parseError = (error: any): string => {
  if (error.response?.data?.error) {
    const apiError = error.response.data.error;
    
    switch (apiError.code) {
      case 'FILE_FORMAT_ERROR':
        return 'Invalid file format. Please upload JPEG, PNG, or WebP images.';
      case 'FILE_SIZE_ERROR':
        return `File too large. Maximum size is ${apiError.details?.max_size_mb || 10}MB.`;
      case 'NO_OBJECTS_DETECTED':
        return 'No clear objects detected. Try better lighting and positioning.';
      case 'RATE_LIMIT_ERROR':
        return `Too many requests. Please wait ${apiError.details?.retry_after || 60} seconds.`;
      default:
        return apiError.message || 'An error occurred';
    }
  }
  
  if (error.code === 'ECONNABORTED') {
    return 'Upload timeout. Please check your connection.';
  }
  
  if (error.response?.status === 413) {
    return 'File too large. Maximum size is 10MB.';
  }
  
  return 'Something went wrong. Please try again.';
};

// Usage in validateImage
const validateImage = async (file: File, text?: string) => {
  try {
    const formData = new FormData();
    formData.append('image_file', file);
    if (text) formData.append('text', text);
    
    const result = await axios.post('/validate/image', formData);
    return result.data;
    
  } catch (error) {
    const userMessage = parseError(error);
    return { error: userMessage };
  }
};
```

## Next Steps to Complete

### High Priority:
1. Wrap `/validate/image` endpoint (currently has basic error handling)
2. Wrap `/validate/voice` endpoint
3. Wrap `/validate/text` endpoint
4. Wrap `/validate/complete` endpoint

### Medium Priority:
5. Update frontend `useValidation.ts` with parseError function
6. Add error display component in frontend
7. Test all error scenarios

### Testing Checklist:
- [ ] Invalid file format (upload .txt file)
- [ ] File too large (upload 20MB image)
- [ ] No objects detected (upload blank image)
- [ ] Network timeout simulation
- [ ] Model loading failure
- [ ] Database connection failure

## Status

**Created:** Core error handling infrastructure ✅
**Remaining:** Apply pattern to all 4 endpoints + frontend

*Estimated time to complete: 1.5 hours*
