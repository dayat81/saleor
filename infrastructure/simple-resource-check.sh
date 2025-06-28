#!/bin/bash
# Simple resource check without complex loops

echo "=============================================="
echo "Simple Multi-Region Resource Check"
echo "Project: melodic-now-463704-k1"
echo "=============================================="
echo ""

gcloud config set project melodic-now-463704-k1 2>/dev/null

echo "=== CHECKING GLOBAL RESOURCES ==="
echo ""

echo "1. Cloud SQL Instances:"
gcloud sql instances list 2>&1 | grep -E "(NAME|saleor|Listed 0)" || echo "❌ Auth error or no instances"
echo ""

echo "2. Storage Buckets:"
gcloud storage buckets list 2>&1 | grep -E "(NAME|saleor)" || echo "✅ No Saleor buckets found"
echo ""

echo "3. VPC Networks:" 
gcloud compute networks list 2>&1 | grep -E "(NAME|saleor)" || echo "✅ No Saleor networks found"
echo ""

echo "4. Global Load Balancers:"
gcloud compute forwarding-rules list --global 2>&1 | grep -E "(NAME|saleor)" || echo "✅ No Saleor forwarding rules found"
echo ""

echo "5. SSL Certificates:"
gcloud compute ssl-certificates list 2>&1 | grep -E "(NAME|saleor)" || echo "✅ No Saleor SSL certificates found"
echo ""

echo "6. Service Accounts:"
gcloud iam service-accounts list 2>&1 | grep -E "(EMAIL|saleor)" || echo "✅ No Saleor service accounts found"
echo ""

echo "7. Secrets:"
gcloud secrets list 2>&1 | grep -E "(NAME|saleor)" || echo "✅ No Saleor secrets found"
echo ""

echo "=== CHECKING KEY REGIONS ==="
echo ""

# Check Indonesia region specifically
echo "8. Cloud Run in Indonesia (asia-southeast2):"
gcloud run services list --region=asia-southeast2 2>&1 | grep -E "(NAME|saleor)" || echo "✅ No Saleor services in Indonesia"
gcloud run jobs list --region=asia-southeast2 2>&1 | grep -E "(NAME|saleor)" || echo "✅ No Saleor jobs in Indonesia"
echo ""

echo "9. Redis in Indonesia (asia-southeast2):"
gcloud redis instances list --region=asia-southeast2 2>&1 | grep -E "(NAME|saleor)" || echo "✅ No Saleor Redis in Indonesia"
echo ""

echo "10. Artifact Registry in Indonesia (asia-southeast2):"
gcloud artifacts repositories list --location=asia-southeast2 2>&1 | grep -E "(NAME|saleor)" || echo "✅ No Saleor registries in Indonesia"
echo ""

# Check US Central region
echo "11. Cloud Run in US Central (us-central1):"
gcloud run services list --region=us-central1 2>&1 | grep -E "(NAME|saleor)" || echo "✅ No Saleor services in US Central"
echo ""

echo "12. Redis in US Central (us-central1):"
gcloud redis instances list --region=us-central1 2>&1 | grep -E "(NAME|saleor)" || echo "✅ No Saleor Redis in US Central"
echo ""

echo "=============================================="
echo "Quick Check Complete"
echo "=============================================="
echo ""

# Count any resources found
total_found=0
if gcloud sql instances list 2>/dev/null | grep -q "saleor"; then
    total_found=$((total_found + 1))
fi
if gcloud storage buckets list 2>/dev/null | grep -q "saleor"; then
    total_found=$((total_found + 1))
fi
if gcloud compute networks list 2>/dev/null | grep -q "saleor"; then
    total_found=$((total_found + 1))
fi

if [ "$total_found" -eq 0 ]; then
    echo "🎉 EXCELLENT: No Saleor resources found!"
    echo "✅ Infrastructure appears to be completely clean"
else
    echo "⚠️  Found some Saleor resources"
    echo "📋 Consider running cleanup script if needed"
fi

echo ""
echo "For comprehensive check: ./check-all-regions.sh"
echo "For cleanup: ./cleanup-all-regions.sh"