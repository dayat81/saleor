# Saleor Cloud Run Deployment Plan

**Date:** 2025-06-28  
**Project:** Saleor E-commerce Platform  
**GCP Project:** melodic-now-463704-k1  
**Current Status:** Infrastructure deployed, application deployment pending

## Overview

The Google Cloud infrastructure for Saleor is fully deployed via Terraform, but the application service is not yet accessible because no Docker image has been built and deployed to Cloud Run.

## Current Infrastructure Status

✅ **Terraform Infrastructure:** Complete (37 resources deployed)  
✅ **Artifact Registry:** Repository `saleor-33b5604e` created  
✅ **Load Balancer:** IP allocated (34.8.212.5)  
✅ **Database:** Cloud SQL PostgreSQL 15 ready  
✅ **Cache:** Redis Memorystore active  
❌ **Docker Image:** Not built/pushed  
❌ **Cloud Run Service:** Not deployed  
❌ **Application Access:** Not available  

## Deployment Tasks

### Phase 1: Docker Image Preparation

#### Task 1.1: Configure Docker Authentication
```bash
# Configure Docker to authenticate with Artifact Registry
gcloud auth configure-docker us-central1-docker.pkg.dev
```

**Purpose:** Enable Docker to push images to GCP Artifact Registry  
**Status:** 🔴 Pending  
**Priority:** High  

#### Task 1.2: Build Saleor Docker Image
```bash
# Navigate to Saleor project root
cd /home/hek/saleor

# Build Docker image with production configuration
docker build -t saleor-production .
```

**Requirements:**
- Valid Dockerfile in project root
- Production-ready configuration
- Health check endpoints configured
- Database migration support

**Status:** 🔴 Pending  
**Priority:** High  

#### Task 1.3: Tag and Push Image
```bash
# Tag image for Artifact Registry
docker tag saleor-production us-central1-docker.pkg.dev/melodic-now-463704-k1/saleor-33b5604e/saleor:latest

# Push to registry
docker push us-central1-docker.pkg.dev/melodic-now-463704-k1/saleor-33b5604e/saleor:latest
```

**Status:** 🔴 Pending  
**Priority:** High  

### Phase 2: Configuration Verification

#### Task 2.1: Environment Variables Audit
**Target:** Verify Terraform environment variables match Saleor requirements

**Terraform Environment Variables:**
- `DEBUG=False`
- `ALLOWED_HOSTS` (configured)
- `DATABASE_URL` (PostgreSQL connection)
- `REDIS_URL` (Redis connection)
- `SECRET_KEY` (from Secret Manager)
- `GS_BUCKET_NAME` (static files)
- `GS_MEDIA_BUCKET_NAME` (media files)
- `PLAYGROUND_ENABLED=True` (development)

**Action Items:**
- [ ] Compare with Saleor's required environment variables
- [ ] Verify database connection string format
- [ ] Ensure all storage buckets are properly configured
- [ ] Check health check endpoint (`/health/`)

**Status:** 🔴 Pending  
**Priority:** Medium  

### Phase 3: Service Deployment

#### Task 3.1: Deploy Cloud Run Service
```bash
# Deploy service (triggered by image push or manual update)
gcloud run services update saleor-app-33b5604e --region=us-central1

# Alternative: Terraform refresh to deploy with new image
terraform apply -refresh-only
```

**Expected Outcome:** Cloud Run service becomes available  
**Status:** 🔴 Pending  
**Priority:** High  

#### Task 3.2: Database Migration
```bash
# Execute database migrations via Cloud Run job
gcloud run jobs execute migration-job --region=us-central1 --wait
```

**Note:** May need to create migration job or run migrations manually  
**Status:** 🔴 Pending  
**Priority:** High  

### Phase 4: Service Verification

#### Task 4.1: Service Accessibility Test
```bash
# Get Cloud Run service URL
SERVICE_URL=$(gcloud run services describe saleor-app-33b5604e --region=us-central1 --format="get(status.url)")

# Test health endpoint
curl -f $SERVICE_URL/health/

# Test GraphQL endpoint
curl -f $SERVICE_URL/graphql/
```

**Expected Results:**
- Health endpoint returns 200 OK
- GraphQL endpoint accessible
- Service responds without errors

**Status:** 🔴 Pending  
**Priority:** Medium  

#### Task 4.2: Load Balancer Verification
```bash
# Test via Load Balancer IP
curl -f http://34.8.212.5/health/
```

**Expected:** HTTP redirect to HTTPS or direct access  
**Status:** 🔴 Pending  
**Priority:** Medium  

### Phase 5: DNS & SSL Configuration

#### Task 5.1: DNS Configuration
**Domain:** `saleor-demo.example.com` (configured in SSL certificate)

**Actions Required:**
- [ ] Update DNS A record to point to `34.8.212.5`
- [ ] Wait for SSL certificate provisioning (can take 10-60 minutes)
- [ ] Verify HTTPS access

**Status:** 🔴 Pending  
**Priority:** Low (can be done last)  

#### Task 5.2: SSL Certificate Verification
```bash
# Check SSL certificate status
gcloud compute ssl-certificates describe saleor-ssl-cert-33b5604e --global

# Test HTTPS access
curl -f https://saleor-demo.example.com/health/
```

**Status:** 🔴 Pending  
**Priority:** Low  

## Risk Assessment

### High Risk Items
1. **Docker Build Issues:** Dockerfile may need adjustments for Cloud Run
2. **Database Migrations:** Initial migration setup required
3. **Environment Configuration:** Missing or incorrect environment variables

### Medium Risk Items
1. **Resource Limits:** Cloud Run memory/CPU limits may need adjustment
2. **Storage Permissions:** Bucket access permissions verification needed

### Low Risk Items
1. **SSL Certificate:** Takes time but should provision automatically
2. **DNS Propagation:** Standard DNS update timing

## Success Criteria

✅ **Phase 1 Complete:** Docker image successfully pushed to Artifact Registry  
✅ **Phase 2 Complete:** Cloud Run service accessible via direct URL  
✅ **Phase 3 Complete:** Load Balancer routing to Cloud Run service  
✅ **Phase 4 Complete:** GraphQL API responding correctly  
✅ **Phase 5 Complete:** HTTPS access via custom domain  

## Rollback Plan

If deployment fails:
1. Check Cloud Run logs: `gcloud run services logs read saleor-app-33b5604e --region=us-central1`
2. Revert to previous image (if any): Update service to use different tag
3. Debug locally: Pull image and run locally for testing
4. Terraform rollback: Use previous state if infrastructure changes needed

## Estimated Timeline

- **Phase 1:** 15-20 minutes (Docker build time dependent)
- **Phase 2:** 10 minutes (configuration review)
- **Phase 3:** 10-15 minutes (deployment and migration)
- **Phase 4:** 5-10 minutes (testing and verification)
- **Phase 5:** 30-60 minutes (DNS propagation and SSL)

**Total Estimated Time:** 1-2 hours (mostly waiting for DNS/SSL)

## Next Steps

1. **Start with Task 1.1:** Configure Docker authentication
2. **Proceed sequentially** through tasks
3. **Monitor Cloud Run logs** during deployment
4. **Test thoroughly** before DNS configuration

---

*This plan assumes the current Terraform infrastructure remains stable and the Saleor application code is ready for production deployment.*