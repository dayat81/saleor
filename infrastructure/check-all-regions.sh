#!/bin/bash
# Comprehensive check for Google Cloud resources in ALL regions

echo "=============================================="
echo "Checking Google Cloud Resources in ALL Regions"
echo "Project: melodic-now-463704-k1"
echo "=============================================="
echo ""

# Set project
gcloud config set project melodic-now-463704-k1 2>/dev/null

# Define major regions to check
REGIONS=(
    "us-central1"
    "us-east1" 
    "us-east4"
    "us-west1"
    "us-west2"
    "us-west3"
    "us-west4"
    "europe-west1"
    "europe-west2"
    "europe-west3"
    "europe-west4"
    "europe-west6"
    "europe-north1"
    "asia-east1"
    "asia-east2"
    "asia-northeast1"
    "asia-northeast2"
    "asia-northeast3"
    "asia-south1"
    "asia-southeast1"
    "asia-southeast2"
    "australia-southeast1"
    "northamerica-northeast1"
    "southamerica-east1"
)

echo "=== GLOBAL RESOURCES ==="
echo ""

echo "1. Cloud SQL Instances (Global):"
echo "--------------------------------"
FOUND_SQL=false
gcloud sql instances list --format="table(name,region,database_version,status)" 2>&1 | while read line; do
    if [[ $line == *"saleor"* ]] || [[ $line == *"NAME"* ]] || [[ $line == *"Listed 0 items"* ]]; then
        echo "$line"
        if [[ $line == *"saleor"* ]]; then
            FOUND_SQL=true
        fi
    fi
done
echo ""

echo "2. Storage Buckets (Global):"
echo "---------------------------"
FOUND_BUCKETS=false
gcloud storage buckets list --format="table(name,location,storage_class)" 2>&1 | while read line; do
    if [[ $line == *"saleor"* ]] || [[ $line == *"NAME"* ]]; then
        echo "$line"
        if [[ $line == *"saleor"* ]]; then
            FOUND_BUCKETS=true
        fi
    fi
done
if ! gcloud storage buckets list 2>&1 | grep -q "saleor"; then
    echo "✅ No Saleor buckets found"
fi
echo ""

echo "3. Global VPC Networks:"
echo "----------------------"
FOUND_NETWORKS=false
gcloud compute networks list --format="table(name,subnet_mode,bgp_routing_mode)" 2>&1 | while read line; do
    if [[ $line == *"saleor"* ]] || [[ $line == *"NAME"* ]]; then
        echo "$line"
        if [[ $line == *"saleor"* ]]; then
            FOUND_NETWORKS=true
        fi
    fi
done
if ! gcloud compute networks list 2>&1 | grep -q "saleor"; then
    echo "✅ No Saleor networks found"
fi
echo ""

echo "4. Global Load Balancers:"
echo "------------------------"
echo "Global Forwarding Rules:"
gcloud compute forwarding-rules list --global --format="table(name,target,ip_address)" 2>&1 | grep -E "(NAME|saleor)" || echo "✅ No Saleor forwarding rules found"
echo ""

echo "SSL Certificates:"
gcloud compute ssl-certificates list --format="table(name,domains,expire_time)" 2>&1 | grep -E "(NAME|saleor)" || echo "✅ No Saleor SSL certificates found"
echo ""

echo "5. IAM Service Accounts:"
echo "------------------------"
gcloud iam service-accounts list --format="table(email,display_name)" 2>&1 | grep -E "(EMAIL|saleor)" || echo "✅ No Saleor service accounts found"
echo ""

echo "6. Secret Manager Secrets:"
echo "-------------------------"
gcloud secrets list --format="table(name,created)" 2>&1 | grep -E "(NAME|saleor)" || echo "✅ No Saleor secrets found"
echo ""

echo "=== REGIONAL RESOURCES ==="
echo ""

echo "7. Cloud Run Services by Region:"
echo "--------------------------------"
FOUND_SERVICES=false
for region in "${REGIONS[@]}"; do
    services=$(gcloud run services list --region=$region --format="value(name)" 2>/dev/null | grep -E "saleor" || true)
    if [[ -n "$services" ]]; then
        echo "🔍 Found services in $region:"
        echo "$services" | while read service; do
            echo "  - $service"
        done
        FOUND_SERVICES=true
    fi
done
if [[ $FOUND_SERVICES == false ]]; then
    echo "✅ No Saleor Cloud Run services found in any region"
fi
echo ""

echo "8. Cloud Run Jobs by Region:"
echo "----------------------------"
FOUND_JOBS=false
for region in "${REGIONS[@]}"; do
    jobs=$(gcloud run jobs list --region=$region --format="value(name)" 2>/dev/null | grep -E "saleor" || true)
    if [[ -n "$jobs" ]]; then
        echo "🔍 Found jobs in $region:"
        echo "$jobs" | while read job; do
            echo "  - $job"
        done
        FOUND_JOBS=true
    fi
done
if [[ $FOUND_JOBS == false ]]; then
    echo "✅ No Saleor Cloud Run jobs found in any region"
fi
echo ""

echo "9. Redis Instances by Region:"
echo "-----------------------------"
FOUND_REDIS=false
for region in "${REGIONS[@]}"; do
    redis=$(gcloud redis instances list --region=$region --format="value(name)" 2>/dev/null | grep -E "saleor" || true)
    if [[ -n "$redis" ]]; then
        echo "🔍 Found Redis instances in $region:"
        echo "$redis" | while read instance; do
            echo "  - $instance"
        done
        FOUND_REDIS=true
    fi
done
if [[ $FOUND_REDIS == false ]]; then
    echo "✅ No Saleor Redis instances found in any region"
fi
echo ""

echo "10. Artifact Registry by Region:"
echo "--------------------------------"
FOUND_REGISTRIES=false
for region in "${REGIONS[@]}"; do
    registries=$(gcloud artifacts repositories list --location=$region --format="value(name)" 2>/dev/null | grep -E "saleor" || true)
    if [[ -n "$registries" ]]; then
        echo "🔍 Found registries in $region:"
        echo "$registries" | while read registry; do
            echo "  - $registry"
        done
        FOUND_REGISTRIES=true
    fi
done
if [[ $FOUND_REGISTRIES == false ]]; then
    echo "✅ No Saleor Artifact Registry repositories found in any region"
fi
echo ""

echo "11. VPC Access Connectors by Region:"
echo "------------------------------------"
FOUND_CONNECTORS=false
for region in "${REGIONS[@]}"; do
    connectors=$(gcloud compute networks vpc-access connectors list --region=$region --format="value(name)" 2>/dev/null | grep -E "saleor" || true)
    if [[ -n "$connectors" ]]; then
        echo "🔍 Found VPC connectors in $region:"
        echo "$connectors" | while read connector; do
            echo "  - $connector"
        done
        FOUND_CONNECTORS=true
    fi
done
if [[ $FOUND_CONNECTORS == false ]]; then
    echo "✅ No Saleor VPC connectors found in any region"
fi
echo ""

echo "12. Compute Engine Instances by Region:"
echo "---------------------------------------"
FOUND_INSTANCES=false
for region in "${REGIONS[@]}"; do
    # Check zones in this region
    zones=$(gcloud compute zones list --filter="region:$region" --format="value(name)" 2>/dev/null || true)
    for zone in $zones; do
        instances=$(gcloud compute instances list --zones=$zone --format="value(name)" 2>/dev/null | grep -E "saleor" || true)
        if [[ -n "$instances" ]]; then
            echo "🔍 Found instances in $zone:"
            echo "$instances" | while read instance; do
                echo "  - $instance"
            done
            FOUND_INSTANCES=true
        fi
    done
done
if [[ $FOUND_INSTANCES == false ]]; then
    echo "✅ No Saleor Compute Engine instances found in any region"
fi
echo ""

echo "13. GKE Clusters by Region:"
echo "---------------------------"
FOUND_CLUSTERS=false
for region in "${REGIONS[@]}"; do
    clusters=$(gcloud container clusters list --region=$region --format="value(name)" 2>/dev/null | grep -E "saleor" || true)
    if [[ -n "$clusters" ]]; then
        echo "🔍 Found GKE clusters in $region:"
        echo "$clusters" | while read cluster; do
            echo "  - $cluster"
        done
        FOUND_CLUSTERS=true
    fi
done
if [[ $FOUND_CLUSTERS == false ]]; then
    echo "✅ No Saleor GKE clusters found in any region"
fi
echo ""

echo "=============================================="
echo "Multi-Region Resource Check Complete"
echo "=============================================="
echo ""
echo "If you found any resources above, run the cleanup script:"
echo "  ./cleanup-all-regions.sh"
echo ""
echo "To check specific regions only:"
echo "  gcloud run services list --region=REGION_NAME"
echo "  gcloud redis instances list --region=REGION_NAME"
echo "  gcloud artifacts repositories list --location=REGION_NAME"