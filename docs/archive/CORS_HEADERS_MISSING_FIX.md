# CORS Headers Missing - Browser Error Analysis

**Error:** "Access to fetch at '...' from origin 'https://app.pipelabs.xyz' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource."

**Date:** February 8, 2026

---

## 🔍 **Investigation Results**

### **curl Tests Show CORS Headers ARE Present:**

**OPTIONS Preflight:**
```bash
curl -X OPTIONS .../bots/{id}/start \
  -H "Origin: https://app.pipelabs.xyz" \
  -H "Access-Control-Request-Method: POST"
```

**Response:**
```
access-control-allow-origin: https://app.pipelabs.xyz ✅
access-control-allow-methods: GET, POST, PUT, DELETE, OPTIONS ✅
access-control-allow-headers: content-type,x-wallet-address ✅
access-control-allow-credentials: true ✅
```

**POST Request:**
```bash
curl -X POST .../bots/{id}/start \
  -H "Origin: https://app.pipelabs.xyz" \
  -H "Content-Type: application/json"
```

**Response:**
```
HTTP/2 401
access-control-allow-credentials: true ✅
access-control-allow-origin: https://app.pipelabs.xyz ✅
```

**Conclusion:** Backend IS returning CORS headers correctly.

---

## ❓ **Why Browser Says Headers Are Missing?**

**Possible Causes:**

1. **Railway Edge Proxy Issue**
   - Edge proxy might strip headers for certain requests
   - Browser might hit edge proxy that doesn't have CORS headers
   - Railway edge might cache responses without CORS

2. **Exception Handler Bypassing CORS**
   - If an exception is raised before CORS middleware processes response
   - Exception handler might return response without CORS headers
   - Need to check if HTTPException responses include CORS

3. **Browser Cache**
   - Old error cached
   - Preflight response cached incorrectly
   - Need to clear cache completely

4. **Timing Issue**
   - Browser checks headers before preflight completes
   - Race condition between OPTIONS and POST

---

## 🔧 **Backend CORS Config (Current)**

```python
# Line 317-324 in app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # ["https://app.pipelabs.xyz", ...]
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)
```

**Status:** ✅ Correctly placed BEFORE routes (line 317, routes start at 332)
**Status:** ✅ Origin is correct (no trailing slash)
**Status:** ✅ Methods include POST
**Status:** ✅ Headers allow all

---

## 🛠️ **Potential Fixes**

### **Fix 1: Ensure Exception Handlers Include CORS**

FastAPI exception handlers might bypass CORS middleware. Need to check if HTTPException responses include CORS headers.

### **Fix 2: Add Explicit CORS Headers to Exception Responses**

If exception handlers bypass middleware, manually add CORS headers:

```python
from fastapi.responses import JSONResponse
from fastapi import Request

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
    # Manually add CORS headers
    response.headers["Access-Control-Allow-Origin"] = "https://app.pipelabs.xyz"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response
```

### **Fix 3: Check Railway Edge Configuration**

Railway edge proxy might need CORS configuration. Check Railway dashboard settings.

---

## 📋 **Next Steps**

1. **Check if exception handlers bypass CORS** - Review all exception handlers
2. **Add CORS headers to exception responses** - Ensure all responses include CORS
3. **Test with browser Network tab** - See actual request/response headers
4. **Check Railway edge logs** - See if edge proxy is modifying headers

---

## 🧪 **Test After Fix**

```bash
# Test OPTIONS
curl -X OPTIONS .../bots/{id}/start \
  -H "Origin: https://app.pipelabs.xyz" \
  -H "Access-Control-Request-Method: POST" \
  -v | grep -i "access-control"

# Test POST (should return 401 with CORS headers)
curl -X POST .../bots/{id}/start \
  -H "Origin: https://app.pipelabs.xyz" \
  -H "Content-Type: application/json" \
  -v | grep -i "access-control"
```

Both should show `access-control-allow-origin: https://app.pipelabs.xyz`

---

**Need to check exception handlers and ensure they include CORS headers.**
