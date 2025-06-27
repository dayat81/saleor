#!/bin/bash
# Complete Saleor deployment after Docker is available
# This script assumes infrastructure is already created

set -euo pipefail

PROJECT_ID="melodic-now-463704-k1"
REGION="us-central1"
REPOSITORY="saleor-demo"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
log_info "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    log_error "Docker is not available. Please install Docker Desktop and enable WSL integration."
    exit 1
fi

if ! command -v /opt/google-cloud-sdk/bin/gcloud &> /dev/null; then
    log_error "gcloud CLI not found at expected location."
    exit 1
fi

# Set up gcloud
log_info "Configuring gcloud..."
/opt/google-cloud-sdk/bin/gcloud config set project $PROJECT_ID

# Configure Docker for Artifact Registry
log_info "Configuring Docker for Artifact Registry..."
/opt/google-cloud-sdk/bin/gcloud auth configure-docker $REGION-docker.pkg.dev

# Build application image
log_info "Building Saleor application image..."
docker build -f Dockerfile.cloudrun \
    -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/saleor:latest \
    .

# Build worker image
log_info "Building Saleor worker image..."
docker build -f Dockerfile.worker \
    -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/saleor-worker:latest \
    .

# Push images
log_info "Pushing images to Artifact Registry..."
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/saleor:latest
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/saleor-worker:latest

# Wait for Redis to be ready
log_info "Checking Redis instance status..."
while true; do
    REDIS_STATUS=$(/opt/google-cloud-sdk/bin/gcloud redis instances describe saleor-redis-demo --region=$REGION --format="value(state)")
    if [ "$REDIS_STATUS" == "READY" ]; then
        log_info "Redis instance is ready"
        break
    else
        log_info "Redis instance status: $REDIS_STATUS - waiting..."
        sleep 30
    fi
done

# Get Redis host
REDIS_HOST=$(/opt/google-cloud-sdk/bin/gcloud redis instances describe saleor-redis-demo --region=$REGION --format="value(host)")
log_info "Redis host: $REDIS_HOST"

# Deploy to Cloud Run
log_info "Deploying to Cloud Run..."
/opt/google-cloud-sdk/bin/gcloud run deploy saleor-app \
    --image=$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/saleor:latest \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=2 \
    --timeout=900 \
    --max-instances=10 \
    --concurrency=200 \
    --set-env-vars="DATABASE_URL=postgresql://saleor:secure-db-password-123@34.41.195.120:5432/saleor,REDIS_URL=redis://$REDIS_HOST:6379/0,CELERY_BROKER_URL=redis://$REDIS_HOST:6379/0,GS_PROJECT_ID=$PROJECT_ID,GS_BUCKET_NAME=saleor-static-$PROJECT_ID,GS_MEDIA_BUCKET_NAME=saleor-media-$PROJECT_ID,GS_MEDIA_PRIVATE_BUCKET_NAME=saleor-private-$PROJECT_ID,PUBLIC_URL=https://saleor-app-$(echo $PROJECT_ID | tr _ -)-$REGION.a.run.app,ALLOWED_HOSTS=*,ALLOWED_CLIENT_HOSTS=*,EMAIL_URL=console://,DEBUG=False,PLAYGROUND_ENABLED=True" \
    --set-secrets="SECRET_KEY=saleor-django-secret-key:latest" \
    --quiet

# Get service URL
SERVICE_URL=$(/opt/google-cloud-sdk/bin/gcloud run services describe saleor-app --region=$REGION --format="value(status.url)")
log_info "Service deployed at: $SERVICE_URL"

# Run database migrations
log_info "Running database migrations..."
MIGRATION_JOB="saleor-migration-$(date +%s)"

/opt/google-cloud-sdk/bin/gcloud run jobs create $MIGRATION_JOB \
    --image=$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/saleor:latest \
    --region=$REGION \
    --memory=1Gi \
    --cpu=1 \
    --task-count=1 \
    --parallelism=1 \
    --command=python \
    --args="manage.py,migrate" \
    --set-env-vars="DATABASE_URL=postgresql://saleor:secure-db-password-123@34.41.195.120:5432/saleor,REDIS_URL=redis://$REDIS_HOST:6379/0" \
    --set-secrets="SECRET_KEY=saleor-django-secret-key:latest" \
    --quiet

/opt/google-cloud-sdk/bin/gcloud run jobs execute $MIGRATION_JOB \
    --region=$REGION \
    --wait \
    --quiet

/opt/google-cloud-sdk/bin/gcloud run jobs delete $MIGRATION_JOB \
    --region=$REGION \
    --quiet

# Populate sample data
log_info "Populating sample data..."
POPULATE_JOB="saleor-populate-$(date +%s)"

/opt/google-cloud-sdk/bin/gcloud run jobs create $POPULATE_JOB \
    --image=$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/saleor:latest \
    --region=$REGION \
    --memory=1Gi \
    --cpu=1 \
    --task-count=1 \
    --parallelism=1 \
    --command=python \
    --args="manage.py,populatedb,--createsuperuser" \
    --set-env-vars="DATABASE_URL=postgresql://saleor:secure-db-password-123@34.41.195.120:5432/saleor,REDIS_URL=redis://$REDIS_HOST:6379/0" \
    --set-secrets="SECRET_KEY=saleor-django-secret-key:latest" \
    --quiet

/opt/google-cloud-sdk/bin/gcloud run jobs execute $POPULATE_JOB \
    --region=$REGION \
    --wait \
    --quiet

/opt/google-cloud-sdk/bin/gcloud run jobs delete $POPULATE_JOB \
    --region=$REGION \
    --quiet

# Health check
log_info "Performing health check..."
if curl -f "$SERVICE_URL/health/" > /dev/null 2>&1; then
    log_info "✅ Health check passed!"
else
    log_warning "⚠️ Health check failed - service may still be starting"
fi

# Final summary
log_info "🎉 Deployment completed!"
echo ""
echo "Service URL: $SERVICE_URL"
echo "GraphQL API: $SERVICE_URL/graphql/"
echo "Admin credentials: admin@example.com / admin"
echo ""
echo "Next steps:"
echo "1. Test the GraphQL API at $SERVICE_URL/graphql/"
echo "2. Configure your domain name"
echo "3. Set up SSL certificate"
echo "4. Configure monitoring and alerting"