# Code Review Report: Room Booking Application

**Date:** February 11, 2026  
**Reviewer:** AI Code Reviewer  
**Project:** VillaEase Room Booking Platform

---

## Executive Summary

This comprehensive review covers both the **Django backend** and **TypeScript frontend** (api.ts) of the room booking application. The review identifies critical security vulnerabilities, architectural inconsistencies, and opportunities for improvement.

### Overall Assessment
- **Backend Quality:** ⚠️ **Needs Improvement** (6/10)
- **Frontend Quality:** ⚠️ **Needs Improvement** (5/10)
- **Security:** 🔴 **Critical Issues Found**
- **API Consistency:** ⚠️ **Multiple Inconsistencies**

---

## 🔴 Critical Issues (Must Fix)

### 1. **Hardcoded SECRET_KEY in Production**
**File:** `bookings/settings.py:28`  
**Severity:** 🔴 CRITICAL

```python
SECRET_KEY = 'django-insecure-1t0&p%7&-m$7jp^*7%r!p%hq9ub8t46)e(zohu4o$s$n2vxt!i'
```

**Issue:** The Django SECRET_KEY is hardcoded and marked as "insecure". This key is used for cryptographic signing and should NEVER be committed to version control.

**Impact:** 
- Session hijacking
- CSRF token forgery
- Password reset token manipulation

**Fix:**
```python
SECRET_KEY = env('SECRET_KEY', default='fallback-key-for-dev')
```

---

### 2. **DEBUG Mode Enabled in Production Settings**
**File:** `bookings/settings.py:31`  
**Severity:** 🔴 CRITICAL

```python
DEBUG = True
```

**Issue:** Debug mode exposes sensitive information in error pages including:
- Full stack traces
- Environment variables
- Database queries
- File paths

**Fix:**
```python
DEBUG = env.bool('DEBUG', default=False)
```

---

### 3. **ALLOWED_HOSTS Set to ["*"]**
**File:** `bookings/settings.py:33`  
**Severity:** 🔴 CRITICAL

```python
ALLOWED_HOSTS = ["*"]
```

**Issue:** Allows HTTP Host Header attacks, potentially leading to:
- Password reset poisoning
- Cache poisoning
- Web cache deception

**Fix:**
```python
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])
```

---

### 4. **CORS_ALLOW_ALL_ORIGINS = True**
**File:** `bookings/settings.py:89`  
**Severity:** 🔴 CRITICAL

```python
CORS_ALLOW_ALL_ORIGINS = True
```

**Issue:** Allows any website to make requests to your API, making CSRF protection ineffective.

**Fix:**
```python
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'http://localhost:3000',
    'https://room-booking-pjo6.onrender.com'
])
```

---

### 5. **Inconsistent Authentication Methods**
**Files:** Multiple  
**Severity:** 🔴 CRITICAL

The application uses THREE different authentication methods simultaneously:

1. **JWT Authentication** (`rest_framework_simplejwt`)
   - Settings configured for JWT
   - `CustomTokenObtainPairSerializer` defined

2. **Token Authentication** (`rest_framework.authtoken`)
   - Login endpoint uses `obtain_auth_token`
   - Logout deletes `auth_token`

3. **Mixed Frontend Expectations**
   - `api.ts` expects both `token` and `access/refresh` tokens
   - Inconsistent storage keys

**Example from `accounts/urls.py`:**
```python
path('login/', obtain_auth_token, name='login'),  # Token Auth
```

**Example from `accounts/serializers.py`:**
```python
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):  # JWT Auth
```

**Impact:**
- Authentication will fail unpredictably
- Frontend cannot reliably authenticate
- Security vulnerabilities due to confusion

**Fix:** Choose ONE authentication method (recommend JWT) and implement consistently.

---

### 6. **Missing User Association in Bookings**
**File:** `bookings_app/models.py`  
**Severity:** 🔴 CRITICAL

```python
class Booking(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')
    # NO USER FIELD!
```

**Issue:** Bookings are not associated with users, meaning:
- Anyone can view/modify any booking
- No user booking history
- Cannot enforce user-specific permissions
- Violates data privacy principles

**Fix:**
```python
from django.contrib.auth.models import User

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings', null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')
    # ... rest of fields
```

---

### 7. **No CSRF Protection on Booking Creation**
**File:** `bookings_app/views.py:20`  
**Severity:** 🔴 CRITICAL

```python
class BookingsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = []  # allow public create
```

**Issue:** Public POST endpoint without authentication allows:
- Spam bookings
- Resource exhaustion
- Booking conflicts
- No accountability

**Fix:**
```python
from rest_framework.permissions import AllowAny, IsAuthenticated

class BookingsView(APIView):
    authentication_classes = [JWTAuthentication]
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [AllowAny()]  # Or IsAuthenticatedOrReadOnly
        return [IsAuthenticated()]
```

---

## ⚠️ High Priority Issues

### 8. **Frontend/Backend API Endpoint Mismatch**
**Severity:** ⚠️ HIGH

**Frontend expects:**
- `/api/auth/login` (from api.ts:228)
- `/api/auth/register` (from api.ts:247)

**Backend provides:**
- `/api/auth/login/` (from accounts/urls.py:14)
- `/api/auth/register/` (from accounts/urls.py:11)

While Django's `APPEND_SLASH` middleware might handle this, it's inconsistent with:
- `/api/rooms` vs `/api/rooms/`
- `/bookings` vs `/bookings/`

**Impact:** API calls may fail or redirect unexpectedly.

---

### 9. **Incomplete Frontend Authentication Implementation**
**File:** `api.ts`  
**Severity:** ⚠️ HIGH

The frontend has THREE different authentication implementations:

**Implementation 1 (authApi.login):**
```typescript
const { token } = data;
if (token) {
  localStorage.setItem("token", token);
}
```

**Implementation 2 (login function):**
```typescript
export async function login(username: string, password: string): Promise<LoginResponse> {
  // Returns access/refresh but doesn't store them
}
```

**Implementation 3 (logout function):**
```typescript
localStorage.removeItem("access");
localStorage.removeItem("refresh");
localStorage.removeItem("user");
```

**Issue:** 
- Multiple token storage strategies
- No consistent token retrieval
- Token refresh logic missing
- Expired token handling absent

---

### 10. **Missing Client Profile Image Validation**
**File:** `accounts/models.py:14`  
**Severity:** ⚠️ HIGH

```python
class Client(models.Model):
    image = models.ImageField(upload_to='accounts/images')
```

**Issues:**
- No file size validation
- No file type validation (could upload executables)
- No image dimension validation
- Missing `null=True, blank=True` (required field)

**Fix:**
```python
from django.core.validators import FileExtensionValidator

class Client(models.Model):
    image = models.ImageField(
        upload_to='accounts/images',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])],
        help_text="Profile image (max 2MB)"
    )
```

Add size validation in the serializer.

---

### 11. **Weak Password Validation in Registration**
**File:** `accounts/serializers.py:20-28`  
**Severity:** ⚠️ HIGH

```python
def save(self):
    password = self.validated_data['password']
    confirm_password = self.validated_data['confirm_password']
    
    if password != confirm_password:
        raise serializers.ValidationError({'error':'Password did not match'})
```

**Issues:**
- No password strength validation
- Django's built-in password validators not called
- No minimum length check
- No complexity requirements

**Fix:**
```python
from django.contrib.auth.password_validation import validate_password

def validate(self, data):
    password = data.get('password')
    confirm_password = data.get('confirm_password')
    
    if password != confirm_password:
        raise serializers.ValidationError({'password': 'Passwords do not match'})
    
    # Use Django's built-in validators
    validate_password(password)
    
    return data
```

---

### 12. **Email Sending Without Error Handling**
**File:** `accounts/views.py:35-42`  
**Severity:** ⚠️ HIGH

```python
email = EmailMultiAlternatives(email_subject, '', to=[user.email])
email.attach_alternative(email_body, 'text/html')
email.send()
```

**Issues:**
- No try/except block
- Registration fails silently if email fails
- No retry mechanism
- User created even if email fails (later set to `is_active=True`)

**Fix:**
```python
try:
    email = EmailMultiAlternatives(email_subject, '', to=[user.email])
    email.attach_alternative(email_body, 'text/html')
    email.send(fail_silently=False)
except Exception as e:
    logger.error(f"Failed to send email to {user.email}: {str(e)}")
    # Continue anyway or handle appropriately
```

---

### 13. **User Activated Immediately After Registration**
**File:** `accounts/views.py:32-33`  
**Severity:** ⚠️ MEDIUM-HIGH

```python
user = serializer.save()
user.is_active = True
user.save()
```

But in the serializer:
```python
account.is_active = False
account.save()
```

**Issue:** User is set to inactive in serializer, then immediately activated in view. This negates email verification entirely.

**Fix:** Either:
1. Remove the `is_active = True` line to require email verification
2. Remove the email verification flow entirely
3. Add an email verification endpoint

---

## 📋 Medium Priority Issues

### 14. **Missing Pagination in List Views**
**Severity:** ⚠️ MEDIUM

While `PAGE_SIZE: 50` is configured in settings, the views don't use pagination properly:

```python
class RoomListAPIView(generics.ListCreateAPIView):
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'success': True, 'data': serializer.data})
```

**Issue:** Overriding `list()` bypasses DRF's built-in pagination.

**Fix:** Remove the custom `list()` method or implement pagination manually.

---

### 15. **Inconsistent Error Response Format**
**Severity:** ⚠️ MEDIUM

Different views return errors in different formats:

**Format 1:**
```python
return Response(serializer.errors, status=400)  # DRF default format
```

**Format 2:**
```python
return Response({'success': False, 'error': 'Room not found', 'status': 404}, status=404)
```

**Fix:** Use a custom exception handler for consistent formatting.

---

### 16. **Missing Request Body Validation**
**File:** `bookings_app/views.py:48-58`  
**Severity:** ⚠️ MEDIUM

```python
def post(self, request):
    payload = request.data
    room_id = payload.get('roomId') or payload.get('room_id')
    # ... manual validation
```

**Issue:** Manual validation instead of using DRF serializers leads to:
- Inconsistent validation
- More code to maintain
- Missing edge cases

**Fix:** Create and use `BookingCreateSerializer` already defined in serializers.py.

---

### 17. **No Input Sanitization**
**Severity:** ⚠️ MEDIUM

User inputs are not sanitized, particularly in:
- `guest_info` JSON field
- Room descriptions
- Search queries

**Potential Issues:**
- XSS attacks if displayed in admin panel
- JSON injection in guest_info field

---

### 18. **Missing Database Indexes**
**Severity:** ⚠️ MEDIUM

Common query fields lack indexes:

```python
# In Room model - missing indexes
location = models.CharField(max_length=255)  # Frequently filtered
type = models.CharField(max_length=50, choices=ROOM_TYPES)  # Frequently filtered
available = models.BooleanField(default=True)  # Frequently filtered

# In Booking model - missing indexes
check_in = models.DateField()  # Used in overlap queries
check_out = models.DateField()  # Used in overlap queries
status = models.CharField(max_length=10, choices=STATUS_CHOICES)  # Frequently filtered
```

**Fix:**
```python
class Meta:
    indexes = [
        models.Index(fields=['location', 'available']),
        models.Index(fields=['type', 'price']),
        models.Index(fields=['check_in', 'check_out']),
    ]
```

---

### 19. **Frontend API Base URL Hardcoded**
**File:** `api.ts:4`  
**Severity:** ⚠️ MEDIUM

```typescript
const API_BASE_URL = "https://room-booking-pjo6.onrender.com/api"
```

**Issue:** Cannot easily switch between development and production environments.

**Fix:**
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api"
```

---

### 20. **No Token Refresh Logic in Frontend**
**Severity:** ⚠️ MEDIUM

The frontend stores `access` and `refresh` tokens but has no logic to:
- Refresh expired access tokens
- Handle 401 errors
- Implement automatic retry with refreshed token

---

### 21. **Unused Swagger Security Definition**
**File:** `bookings/settings.py:66-75`  
**Severity:** ⚠️ LOW-MEDIUM

```python
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Token': {  # Updated to Token authentication
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
```

**Issue:** Configured for "Token" auth but using JWT. Swagger UI won't work correctly for testing.

**Fix:**
```python
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'JWT authorization using the Bearer scheme. Example: "Bearer {token}"'
        }
    },
    'USE_SESSION_AUTH': False,
}
```

---

### 22. **Missing Logging Configuration**
**Severity:** ⚠️ MEDIUM

No logging configured for:
- Authentication attempts
- Failed bookings
- Email sending failures
- Admin actions

---

## 📝 Code Quality Issues

### 23. **Inconsistent Code Formatting**
- Missing docstrings
- Inconsistent spacing (2 spaces in some files, 4 in others)
- Mixed quote styles (single and double quotes)
- Trailing whitespace (visible as `\r\n`)

### 24. **Dead Code / Duplicate Functions**

**File:** `api.ts`

```typescript
// Three different login implementations
export const authApi = { login: async ... }
export async function login(...): Promise<LoginResponse> { ... }
// Plus the authApi.login is different
```

### 25. **Magic Numbers and Strings**
```python
if int(guests) > room.max_guests:  # Should use room.max_guests explicitly
nights = (check_out_dt - check_in_dt).days  # No validation for max stay
```

### 26. **Type Safety Issues in Frontend**

```typescript
type Room = {}  // Empty type definition!

interface LoginResponse {
  access: string
  refresh: string
  user?: any  // Should be properly typed
}
```

### 27. **Missing API Response Types**

Frontend lacks TypeScript interfaces for:
- Booking responses
- Error responses
- Room detail responses
- User profile responses

---

## 🏗️ Architecture Issues

### 28. **Mixed Responsibility in Views**

The `BookingsView` POST method does too much:
- Request validation
- Business logic (date validation, price calculation)
- Data persistence
- Response formatting

Should be separated into:
- Serializer (validation)
- Service layer (business logic)
- View (HTTP handling)

### 29. **No Service Layer**

Business logic is scattered across views and serializers. Should have dedicated service classes for:
- BookingService (availability check, price calculation)
- AuthService (user registration flow)
- NotificationService (email sending)

### 30. **Frontend API Client Not Centralized**

The `api.ts` file has both named exports and default object exports, making it confusing to import:

```typescript
import { roomsApi, bookingsApi, authApi, login, register, logout } from './api'
```

Should be:
```typescript
import api from './api'

api.rooms.getAll()
api.auth.login()
api.bookings.create()
```

---

## 🔒 Security Best Practices Missing

### 31. **No Rate Limiting**
No protection against:
- Brute force login attempts
- Booking spam
- API abuse

**Recommendation:** Use `django-ratelimit` or DRF throttling.

### 32. **No Input Length Limits**
Fields like `description` have no max length in models:
```python
description = models.TextField()
```

Could cause database issues or DoS attacks.

### 33. **No Request Size Limits**
Missing middleware to limit request body size.

### 34. **Passwords Stored in LocalStorage (Frontend)**
While not directly in this code, the pattern suggests passwords might be handled insecurely.

### 35. **No HTTP Security Headers**
Missing:
- `X-Content-Type-Options`
- `X-Frame-Options`
- `Content-Security-Policy`
- `Strict-Transport-Security`

**Fix:** Use `django-csp` and configure security middleware.

---

## 🧪 Testing Issues

### 36. **No Tests**
Files contain only placeholder tests:
```python
# tests.py
# Create your tests here.
```

### 37. **No API Tests**
Critical paths untested:
- Authentication flow
- Booking creation and validation
- Admin permissions
- Edge cases (date overlaps, etc.)

---

## 📚 Documentation Issues

### 38. **API Documentation Mismatch**

The `API_DOCUMENTATION[1].md` file describes a different API structure than implemented:

**Documentation says:**
- `/auth/login` (no `/api` prefix)
- Returns `{ token: "jwt_token_here" }`

**Implementation:**
- `/api/auth/login/`
- Returns token auth response

### 39. **Missing Docstrings**
No documentation for:
- View methods
- Serializer validation logic
- Model methods
- Helper functions

---

## ✅ Positive Aspects

Despite the issues, there are some good practices:

1. ✅ Using DRF generics for CRUD operations
2. ✅ Custom permissions (`IsAdminOrReadOnly`)
3. ✅ Booking availability check logic
4. ✅ Price auto-calculation
5. ✅ Using JSONField for flexible data (amenities, guest_info)
6. ✅ CSRF trusted origins configured
7. ✅ Database connection supports both SQLite and PostgreSQL
8. ✅ Media file handling configured
9. ✅ Swagger/ReDoc API documentation setup
10. ✅ Proper use of related_name in foreign keys

---

## 🎯 Recommendations Priority Matrix

### Must Fix Immediately (P0)
1. ❗ Remove hardcoded SECRET_KEY
2. ❗ Set DEBUG = False for production
3. ❗ Fix ALLOWED_HOSTS
4. ❗ Fix CORS_ALLOW_ALL_ORIGINS
5. ❗ Choose ONE authentication method (JWT recommended)
6. ❗ Add user field to Booking model

### High Priority (P1 - This Week)
7. ⚠️ Implement proper authentication in frontend
8. ⚠️ Add token refresh logic
9. ⚠️ Protect booking endpoint or add rate limiting
10. ⚠️ Fix email verification flow
11. ⚠️ Add password strength validation
12. ⚠️ Add file upload validation

### Medium Priority (P2 - This Sprint)
13. 📋 Implement proper pagination
14. 📋 Standardize error responses
15. 📋 Add logging
16. 📋 Add database indexes
17. 📋 Use serializers for all validation
18. 📋 Add input sanitization

### Low Priority (P3 - Next Sprint)
19. 📝 Add comprehensive tests
20. 📝 Add docstrings
21. 📝 Refactor to use service layer
22. 📝 Clean up dead code
23. 📝 Add TypeScript types
24. 📝 Update API documentation

---

## 📊 Detailed Code Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Critical Security Issues | 7 | 🔴 Poor |
| High Priority Issues | 6 | ⚠️ Needs Attention |
| Medium Priority Issues | 15 | ⚠️ Needs Attention |
| Code Coverage | 0% | 🔴 Poor |
| Documentation Coverage | 10% | 🔴 Poor |
| Type Safety (Frontend) | 30% | ⚠️ Needs Improvement |
| API Consistency | 60% | ⚠️ Needs Improvement |

---

## 🔧 Quick Fixes Checklist

Create a `.env` file:
```env
DEBUG=False
SECRET_KEY=your-generated-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,room-booking-pjo6.onrender.com
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://your-frontend-domain.com
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
EMAIL=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
FERNET_SECRET_KEY=your-fernet-key
```

Update `settings.py`:
```python
import environ
import os
from pathlib import Path

env = environ.Env(
    DEBUG=(bool, False)
)

BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')
```

---

## 📞 Final Recommendations

1. **Start with Security**: Fix all P0 critical security issues before deploying to production
2. **Choose Authentication Strategy**: Standardize on JWT across frontend and backend
3. **Add Tests**: Minimum 70% code coverage for critical paths
4. **Documentation**: Keep API docs in sync with implementation
5. **Code Review Process**: Implement peer review before merging
6. **CI/CD**: Add automated testing and security scanning
7. **Monitoring**: Add logging and error tracking (e.g., Sentry)
8. **Performance**: Add caching for frequently accessed data (rooms list)

---

## 📝 Next Steps

1. Create a `.env` file with proper secrets
2. Fix authentication inconsistency
3. Add user field to bookings
4. Implement proper error handling
5. Add comprehensive tests
6. Update documentation

**Estimated Time to Fix Critical Issues:** 2-3 days  
**Estimated Time for High Priority Issues:** 1 week  
**Estimated Time for Complete Refactor:** 2-3 weeks

---

*End of Code Review Report*
