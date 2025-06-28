# Database Connection Timeout Fix Plan

## Problem Summary
The Cloud Run migration job is failing with a database connection timeout error when trying to connect to the PostgreSQL instance. The error occurs after attempting to establish a connection for the default timeout period.

## Root Cause Analysis
1. **Network connectivity**: Cloud Run service cannot reach Cloud SQL instance
2. **Missing Cloud SQL Proxy**: The migration job is not configured with Cloud SQL proxy
3. **Connection method**: Using direct IP connection instead of Unix socket through proxy
4. **Timeout settings**: Default connection timeout may be too short for cold starts

## Solution Steps

### 1. Verify Cloud SQL Instance Configuration
- [ ] Check Cloud SQL instance status and region
- [ ] Verify instance connection name format: `PROJECT_ID:REGION:INSTANCE_NAME`
- [ ] Ensure Cloud SQL Admin API is enabled
- [ ] Confirm the service account has Cloud SQL Client role

### 2. Update Cloud Run Job Configuration
- [ ] Add Cloud SQL connection to the job configuration
- [ ] Use the Cloud SQL proxy sidecar pattern or built-in connection
- [ ] Set proper environment variables for database connection

### 3. Fix Database Connection String
- [ ] Update `DATABASE_URL` to use Unix socket connection
- [ ] Format: `postgresql://USER:PASSWORD@/DATABASE_NAME?host=/cloudsql/CONNECTION_NAME`
- [ ] Remove any hardcoded IP addresses or hostnames

### 4. Implement Connection Retry Logic
- [ ] Add connection timeout and retry parameters
- [ ] Use connection pooling with appropriate settings
- [ ] Consider implementing exponential backoff

### 5. Update Deployment Configuration

#### Option A: Using Cloud Run Built-in Connection (Recommended)
```yaml
gcloud run jobs update saleor-migration-1751028053 \
  --add-cloudsql-instances=PROJECT_ID:REGION:INSTANCE_NAME \
  --region=us-central1
```

#### Option B: Using Cloud SQL Proxy Sidecar
```yaml
spec:
  template:
    spec:
      containers:
      - name: cloud-sql-proxy
        image: gcr.io/cloud-sql-connectors/cloud-sql-proxy:latest
        args:
          - "--port=5432"
          - "PROJECT_ID:REGION:INSTANCE_NAME"
      - name: app
        env:
        - name: DATABASE_URL
          value: "postgresql://USER:PASSWORD@localhost:5432/DATABASE_NAME"
```

### 6. Environment Variable Updates
```bash
# For Unix socket connection (recommended)
DATABASE_URL=postgresql://USER:PASSWORD@/DATABASE_NAME?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME

# Connection pool settings
CONN_MAX_AGE=600
DB_POOL_SIZE=10
DB_POOL_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
```

### 7. Testing Steps
1. [ ] Update the migration job with Cloud SQL connection
2. [ ] Run a test execution with verbose logging
3. [ ] Monitor Cloud SQL connections and Cloud Run logs
4. [ ] Verify successful database connection and migration completion

### 8. Production Deployment
1. [ ] Apply the same configuration to the main Saleor service
2. [ ] Update all environment variables in Secret Manager
3. [ ] Test the full deployment pipeline
4. [ ] Document the final working configuration

## Quick Fix Commands

```bash
# 1. Get Cloud SQL instance connection name
gcloud sql instances describe saleor-db --format="value(connectionName)"

# 2. Update migration job with Cloud SQL connection
gcloud run jobs update saleor-migration-1751028053 \
  --add-cloudsql-instances=PROJECT_ID:REGION:INSTANCE_NAME \
  --set-env-vars="DATABASE_URL=postgresql://saleor:PASSWORD@/saleor?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME" \
  --region=us-central1

# 3. Execute the updated job
gcloud run jobs execute saleor-migration-1751028053 --region=us-central1

# 4. Stream logs
gcloud run jobs executions logs --tail --region=us-central1
```

## Alternative Solutions

### If Cloud SQL Proxy doesn't work:
1. **VPC Connector**: Create a Serverless VPC Access connector for private IP connection
2. **Public IP with SSL**: Use Cloud SQL public IP with SSL certificates
3. **Cloud SQL Auth Proxy**: Use the newer Cloud SQL Auth proxy with IAM authentication

### Debugging Commands:
```bash
# Check service account permissions
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:*"

# Test database connection from Cloud Shell
gcloud sql connect saleor-db --user=saleor --database=saleor

# Check Cloud SQL instance settings
gcloud sql instances describe saleor-db
```

## Success Criteria
- [ ] Migration job completes successfully
- [ ] Database schema is fully migrated
- [ ] Connection is stable without timeouts
- [ ] Logs show successful connection using Unix socket
- [ ] Main Saleor service can connect using the same method

## Timeline
- Immediate fix: 30 minutes (using built-in Cloud SQL connection)
- Full implementation with testing: 2-3 hours
- Production deployment: 4-5 hours total