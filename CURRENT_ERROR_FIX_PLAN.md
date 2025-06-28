# Current Database Connection Error Fix Plan

## Real-Time Log Monitoring Results
**Timestamp**: 2025-06-28 07:16:16 WIB

### Current Error Identified
```
django.db.utils.OperationalError: connection timeout expired
```

### Error Analysis from Logs
- **Error**: Connection timeout when trying to connect to Cloud SQL public IP (34.41.195.120:5432)
- **Root Cause**: Cloud SQL instance doesn't allow connections from Cloud Run public IPs
- **Issue**: No authorized networks configured for public IP access

### Current Configuration
- **DATABASE_URL**: `postgresql://saleor:***@34.41.195.120:5432/saleor`
- **Connection Method**: Direct public IP connection
- **Authorized Networks**: None configured

## Root Cause Analysis

### Problem 1: Network Security
- Cloud SQL instance has public IP but no authorized networks
- Cloud Run services use dynamic public IPs that aren't whitelisted
- Connection attempts are being blocked at the network level

### Problem 2: Connection Method
- Using public IP instead of private connectivity
- No Cloud SQL proxy configuration in use
- Missing proper Cloud SQL IAM authentication

## Fix Plan - Multiple Options

### Option 1: Enable All Cloud Run IPs (Quick Fix)
```bash
# Allow all Cloud Run traffic (less secure but functional)
gcloud sql instances patch saleor-db-demo \
  --authorized-networks=0.0.0.0/0 \
  --region=us-central1
```

**Pros**: Quick immediate fix
**Cons**: Security risk - open to all IPs

### Option 2: Use Cloud SQL Proxy with Private IP (Recommended)
```bash
# 1. Configure Cloud SQL for private IP only
gcloud sql instances patch saleor-db-demo \
  --no-assign-ip \
  --network=projects/melodic-now-463704-k1/global/networks/default

# 2. Update job to use Cloud SQL proxy
gcloud run jobs update saleor-migration-1751028053 \
  --add-cloudsql-instances=melodic-now-463704-k1:us-central1:saleor-db-demo \
  --set-env-vars="DATABASE_URL=postgresql://saleor:secure-db-password-123@/saleor?host=/cloudsql/melodic-now-463704-k1:us-central1:saleor-db-demo" \
  --region=us-central1
```

### Option 3: Use VPC Connector (Production Ready)
```bash
# 1. Create VPC Connector
gcloud compute networks vpc-access connectors create saleor-connector \
  --network=default \
  --range=10.8.0.0/28 \
  --region=us-central1

# 2. Update job to use VPC connector
gcloud run jobs update saleor-migration-1751028053 \
  --vpc-connector=saleor-connector \
  --set-env-vars="DATABASE_URL=postgresql://saleor:secure-db-password-123@PRIVATE_IP:5432/saleor" \
  --region=us-central1
```

## Immediate Action Plan

### Step 1: Quick Fix - Allow Cloud Run IPs
Since we need immediate resolution, temporarily allow Cloud Run traffic:

```bash
# Get Cloud Run IP ranges (approximate)
gcloud sql instances patch saleor-db-demo \
  --authorized-networks="34.102.136.180/32,34.71.242.81/32,35.244.181.169/32" \
  --region=us-central1
```

### Step 2: Test Connection
```bash
# Execute migration with current config
gcloud run jobs execute saleor-migration-1751028053 --region=us-central1
```

### Step 3: Monitor Results
```bash
# Stream logs in real-time
gcloud logging tail "resource.type=cloud_run_job AND resource.labels.job_name=saleor-migration-1751028053"
```

## Long-term Solution Implementation

### Phase 1: Immediate (15 minutes)
1. ✅ Identify error from logs
2. ⏳ Add Cloud Run IP ranges to authorized networks
3. ⏳ Test migration execution
4. ⏳ Verify successful database connection

### Phase 2: Security Enhancement (1-2 hours)
1. Implement VPC Connector for private connectivity
2. Remove public IP authorization
3. Update all Cloud Run services to use VPC connector
4. Test complete deployment pipeline

### Phase 3: Production Hardening (2-4 hours)
1. Implement Cloud SQL IAM authentication
2. Use managed service accounts
3. Enable SSL/TLS encryption
4. Add connection pooling configuration

## Success Criteria
- [ ] Migration job completes successfully
- [ ] Database connection establishes without timeout
- [ ] All Django migrations applied successfully
- [ ] Connection uses secure private networking (long-term)

## Rollback Plan
If the fix fails:
1. Revert to original Cloud SQL configuration
2. Use Cloud SQL proxy with Unix socket connection
3. Implement manual migration using Cloud Shell

## Monitoring Commands
```bash
# Real-time log monitoring
gcloud logging tail "resource.type=cloud_run_job"

# Check execution status
gcloud run jobs executions list --job=saleor-migration-1751028053 --region=us-central1 --limit=1

# Verify Cloud SQL connections
gcloud sql operations list --instance=saleor-db-demo --limit=5
```

## Next Steps
1. Execute Option 1 (quick fix) immediately
2. Monitor migration execution
3. Plan implementation of Option 3 (VPC connector) for production
4. Update documentation with final solution