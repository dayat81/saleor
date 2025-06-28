# Database Connectivity Fix Plan

**Created**: 2025-06-28 09:10:00  
**Severity**: Critical  
**Impact**: 4/8 API verification tests failing  

---

## Issue Analysis

### Failed Test Cases Summary

| Test | Status | Error Pattern | Root Cause |
|------|--------|---------------|------------|
| Channels Query | ❌ FAIL | `connection to server at "127.0.0.1", port 5432 failed: Connection refused` | Database URL not configured |
| Products Query | ❌ FAIL | `connection to server at "127.0.0.1", port 5432 failed: server closed unexpectedly` | Database URL not configured |
| Categories Query | ❌ FAIL | `connection to server at "127.0.0.1", port 5432 failed: server closed unexpectedly` | Database URL not configured |
| Collections Query | ❌ FAIL | `connection to server at "127.0.0.1", port 5432 failed: server closed unexpectedly` | Database URL not configured |

### Root Cause Analysis

**Primary Issue**: Cloud Run service is attempting to connect to `localhost:5432` instead of the Cloud SQL instance at `34.41.195.120:5432`

**Evidence**:
1. All database-dependent queries fail with connection to `127.0.0.1:5432`
2. Non-database operations (schema introspection, performance checks) pass
3. Authentication and GraphQL framework working correctly
4. Error occurs during Django's `ensure_connection()` phase

**Technical Stack Trace Pattern**:
```
django.db.backends.base.base.py:279 -> ensure_connection()
django.db.backends.postgresql.base.py:332 -> get_new_connection()
psycopg.connection.py:117 -> connect()
OperationalError: connection failed: connection to server at "127.0.0.1", port 5432
```

---

## Current Environment Status

### ✅ Working Components
- Cloud Run service deployed and running
- Authentication with IAM tokens functional
- GraphQL schema accessible (1378 types, 311 mutations)
- RSA_PRIVATE_KEY properly configured
- ALLOWED_HOSTS set to `*`

### ❌ Failing Components
- Database connectivity to Cloud SQL
- All Django ORM-dependent GraphQL queries
- User authentication (depends on database for user lookup)
- Plugin system initialization (requires database access)

### Environment Variables Status
- `RSA_PRIVATE_KEY`: ✅ Configured
- `ALLOWED_HOSTS`: ✅ Set to `*`
- `DEBUG`: ✅ Set to `False`
- `DATABASE_URL`: ❌ **MISSING OR INCORRECT**

---

## Fix Implementation Plan

### Phase 1: Immediate Database URL Configuration ⚡ (5 minutes)

**Objective**: Configure correct DATABASE_URL environment variable in Cloud Run

**Steps**:
1. **Verify Current DATABASE_URL Status**
   ```bash
   gcloud run services describe saleor-app --region=us-central1 --project=melodic-now-463704-k1 --format="value(spec.template.spec.template.spec.containers[0].env[].name,spec.template.spec.template.spec.containers[0].env[].value)" | grep -i database
   ```

2. **Set Correct DATABASE_URL**
   ```bash
   gcloud run services update saleor-app \
     --region=us-central1 \
     --project=melodic-now-463704-k1 \
     --set-env-vars="DATABASE_URL=postgresql://saleor:Axwn5J0V6CJqF3e1@34.41.195.120:5432/saleor-db"
   ```

3. **Verify Service Deployment**
   ```bash
   gcloud run services describe saleor-app --region=us-central1 --project=melodic-now-463704-k1 --format="value(status.url)"
   ```

**Expected Result**: Cloud Run service redeploys with correct database configuration

### Phase 2: Database Connection Validation 🔍 (10 minutes)

**Objective**: Verify database connectivity and configuration

**Steps**:
1. **Test Direct Database Connection**
   ```bash
   # Test Cloud SQL connectivity
   gcloud sql connect saleor-db-demo --user=saleor --project=melodic-now-463704-k1
   ```

2. **Verify Database Schema**
   ```sql
   \l  -- List databases
   \c saleor-db  -- Connect to saleor database
   \dt  -- List tables
   SELECT COUNT(*) FROM django_migrations;  -- Check migration status
   ```

3. **Check Cloud SQL Instance Status**
   ```bash
   gcloud sql instances describe saleor-db-demo --project=melodic-now-463704-k1
   ```

**Expected Result**: Confirm database is accessible and properly configured

### Phase 3: Cloud Run Environment Verification 🛠️ (15 minutes)

**Objective**: Ensure all required environment variables are properly set

**Steps**:
1. **Comprehensive Environment Check**
   ```bash
   gcloud run services describe saleor-app \
     --region=us-central1 \
     --project=melodic-now-463704-k1 \
     --format="value(spec.template.spec.template.spec.containers[0].env[].name,spec.template.spec.template.spec.containers[0].env[].value)"
   ```

2. **Required Environment Variables Checklist**:
   - [ ] `DATABASE_URL` → `postgresql://saleor:Axwn5J0V6CJqF3e1@34.41.195.120:5432/saleor-db`
   - [ ] `RSA_PRIVATE_KEY` → (Base64 encoded RSA key)
   - [ ] `ALLOWED_HOSTS` → `*`
   - [ ] `DEBUG` → `False`
   - [ ] `DJANGO_SETTINGS_MODULE` → (if needed)

3. **Service Health Check**
   ```bash
   # Check service logs for startup issues
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=saleor-app" \
     --limit=10 \
     --project=melodic-now-463704-k1 \
     --format="value(timestamp,severity,textPayload)"
   ```

**Expected Result**: All environment variables correctly configured

### Phase 4: API Verification Re-run 🧪 (10 minutes)

**Objective**: Confirm all database-dependent tests pass

**Steps**:
1. **Run Comprehensive Verification**
   ```bash
   python comprehensive_verification_plan.py
   ```

2. **Run Targeted Database Tests**
   ```bash
   # Test specific database queries with authentication
   TOKEN=$(gcloud auth print-identity-token)
   
   # Test channels query
   curl -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -X POST "https://saleor-app-hvodeun2nq-uc.a.run.app/graphql/" \
        -d '{"query":"{ channels { id name slug isActive currencyCode } }"}'
   
   # Test products query
   curl -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -X POST "https://saleor-app-hvodeun2nq-uc.a.run.app/graphql/" \
        -d '{"query":"{ products(first:5, channel:\"default-channel\") { edges { node { id name } } } }"}'
   ```

3. **Performance Verification**
   ```bash
   # Test response times for database queries
   time curl -H "Authorization: Bearer $TOKEN" \
             -H "Content-Type: application/json" \
             -X POST "https://saleor-app-hvodeun2nq-uc.a.run.app/graphql/" \
             -d '{"query":"{ categories(first:10) { edges { node { id name } } } }"}'
   ```

**Expected Result**: All 8 tests pass, database queries return successful responses

---

## Alternative Solutions (If Primary Fix Fails)

### Option A: Cloud SQL Proxy Configuration
**Use Case**: If direct IP connection continues to fail

**Implementation**:
1. **Enable Cloud SQL Admin API**
   ```bash
   gcloud services enable sqladmin.googleapis.com --project=melodic-now-463704-k1
   ```

2. **Configure Cloud SQL Proxy in Cloud Run**
   ```bash
   gcloud run services update saleor-app \
     --region=us-central1 \
     --project=melodic-now-463704-k1 \
     --add-cloudsql-instances=melodic-now-463704-k1:us-central1:saleor-db-demo \
     --set-env-vars="DATABASE_URL=postgresql://saleor:Axwn5J0V6CJqF3e1@/cloudsql/melodic-now-463704-k1:us-central1:saleor-db-demo/saleor-db"
   ```

### Option B: Connection Pooling Configuration
**Use Case**: If connection instability persists

**Implementation**:
1. **Add Connection Pool Settings**
   ```bash
   gcloud run services update saleor-app \
     --region=us-central1 \
     --project=melodic-now-463704-k1 \
     --set-env-vars="DATABASE_URL=postgresql://saleor:Axwn5J0V6CJqF3e1@34.41.195.120:5432/saleor-db?pool_pre_ping=true&pool_recycle=300"
   ```

### Option C: Network Security Configuration
**Use Case**: If connection is blocked by firewall rules

**Implementation**:
1. **Verify Authorized Networks**
   ```bash
   gcloud sql instances describe saleor-db-demo \
     --project=melodic-now-463704-k1 \
     --format="value(settings.ipConfiguration.authorizedNetworks[].value)"
   ```

2. **Add Cloud Run IP Ranges** (if needed)
   ```bash
   gcloud sql instances patch saleor-db-demo \
     --project=melodic-now-463704-k1 \
     --authorized-networks=0.0.0.0/0
   ```

---

## Success Criteria

### ✅ Primary Success Indicators
- [ ] All 4 failed database tests now pass
- [ ] Channels query returns valid channel data or empty array
- [ ] Products query executes without connection errors
- [ ] Categories query executes without connection errors
- [ ] Collections query executes without connection errors

### ✅ Secondary Success Indicators
- [ ] Response times under 2 seconds for database queries
- [ ] No connection timeout errors in Cloud Run logs
- [ ] Authentication continues to work properly
- [ ] GraphQL schema introspection remains functional

### ✅ Verification Metrics
- [ ] Test success rate: 8/8 (100%)
- [ ] Database connection errors: 0
- [ ] Average response time: < 1.5 seconds
- [ ] Cloud Run service stable and responsive

---

## Risk Assessment

### 🟢 Low Risk Actions
- Setting DATABASE_URL environment variable
- Running verification tests
- Checking environment variables

### 🟡 Medium Risk Actions
- Updating Cloud Run service (causes brief downtime)
- Modifying Cloud SQL authorized networks
- Connection pool configuration changes

### 🔴 High Risk Actions
- Changing Cloud SQL instance configuration
- Modifying database credentials
- Network security rule changes

---

## Timeline & Dependencies

### Immediate (0-30 minutes)
- **Phase 1**: DATABASE_URL configuration ⚡
- **Phase 2**: Database connectivity validation 🔍

### Short-term (30-60 minutes)
- **Phase 3**: Complete environment verification 🛠️
- **Phase 4**: Full API verification re-run 🧪

### Dependencies
- Cloud SQL instance must be running and accessible
- Cloud Run service must have proper IAM permissions
- Network connectivity between Cloud Run and Cloud SQL

---

## Monitoring & Validation

### Real-time Monitoring
```bash
# Monitor Cloud Run logs during fix
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=saleor-app" \
  --project=melodic-now-463704-k1
```

### Success Validation Commands
```bash
# Quick connectivity test
TOKEN=$(gcloud auth print-identity-token)
curl -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -X POST "https://saleor-app-hvodeun2nq-uc.a.run.app/graphql/" \
     -d '{"query":"{ channels { id name } }"}' | jq .

# Comprehensive verification
python comprehensive_verification_plan.py
```

---

## Post-Fix Actions

### 1. Update Documentation
- [ ] Update ISSUE_TRACKING_SUMMARY.md with resolution
- [ ] Update saleor-api-verification-log.md with success results
- [ ] Create follow-up verification schedule

### 2. Preventive Measures
- [ ] Add DATABASE_URL to environment variable monitoring
- [ ] Create automated health checks for database connectivity
- [ ] Document environment variable requirements

### 3. Performance Optimization
- [ ] Monitor database query performance
- [ ] Consider connection pooling optimization
- [ ] Implement retry logic for transient failures

---

**Next Action**: Execute Phase 1 - DATABASE_URL configuration immediately to resolve critical database connectivity issue.