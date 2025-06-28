#!/bin/bash
# Check all Google Cloud resources in Indonesia region (asia-southeast2)

echo "========================================="
echo "Checking Google Cloud Resources in Indonesia Region"
echo "Project: melodic-now-463704-k1"
echo "Region: asia-southeast2"
echo "========================================="
echo ""

# Set project
gcloud config set project melodic-now-463704-k1 2>/dev/null

echo "1. Cloud Run Services in asia-southeast2:"
echo "-----------------------------------------"
gcloud run services list --region=asia-southeast2 2>&1 | grep -E "(NAME|saleor|No services|UNAUTHENTICATED)" || echo "Error checking services"
echo ""

echo "2. Cloud Run Jobs in asia-southeast2:"
echo "------------------------------------"
gcloud run jobs list --region=asia-southeast2 2>&1 | grep -E "(NAME|saleor|No jobs|UNAUTHENTICATED)" || echo "Error checking jobs"
echo ""

echo "3. Cloud SQL Instances:"
echo "----------------------"
gcloud sql instances list 2>&1 | grep -E "(NAME|saleor|Listed 0 items|UNAUTHENTICATED)" || echo "Error checking SQL instances"
echo ""

echo "4. Redis Instances in asia-southeast2:"
echo "-------------------------------------"
gcloud redis instances list --region=asia-southeast2 2>&1 | grep -E "(NAME|saleor|Listed 0 items|UNAUTHENTICATED)" || echo "Error checking Redis instances"
echo ""

echo "5. Storage Buckets with 'saleor' prefix:"
echo "---------------------------------------"
gcloud storage buckets list 2>&1 | grep -E "(saleor|Listed 0 items|UNAUTHENTICATED)" || echo "No saleor buckets found"
echo ""

echo "6. Artifact Registries in asia-southeast2:"
echo "-----------------------------------------"
gcloud artifacts repositories list --location=asia-southeast2 2>&1 | grep -E "(NAME|saleor|Listed 0 items|UNAUTHENTICATED)" || echo "Error checking registries"
echo ""

echo "7. VPC Networks:"
echo "---------------"
gcloud compute networks list 2>&1 | grep -E "(NAME|saleor|Listed 0 items|UNAUTHENTICATED)" || echo "Error checking networks"
echo ""

echo "8. Load Balancers:"
echo "-----------------"
gcloud compute forwarding-rules list --global 2>&1 | grep -E "(NAME|saleor|Listed 0 items|UNAUTHENTICATED)" || echo "Error checking load balancers"
echo ""

echo "9. SSL Certificates:"
echo "-------------------"
gcloud compute ssl-certificates list 2>&1 | grep -E "(NAME|saleor|Listed 0 items|UNAUTHENTICATED)" || echo "Error checking SSL certificates"
echo ""

echo "10. Service Accounts:"
echo "--------------------"
gcloud iam service-accounts list 2>&1 | grep -E "(saleor|UNAUTHENTICATED)" || echo "No saleor service accounts found"
echo ""

echo "11. Secrets:"
echo "-----------"
gcloud secrets list 2>&1 | grep -E "(NAME|saleor|Listed 0 items|UNAUTHENTICATED)" || echo "Error checking secrets"
echo ""

echo "12. VPC Access Connectors in asia-southeast2:"
echo "--------------------------------------------"
gcloud compute networks vpc-access connectors list --region=asia-southeast2 2>&1 | grep -E "(NAME|saleor|Listed 0 items|UNAUTHENTICATED)" || echo "Error checking VPC connectors"
echo ""

echo "13. Service Networking Connections:"
echo "----------------------------------"
gcloud services vpc-peerings list --network=default 2>&1 | grep -E "(NAME|saleor|UNAUTHENTICATED)" || echo "Error checking service connections"
echo ""

echo "========================================="
echo "Cleanup Verification Complete"
echo "========================================="
echo ""
echo "Note: If you see UNAUTHENTICATED errors, you need to run:"
echo "  gcloud auth login"
echo "  gcloud config set project melodic-now-463704-k1"