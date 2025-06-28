#!/bin/bash
# Quick check for Google Cloud resources in key regions

echo "=============================================="
echo "Quick Multi-Region Resource Check"
echo "Project: melodic-now-463704-k1"
echo "=============================================="
echo ""

# Set project
gcloud config set project melodic-now-463704-k1 2>/dev/null

# Key regions to check (reduced list)
KEY_REGIONS=(
    "us-central1"
    "us-east1" 
    "europe-west1"
    "asia-east1"
    "asia-southeast1"
    "asia-southeast2"
)

echo "=== GLOBAL RESOURCES ==="
echo ""

echo "1. Cloud SQL Instances:"
echo "----------------------"
sql_count=$(gcloud sql instances list --format="value(name)" 2>/dev/null | grep -c "saleor" || echo "0")
echo "Saleor SQL instances found: $sql_count"
if [ "$sql_count" -gt 0 ]; then
    gcloud sql instances list --format="table(name,region,status)" 2>/dev/null | grep -E "(NAME|saleor)"
fi
echo ""

echo "2. Storage Buckets:"
echo "------------------"
bucket_count=$(gcloud storage buckets list --format="value(name)" 2>/dev/null | grep -c "saleor" || echo "0")
echo "Saleor buckets found: $bucket_count"
if [ "$bucket_count" -gt 0 ]; then
    gcloud storage buckets list --format="table(name,location)" 2>/dev/null | grep -E "(NAME|saleor)"
fi
echo ""

echo "3. Global Networking:"
echo "--------------------"
network_count=$(gcloud compute networks list --format="value(name)" 2>/dev/null | grep -c "saleor" || echo "0")
lb_count=$(gcloud compute forwarding-rules list --global --format="value(name)" 2>/dev/null | grep -c "saleor" || echo "0")
cert_count=$(gcloud compute ssl-certificates list --format="value(name)" 2>/dev/null | grep -c "saleor" || echo "0")
echo "Saleor networks: $network_count"
echo "Saleor load balancers: $lb_count" 
echo "Saleor SSL certificates: $cert_count"
echo ""

echo "4. Service Accounts & Secrets:"
echo "------------------------------"
sa_count=$(gcloud iam service-accounts list --format="value(email)" 2>/dev/null | grep -c "saleor" || echo "0")
secret_count=$(gcloud secrets list --format="value(name)" 2>/dev/null | grep -c "saleor" || echo "0")
echo "Saleor service accounts: $sa_count"
echo "Saleor secrets: $secret_count"
echo ""

echo "=== REGIONAL RESOURCES ==="
echo ""

total_services=0
total_jobs=0
total_redis=0
total_registries=0

for region in "${KEY_REGIONS[@]}"; do
    echo "Region: $region"
    echo "----------------"
    
    # Cloud Run Services
    services=$(gcloud run services list --region=$region --format="value(name)" 2>/dev/null | grep -c "saleor" || echo "0")
    total_services=$((total_services + services))
    
    # Cloud Run Jobs  
    jobs=$(gcloud run jobs list --region=$region --format="value(name)" 2>/dev/null | grep -c "saleor" || echo "0")
    total_jobs=$((total_jobs + jobs))
    
    # Redis
    redis=$(gcloud redis instances list --region=$region --format="value(name)" 2>/dev/null | grep -c "saleor" || echo "0")
    total_redis=$((total_redis + redis))
    
    # Artifact Registry
    registries=$(gcloud artifacts repositories list --location=$region --format="value(name)" 2>/dev/null | grep -c "saleor" || echo "0")
    total_registries=$((total_registries + registries))
    
    echo "  Services: $services | Jobs: $jobs | Redis: $redis | Registries: $registries"
    
    # Show details if found
    if [ "$services" -gt 0 ]; then
        echo "  🔍 Services found:"
        gcloud run services list --region=$region --format="value(name)" 2>/dev/null | grep "saleor" | sed 's/^/    - /'
    fi
    if [ "$jobs" -gt 0 ]; then
        echo "  🔍 Jobs found:"
        gcloud run jobs list --region=$region --format="value(name)" 2>/dev/null | grep "saleor" | sed 's/^/    - /'
    fi
    if [ "$redis" -gt 0 ]; then
        echo "  🔍 Redis found:"
        gcloud redis instances list --region=$region --format="value(name)" 2>/dev/null | grep "saleor" | sed 's/^/    - /'
    fi
    if [ "$registries" -gt 0 ]; then
        echo "  🔍 Registries found:"
        gcloud artifacts repositories list --location=$region --format="value(name)" 2>/dev/null | grep "saleor" | sed 's/^/    - /'
    fi
    echo ""
done

echo "=============================================="
echo "SUMMARY"
echo "=============================================="
echo ""
echo "Global Resources:"
echo "  - SQL Instances: $sql_count"
echo "  - Storage Buckets: $bucket_count" 
echo "  - VPC Networks: $network_count"
echo "  - Load Balancers: $lb_count"
echo "  - SSL Certificates: $cert_count"
echo "  - Service Accounts: $sa_count"
echo "  - Secrets: $secret_count"
echo ""
echo "Regional Resources (total across key regions):"
echo "  - Cloud Run Services: $total_services"
echo "  - Cloud Run Jobs: $total_jobs"
echo "  - Redis Instances: $total_redis"
echo "  - Artifact Registries: $total_registries"
echo ""

# Calculate total resources
total_resources=$((sql_count + bucket_count + network_count + lb_count + cert_count + sa_count + secret_count + total_services + total_jobs + total_redis + total_registries))

if [ "$total_resources" -eq 0 ]; then
    echo "🎉 SUCCESS: No Saleor resources found in any region!"
    echo "✅ Infrastructure is completely clean"
else
    echo "⚠️  WARNING: Found $total_resources Saleor resources"
    echo "📋 Run cleanup script to remove remaining resources"
fi

echo ""
echo "To check additional regions or resources:"
echo "  ./check-all-regions.sh"