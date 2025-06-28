#!/bin/bash

# Script to update Kubernetes manifests with actual values from Terraform
# Usage: ./update-k8s-manifests.sh

set -e

# Get values from terraform.tfvars
PROJECT_ID=$(grep "project_id" terraform.tfvars | cut -d'"' -f2)
REGION=$(grep "region" terraform.tfvars | cut -d'"' -f2)
DOMAIN_NAME=$(grep "domain_name" terraform.tfvars | cut -d'"' -f2)

# Get suffix from terraform state
SUFFIX=$(terraform show -json | jq -r '.values.outputs.gke_cluster_name.value' | sed 's/saleor-gke-//')

if [ -z "$SUFFIX" ]; then
    echo "Warning: Could not get suffix from terraform state, using placeholder"
    SUFFIX="SUFFIX"
fi

echo "Using values:"
echo "  PROJECT_ID: $PROJECT_ID"
echo "  REGION: $REGION"
echo "  DOMAIN_NAME: $DOMAIN_NAME"
echo "  SUFFIX: $SUFFIX"

# Create updated manifests
cp k8s-manifests.yaml k8s-manifests-updated.yaml

# Replace placeholders
sed -i "s/PROJECT_ID/$PROJECT_ID/g" k8s-manifests-updated.yaml
sed -i "s/REGION/$REGION/g" k8s-manifests-updated.yaml
sed -i "s/SUFFIX/$SUFFIX/g" k8s-manifests-updated.yaml
sed -i "s/DOMAIN_NAME/$DOMAIN_NAME/g" k8s-manifests-updated.yaml

# Get bucket names from terraform if available
if command -v terraform &> /dev/null && terraform state list | grep -q google_storage_bucket; then
    STATIC_BUCKET=$(terraform show -json | jq -r '.values.outputs.static_bucket_name.value // "saleor-static-bucket"')
    MEDIA_BUCKET=$(terraform show -json | jq -r '.values.outputs.media_bucket_name.value // "saleor-media-bucket"')
    PRIVATE_BUCKET=$(terraform show -json | jq -r '.values.outputs.private_bucket_name.value // "saleor-private-bucket"')
    
    sed -i "s/STATIC_BUCKET/$STATIC_BUCKET/g" k8s-manifests-updated.yaml
    sed -i "s/MEDIA_BUCKET/$MEDIA_BUCKET/g" k8s-manifests-updated.yaml
    sed -i "s/PRIVATE_BUCKET/$PRIVATE_BUCKET/g" k8s-manifests-updated.yaml
else
    echo "Warning: Terraform state not available, using placeholder bucket names"
    sed -i "s/STATIC_BUCKET/saleor-static-$PROJECT_ID-$SUFFIX/g" k8s-manifests-updated.yaml
    sed -i "s/MEDIA_BUCKET/saleor-media-$PROJECT_ID-$SUFFIX/g" k8s-manifests-updated.yaml
    sed -i "s/PRIVATE_BUCKET/saleor-private-$PROJECT_ID-$SUFFIX/g" k8s-manifests-updated.yaml
fi

echo "Updated manifests created: k8s-manifests-updated.yaml"
echo ""
echo "Next steps:"
echo "1. Review the updated manifests"
echo "2. Update the secrets with actual database and Redis connection strings"
echo "3. Deploy: kubectl apply -f k8s-manifests-updated.yaml"