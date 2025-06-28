#!/bin/bash
# Comprehensive cleanup script for all Google Cloud regions

echo "=============================================="
echo "Multi-Region Cleanup Script"
echo "Project: melodic-now-463704-k1"
echo "=============================================="
echo ""

# Authenticate first
echo "Please ensure you're authenticated:"
echo "  gcloud auth login"
echo "  gcloud config set project melodic-now-463704-k1"
echo ""
echo "This script will delete ALL Saleor resources in ALL regions!"
echo "Press Enter to continue or Ctrl+C to cancel..."
read

# Set project
gcloud config set project melodic-now-463704-k1

# All major regions
ALL_REGIONS=(
    "us-central1" "us-east1" "us-east4" "us-west1" "us-west2" "us-west3" "us-west4"
    "europe-west1" "europe-west2" "europe-west3" "europe-west4" "europe-west6" "europe-north1"
    "asia-east1" "asia-east2" "asia-northeast1" "asia-northeast2" "asia-northeast3"
    "asia-south1" "asia-southeast1" "asia-southeast2"
    "australia-southeast1" "northamerica-northeast1" "southamerica-east1"
)

echo "=== GLOBAL RESOURCE CLEANUP ==="
echo ""

echo "1. Deleting Cloud SQL Instances..."
for instance in $(gcloud sql instances list --format="value(name)" 2>/dev/null | grep "saleor"); do
    echo "Deleting SQL instance: $instance"
    gcloud sql instances delete $instance --quiet
done

echo "2. Deleting Storage Buckets..."
for bucket in $(gcloud storage buckets list --format="value(name)" 2>/dev/null | grep "saleor"); do
    echo "Deleting bucket: $bucket"
    gcloud storage rm -r gs://$bucket --quiet 2>/dev/null || true
done

echo "3. Deleting Global Load Balancer Components..."
# Global forwarding rules
for rule in $(gcloud compute forwarding-rules list --global --format="value(name)" 2>/dev/null | grep "saleor"); do
    echo "Deleting global forwarding rule: $rule"
    gcloud compute forwarding-rules delete $rule --global --quiet
done

# Target HTTPS proxies
for proxy in $(gcloud compute target-https-proxies list --format="value(name)" 2>/dev/null | grep "saleor"); do
    echo "Deleting target HTTPS proxy: $proxy"
    gcloud compute target-https-proxies delete $proxy --quiet
done

# URL maps
for urlmap in $(gcloud compute url-maps list --format="value(name)" 2>/dev/null | grep "saleor"); do
    echo "Deleting URL map: $urlmap"
    gcloud compute url-maps delete $urlmap --quiet
done

# Backend services
for backend in $(gcloud compute backend-services list --global --format="value(name)" 2>/dev/null | grep "saleor"); do
    echo "Deleting backend service: $backend"
    gcloud compute backend-services delete $backend --global --quiet
done

# Health checks
for healthcheck in $(gcloud compute health-checks list --format="value(name)" 2>/dev/null | grep "saleor"); do
    echo "Deleting health check: $healthcheck"
    gcloud compute health-checks delete $healthcheck --quiet
done

# SSL certificates
for cert in $(gcloud compute ssl-certificates list --format="value(name)" 2>/dev/null | grep "saleor"); do
    echo "Deleting SSL certificate: $cert"
    gcloud compute ssl-certificates delete $cert --quiet
done

# Global IP addresses
for ip in $(gcloud compute addresses list --global --format="value(name)" 2>/dev/null | grep "saleor"); do
    echo "Deleting global IP: $ip"
    gcloud compute addresses delete $ip --global --quiet
done

echo "4. Deleting VPC Networks..."
for network in $(gcloud compute networks list --format="value(name)" 2>/dev/null | grep "saleor"); do
    # Delete subnets first
    for subnet in $(gcloud compute networks subnets list --network=$network --format="value(name,region)" 2>/dev/null); do
        subnet_name=$(echo $subnet | awk '{print $1}')
        subnet_region=$(echo $subnet | awk '{print $2}')
        echo "Deleting subnet: $subnet_name in $subnet_region"
        gcloud compute networks subnets delete $subnet_name --region=$subnet_region --quiet
    done
    echo "Deleting network: $network"
    gcloud compute networks delete $network --quiet
done

echo "5. Deleting Service Accounts..."
for sa in $(gcloud iam service-accounts list --format="value(email)" 2>/dev/null | grep "saleor"); do
    echo "Deleting service account: $sa"
    gcloud iam service-accounts delete $sa --quiet
done

echo "6. Deleting Secrets..."
for secret in $(gcloud secrets list --format="value(name)" 2>/dev/null | grep "saleor"); do
    echo "Deleting secret: $secret"
    gcloud secrets delete $secret --quiet
done

echo ""
echo "=== REGIONAL RESOURCE CLEANUP ==="
echo ""

for region in "${ALL_REGIONS[@]}"; do
    echo "Processing region: $region"
    echo "-------------------------"
    
    # Cloud Run Services
    services=$(gcloud run services list --region=$region --format="value(name)" 2>/dev/null | grep "saleor" || true)
    for service in $services; do
        echo "Deleting Cloud Run service: $service in $region"
        gcloud run services delete $service --region=$region --quiet
    done
    
    # Cloud Run Jobs
    jobs=$(gcloud run jobs list --region=$region --format="value(name)" 2>/dev/null | grep "saleor" || true)
    for job in $jobs; do
        echo "Deleting Cloud Run job: $job in $region"
        gcloud run jobs delete $job --region=$region --quiet
    done
    
    # Redis Instances
    redis_instances=$(gcloud redis instances list --region=$region --format="value(name)" 2>/dev/null | grep "saleor" || true)
    for redis in $redis_instances; do
        echo "Deleting Redis instance: $redis in $region"
        gcloud redis instances delete $redis --region=$region --quiet
    done
    
    # Artifact Registry Repositories
    repositories=$(gcloud artifacts repositories list --location=$region --format="value(name)" 2>/dev/null | grep "saleor" || true)
    for repo in $repositories; do
        echo "Deleting Artifact Registry repository: $repo in $region"
        gcloud artifacts repositories delete $repo --location=$region --quiet
    done
    
    # VPC Access Connectors
    connectors=$(gcloud compute networks vpc-access connectors list --region=$region --format="value(name)" 2>/dev/null | grep "saleor" || true)
    for connector in $connectors; do
        echo "Deleting VPC connector: $connector in $region"
        gcloud compute networks vpc-access connectors delete $connector --region=$region --quiet
    done
    
    # GKE Clusters
    clusters=$(gcloud container clusters list --region=$region --format="value(name)" 2>/dev/null | grep "saleor" || true)
    for cluster in $clusters; do
        echo "Deleting GKE cluster: $cluster in $region"
        gcloud container clusters delete $cluster --region=$region --quiet
    done
    
    # Compute Engine Instances (check zones in region)
    zones=$(gcloud compute zones list --filter="region:$region" --format="value(name)" 2>/dev/null || true)
    for zone in $zones; do
        instances=$(gcloud compute instances list --zones=$zone --format="value(name)" 2>/dev/null | grep "saleor" || true)
        for instance in $instances; do
            echo "Deleting Compute Engine instance: $instance in $zone"
            gcloud compute instances delete $instance --zone=$zone --quiet
        done
    done
    
    echo ""
done

echo "=============================================="
echo "Multi-Region Cleanup Complete"
echo "=============================================="
echo ""
echo "Verification commands:"
echo "  ./quick-multi-region-check.sh"
echo "  ./check-all-regions.sh"
echo ""
echo "Note: Some resources may take a few minutes to fully delete."