#!/bin/bash

# Script to show Docker images available in Google Cloud Artifact Registry
# Author: Generated for Saleor infrastructure
# Date: 2025-06-28

set -e

echo "🐳 Google Cloud Docker Images Status"
echo "===================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get project info
PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "unknown")
REGION="us-central1"
REPO_NAME="saleor-33b5604e"

echo -e "${BLUE}Project ID:${NC} $PROJECT_ID"
echo -e "${BLUE}Region:${NC} $REGION"
echo -e "${BLUE}Repository:${NC} $REPO_NAME"
echo

# Check if Artifact Registry repository exists
echo "🔍 Checking Artifact Registry repository..."
if gcloud artifacts repositories describe "$REPO_NAME" --location="$REGION" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Repository '$REPO_NAME' exists${NC}"
    
    # Get repository details
    echo
    echo "📋 Repository Details:"
    gcloud artifacts repositories describe "$REPO_NAME" --location="$REGION" \
        --format="table(name,format,createTime)" 2>/dev/null || true
    
else
    echo -e "${RED}❌ Repository '$REPO_NAME' not found${NC}"
    echo "Creating repository would require: gcloud artifacts repositories create $REPO_NAME --location=$REGION --repository-format=docker"
    exit 1
fi

echo
echo "🖼️  Available Docker Images:"
echo "=============================="

# List all images in the repository
IMAGES=$(gcloud artifacts docker images list "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME" \
    --format="value(IMAGE)" 2>/dev/null || echo "")

if [ -z "$IMAGES" ]; then
    echo -e "${YELLOW}⚠️  No Docker images found in repository${NC}"
    echo
    echo "To push an image:"
    echo "  1. Build: docker build -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/saleor:latest ."
    echo "  2. Push:  docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/saleor:latest"
else
    echo -e "${GREEN}Found images:${NC}"
    echo "$IMAGES"
    echo
    
    # Show detailed image information
    echo "📊 Image Details:"
    echo "=================="
    gcloud artifacts docker images list "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME" \
        --format="table(IMAGE,TAGS,CREATE_TIME,UPDATE_TIME)" 2>/dev/null || echo "No detailed info available"
fi

echo
echo "🔗 Useful Commands:"
echo "==================="
echo "Configure Docker auth:"
echo "  gcloud auth configure-docker $REGION-docker.pkg.dev"
echo
echo "Pull image (if exists):"
echo "  docker pull $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/saleor:latest"
echo
echo "Push new image:"
echo "  docker tag YOUR_LOCAL_IMAGE $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/saleor:latest"
echo "  docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/saleor:latest"
echo
echo "🌐 View in Console:"
echo "https://console.cloud.google.com/artifacts/docker/$PROJECT_ID/$REGION/$REPO_NAME?project=$PROJECT_ID"