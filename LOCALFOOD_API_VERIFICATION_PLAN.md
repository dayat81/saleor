# LocalFood API Verification Plan

**Created**: 2025-06-28  
**Purpose**: Comprehensive verification of all URLs and endpoints documented in localfood-development-log.md  
**Status**: Ready for execution  
**Base URL**: http://localhost:8000

---

## Overview

This plan systematically tests all 14+ API endpoints, authentication mechanisms, and user flows documented in the LocalFood development log to ensure complete functionality before production deployment.

## Prerequisites

### Environment Setup
- [ ] LocalFood development server running (`python manage.py runserver`)
- [ ] SQLite database with migrations applied
- [ ] Admin user created (username: admin, password: admin123)
- [ ] Virtual environment activated
- [ ] All dependencies installed

### Testing Tools Required
- [ ] cURL (command line HTTP client)
- [ ] Web browser (for admin interface testing)
- [ ] API testing tool (Postman/Insomnia) - optional
- [ ] JSON formatter for response validation

---

## Phase 1: Infrastructure Verification (5 tests)

### Test 1.1: Development Server Status
**Objective**: Verify server starts and responds  
**URL**: `http://localhost:8000/`  
**Method**: GET  
**Expected**: HTTP 200 or Django welcome page  
**Command**:
```bash
curl -I http://localhost:8000/
```

### Test 1.2: Admin Interface Access
**Objective**: Verify Django admin is accessible  
**URL**: `http://localhost:8000/admin/`  
**Method**: GET  
**Expected**: Admin login page  
**Command**:
```bash
curl -s http://localhost:8000/admin/ | grep -i "django administration"
```

### Test 1.3: API Root Endpoint
**Objective**: Verify DRF browsable API is accessible  
**URL**: `http://localhost:8000/api/`  
**Method**: GET  
**Expected**: DRF API root page  
**Command**:
```bash
curl -I http://localhost:8000/api/
```

### Test 1.4: GraphQL Playground
**Objective**: Verify GraphQL endpoint is accessible  
**URL**: `http://localhost:8000/graphql/`  
**Method**: GET  
**Expected**: GraphQL playground interface  
**Command**:
```bash
curl -s http://localhost:8000/graphql/ | grep -i "graphql"
```

### Test 1.5: API Authentication Endpoint
**Objective**: Verify token authentication endpoint exists  
**URL**: `http://localhost:8000/api/auth/token/`  
**Method**: POST  
**Expected**: HTTP 400 (missing credentials) or authentication form  
**Command**:
```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{}' -w "%{http_code}"
```

---

## Phase 2: Authentication Testing (3 tests)

### Test 2.1: Admin Login
**Objective**: Verify admin credentials work  
**URL**: `http://localhost:8000/api/auth/token/`  
**Method**: POST  
**Credentials**: admin / admin123  
**Expected**: Valid token response  
**Command**:
```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```
**Save token for subsequent tests**: `export TOKEN="obtained_token_here"`

### Test 2.2: Invalid Credentials
**Objective**: Verify authentication rejects invalid credentials  
**URL**: `http://localhost:8000/api/auth/token/`  
**Method**: POST  
**Expected**: HTTP 400 with error message  
**Command**:
```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "invalid", "password": "wrong"}' \
  -w "%{http_code}"
```

### Test 2.3: Token Usage
**Objective**: Verify token works for protected endpoints  
**URL**: `http://localhost:8000/api/outlets/`  
**Method**: GET  
**Expected**: HTTP 200 with outlet list (may be empty)  
**Command**:
```bash
curl -H "Authorization: Token $TOKEN" \
  http://localhost:8000/api/outlets/ -w "%{http_code}"
```

---

## Phase 3: Outlet Management API (6 tests)

### Test 3.1: Outlet List (Unauthenticated)
**Objective**: Verify public outlet listing works  
**URL**: `http://localhost:8000/api/outlets/`  
**Method**: GET  
**Expected**: HTTP 200 with empty outlet list  
**Command**:
```bash
curl http://localhost:8000/api/outlets/ -w "%{http_code}"
```

### Test 3.2: Create Test Outlet
**Objective**: Create outlet for testing  
**URL**: `http://localhost:8000/api/outlets/`  
**Method**: POST  
**Expected**: HTTP 201 with outlet data  
**Command**:
```bash
curl -X POST http://localhost:8000/api/outlets/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "saleor_merchant_id": "test-merchant-001",
    "business_name": "Green Valley Farm",
    "description": "Organic vegetables and fresh produce",
    "address": "123 Farm Road, Green Valley, CA 90210",
    "latitude": 34.0522,
    "longitude": -118.2437,
    "delivery_radius": 15.0,
    "cuisine_types": ["organic", "farm_fresh"],
    "phone_number": "+1-555-0123",
    "email": "contact@greenvalleyfarm.com",
    "minimum_order": 25.00,
    "average_prep_time": 60,
    "is_organic_certified": true,
    "is_farm_to_table": true
  }'
```
**Save outlet ID**: `export OUTLET_ID="obtained_outlet_id_here"`

### Test 3.3: Outlet Detail View
**Objective**: Retrieve specific outlet  
**URL**: `http://localhost:8000/api/outlets/{outlet_id}/`  
**Method**: GET  
**Expected**: HTTP 200 with outlet details  
**Command**:
```bash
curl http://localhost:8000/api/outlets/$OUTLET_ID/
```

### Test 3.4: Nearby Outlets Search
**Objective**: Test geolocation-based outlet search  
**URL**: `http://localhost:8000/api/outlets/nearby/`  
**Method**: GET  
**Parameters**: lat, lng, max_distance  
**Expected**: HTTP 200 with filtered outlets  
**Command**:
```bash
curl "http://localhost:8000/api/outlets/nearby/?lat=34.0522&lng=-118.2437&max_distance=25"
```

### Test 3.5: My Outlets Filter
**Objective**: Test owner-specific outlet filtering  
**URL**: `http://localhost:8000/api/outlets/?my_outlets=true`  
**Method**: GET  
**Expected**: HTTP 200 with user's outlets  
**Command**:
```bash
curl -H "Authorization: Token $TOKEN" \
  "http://localhost:8000/api/outlets/?my_outlets=true"
```

### Test 3.6: Outlet Images Upload
**Objective**: Test outlet image management  
**URL**: `http://localhost:8000/api/outlet-images/`  
**Method**: POST  
**Expected**: HTTP 201 or proper validation error  
**Command**:
```bash
curl -X POST http://localhost:8000/api/outlet-images/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "outlet": "'$OUTLET_ID'",
    "alt_text": "Farm entrance",
    "is_primary": true
  }'
```

---

## Phase 4: Product Management API (7 tests)

### Test 4.1: Product List
**Objective**: Verify product listing endpoint  
**URL**: `http://localhost:8000/api/products/`  
**Method**: GET  
**Expected**: HTTP 200 with product list  
**Command**:
```bash
curl http://localhost:8000/api/products/
```

### Test 4.2: Create Test Product
**Objective**: Create product for testing  
**URL**: `http://localhost:8000/api/products/`  
**Method**: POST  
**Expected**: HTTP 201 with product data  
**Command**:
```bash
curl -X POST http://localhost:8000/api/products/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "saleor_product_id": "prod-tomatoes-001",
    "outlet": "'$OUTLET_ID'",
    "name": "Organic Cherry Tomatoes",
    "description": "Fresh organic cherry tomatoes, locally grown",
    "product_type": "produce",
    "sku": "GVF-TOMATO-CHERRY-001",
    "source_farm": "Green Valley Farm",
    "harvest_date": "2025-06-27",
    "best_by_date": "2025-07-05",
    "local_radius": 2.5,
    "is_organic_certified": true,
    "is_seasonal": true,
    "freshness_guarantee_days": 7,
    "carbon_footprint_kg": 0.15,
    "packaging_type": "Compostable basket",
    "is_plastic_free": true,
    "current_stock": 50
  }'
```
**Save product ID**: `export PRODUCT_ID="obtained_product_id_here"`

### Test 4.3: Fresh Products Filter
**Objective**: Test fresh products endpoint  
**URL**: `http://localhost:8000/api/products/fresh/`  
**Method**: GET  
**Expected**: HTTP 200 with fresh products  
**Command**:
```bash
curl "http://localhost:8000/api/products/fresh/?days_ago=7"
```

### Test 4.4: Seasonal Products Filter
**Objective**: Test seasonal products endpoint  
**URL**: `http://localhost:8000/api/products/seasonal/`  
**Method**: GET  
**Expected**: HTTP 200 with seasonal products  
**Command**:
```bash
curl http://localhost:8000/api/products/seasonal/
```

### Test 4.5: Sustainable Products Filter
**Objective**: Test sustainability scoring filter  
**URL**: `http://localhost:8000/api/products/sustainable/`  
**Method**: GET  
**Expected**: HTTP 200 with high-scoring products  
**Command**:
```bash
curl "http://localhost:8000/api/products/sustainable/?min_score=75"
```

### Test 4.6: Expiring Soon Filter
**Objective**: Test expiration date filtering  
**URL**: `http://localhost:8000/api/products/expiring_soon/`  
**Method**: GET  
**Expected**: HTTP 200 with expiring products  
**Command**:
```bash
curl "http://localhost:8000/api/products/expiring_soon/?days_ahead=3"
```

### Test 4.7: Product Nutrition Management
**Objective**: Test nutrition information endpoint  
**URL**: `http://localhost:8000/api/products/{product_id}/nutrition/`  
**Method**: POST  
**Expected**: HTTP 201 with nutrition data  
**Command**:
```bash
curl -X POST http://localhost:8000/api/products/$PRODUCT_ID/nutrition/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "calories_per_100g": 18,
    "protein_g": 0.9,
    "carbs_g": 3.9,
    "fat_g": 0.2,
    "fiber_g": 1.2,
    "allergens": []
  }'
```

---

## Phase 5: Customer Management API (5 tests)

### Test 5.1: Customer Profile Access (Unauthenticated)
**Objective**: Verify authentication required  
**URL**: `http://localhost:8000/api/customers/profile/`  
**Method**: GET  
**Expected**: HTTP 401 Unauthorized  
**Command**:
```bash
curl http://localhost:8000/api/customers/profile/ -w "%{http_code}"
```

### Test 5.2: Create Customer Profile
**Objective**: Create customer profile for testing  
**URL**: `http://localhost:8000/api/customers/create_profile/`  
**Method**: POST  
**Expected**: HTTP 201 with customer profile  
**Command**:
```bash
curl -X POST http://localhost:8000/api/customers/create_profile/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "saleor_customer_id": "cust-001",
    "preferred_radius": 20.0,
    "dietary_restrictions": ["vegetarian", "gluten-free"],
    "organic_preference": true,
    "local_preference": true,
    "delivery_addresses": [
      {
        "name": "Home",
        "address": "456 Oak Street, Los Angeles, CA 90210",
        "latitude": 34.0622,
        "longitude": -118.2537,
        "is_default": true
      }
    ]
  }'
```

### Test 5.3: Get Customer Profile
**Objective**: Retrieve customer profile  
**URL**: `http://localhost:8000/api/customers/profile/`  
**Method**: GET  
**Expected**: HTTP 200 with profile data  
**Command**:
```bash
curl -H "Authorization: Token $TOKEN" \
  http://localhost:8000/api/customers/profile/
```

### Test 5.4: Update Customer Preferences
**Objective**: Test profile update functionality  
**URL**: `http://localhost:8000/api/customers/update_preferences/`  
**Method**: PUT  
**Expected**: HTTP 200 with updated profile  
**Command**:
```bash
curl -X PUT http://localhost:8000/api/customers/update_preferences/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "preferred_radius": 25.0,
    "organic_preference": true
  }'
```

### Test 5.5: Add Favorite Outlet
**Objective**: Test favorite outlet management  
**URL**: `http://localhost:8000/api/customers/add_favorite_outlet/`  
**Method**: POST  
**Expected**: HTTP 200 with success message  
**Command**:
```bash
curl -X POST http://localhost:8000/api/customers/add_favorite_outlet/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"outlet_id": "'$OUTLET_ID'"}'
```

---

## Phase 6: Order Management API (6 tests)

### Test 6.1: Order List (Empty)
**Objective**: Verify order listing endpoint  
**URL**: `http://localhost:8000/api/orders/`  
**Method**: GET  
**Expected**: HTTP 200 with empty order list  
**Command**:
```bash
curl -H "Authorization: Token $TOKEN" \
  http://localhost:8000/api/orders/
```

### Test 6.2: Create Test Order
**Objective**: Create order for testing  
**URL**: `http://localhost:8000/api/orders/`  
**Method**: POST  
**Expected**: HTTP 201 with order data  
**Setup**: First get customer ID from profile
**Command**:
```bash
# Get customer ID first
CUSTOMER_ID=$(curl -s -H "Authorization: Token $TOKEN" \
  http://localhost:8000/api/customers/profile/ | \
  python -c "import sys, json; print(json.load(sys.stdin)['id'])")

# Create order
curl -X POST http://localhost:8000/api/orders/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "saleor_order_id": "order-001",
    "outlet": "'$OUTLET_ID'",
    "customer": "'$CUSTOMER_ID'",
    "delivery_address": {
      "name": "Home",
      "address": "456 Oak Street, Los Angeles, CA 90210",
      "latitude": 34.0622,
      "longitude": -118.2537
    },
    "estimated_delivery": "2025-06-28T18:00:00Z",
    "special_instructions": "Leave at front door"
  }'
```
**Save order ID**: `export ORDER_ID="obtained_order_id_here"`

### Test 6.3: Order Status Update
**Objective**: Test order status updates  
**URL**: `http://localhost:8000/api/orders/{order_id}/update_status/`  
**Method**: PUT  
**Expected**: HTTP 200 with updated order  
**Command**:
```bash
curl -X PUT http://localhost:8000/api/orders/$ORDER_ID/update_status/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "confirmed"}'
```

### Test 6.4: Active Orders Filter
**Objective**: Test active orders endpoint  
**URL**: `http://localhost:8000/api/orders/active/`  
**Method**: GET  
**Expected**: HTTP 200 with active orders  
**Command**:
```bash
curl -H "Authorization: Token $TOKEN" \
  http://localhost:8000/api/orders/active/
```

### Test 6.5: Today's Delivered Orders
**Objective**: Test delivered orders filter  
**URL**: `http://localhost:8000/api/orders/delivered_today/`  
**Method**: GET  
**Expected**: HTTP 200 with today's delivered orders  
**Command**:
```bash
curl -H "Authorization: Token $TOKEN" \
  http://localhost:8000/api/orders/delivered_today/
```

### Test 6.6: Sustainability Report
**Objective**: Test sustainability metrics endpoint  
**URL**: `http://localhost:8000/api/orders/sustainability_report/`  
**Method**: GET  
**Expected**: HTTP 200 with sustainability data  
**Command**:
```bash
curl -H "Authorization: Token $TOKEN" \
  http://localhost:8000/api/orders/sustainability_report/
```

---

## Phase 7: Admin Interface Testing (4 tests)

### Test 7.1: Admin Login
**Objective**: Verify admin interface login  
**Method**: Manual browser test  
**URL**: `http://localhost:8000/admin/`  
**Credentials**: admin / admin123  
**Expected**: Successful login to admin dashboard  

### Test 7.2: Outlet Management
**Objective**: Verify outlet admin interface  
**URL**: `http://localhost:8000/admin/outlets/outlet/`  
**Expected**: Outlet list with created test outlet  

### Test 7.3: Product Management
**Objective**: Verify product admin interface  
**URL**: `http://localhost:8000/admin/products/localproduct/`  
**Expected**: Product list with created test product  

### Test 7.4: Order Management
**Objective**: Verify order admin interface  
**URL**: `http://localhost:8000/admin/orders/localorder/`  
**Expected**: Order list with created test order  

---

## Phase 8: Error Handling & Edge Cases (5 tests)

### Test 8.1: Invalid Outlet ID
**Objective**: Test 404 handling  
**URL**: `http://localhost:8000/api/outlets/invalid-id/`  
**Method**: GET  
**Expected**: HTTP 404 Not Found  
**Command**:
```bash
curl http://localhost:8000/api/outlets/invalid-id/ -w "%{http_code}"
```

### Test 8.2: Unauthorized Access
**Objective**: Test permission enforcement  
**URL**: `http://localhost:8000/api/outlets/`  
**Method**: POST (without token)  
**Expected**: HTTP 401 Unauthorized  
**Command**:
```bash
curl -X POST http://localhost:8000/api/outlets/ \
  -H "Content-Type: application/json" \
  -d '{"business_name": "Test"}' -w "%{http_code}"
```

### Test 8.3: Invalid JSON Data
**Objective**: Test validation handling  
**URL**: `http://localhost:8000/api/outlets/`  
**Method**: POST  
**Expected**: HTTP 400 Bad Request  
**Command**:
```bash
curl -X POST http://localhost:8000/api/outlets/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}' -w "%{http_code}"
```

### Test 8.4: Invalid Geolocation Parameters
**Objective**: Test parameter validation  
**URL**: `http://localhost:8000/api/outlets/nearby/?lat=invalid&lng=invalid`  
**Method**: GET  
**Expected**: HTTP 400 Bad Request  
**Command**:
```bash
curl "http://localhost:8000/api/outlets/nearby/?lat=invalid&lng=invalid" -w "%{http_code}"
```

### Test 8.5: Rate Limiting (if implemented)
**Objective**: Test rate limiting behavior  
**Method**: Multiple rapid requests  
**Expected**: Appropriate rate limiting response  

---

## Phase 9: Performance & Integration (3 tests)

### Test 9.1: GraphQL Query
**Objective**: Test GraphQL integration  
**URL**: `http://localhost:8000/graphql/`  
**Method**: POST  
**Expected**: Valid GraphQL response  
**Command**:
```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ __schema { types { name } } }"
  }'
```

### Test 9.2: Response Time Check
**Objective**: Verify acceptable response times  
**Method**: Time multiple endpoint calls  
**Expected**: < 2 seconds per request  
**Command**:
```bash
time curl -s http://localhost:8000/api/outlets/ > /dev/null
```

### Test 9.3: Concurrent Requests
**Objective**: Test concurrent request handling  
**Method**: Multiple simultaneous requests  
**Expected**: All requests complete successfully  
**Command**:
```bash
for i in {1..5}; do
  curl -s http://localhost:8000/api/outlets/ &
done
wait
```

---

## Verification Checklist

### Pre-execution Checklist
- [ ] Development server running on port 8000
- [ ] Database migrations applied
- [ ] Admin user created
- [ ] Virtual environment activated
- [ ] All dependencies installed
- [ ] Testing tools available (curl, browser)

### Success Criteria
- [ ] All infrastructure endpoints return expected status codes
- [ ] Authentication works for all user types
- [ ] All CRUD operations function correctly
- [ ] Geolocation features work properly
- [ ] Custom filters and actions work
- [ ] Admin interface is fully functional
- [ ] Error handling is appropriate
- [ ] Performance is acceptable
- [ ] GraphQL integration works

### Post-execution Actions
- [ ] Document any failures or issues
- [ ] Update API documentation if needed
- [ ] Create test data cleanup script
- [ ] Generate verification report
- [ ] Plan production deployment testing

---

## Expected Results Summary

### Endpoint Count Verification
- **Infrastructure**: 4 endpoints
- **Authentication**: 1 endpoint  
- **Outlets**: 3 main + 3 custom actions = 6 endpoints
- **Products**: 3 main + 4 custom actions = 7 endpoints
- **Customers**: 2 main + 3 custom actions = 5 endpoints
- **Orders**: 3 main + 3 custom actions = 6 endpoints
- **Admin**: 4 interface pages
- **GraphQL**: 1 endpoint

**Total**: 32+ endpoints and interfaces to verify

### Success Metrics
- **Functional Tests**: 95%+ pass rate
- **Performance**: < 2s average response time
- **Security**: All unauthorized access properly blocked
- **Data Integrity**: All CRUD operations work correctly
- **Integration**: Saleor GraphQL client operational

---

*Plan created: 2025-06-28*  
*Ready for execution with LocalFood development server*