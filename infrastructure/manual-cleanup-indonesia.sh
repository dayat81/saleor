#!/bin/bash
# Manual cleanup script for any remaining Google Cloud resources in Indonesia region

echo "========================================="
echo "Manual Cleanup Script for Indonesia Region"
echo "Project: melodic-now-463704-k1"
echo "Region: asia-southeast2"
echo "========================================="
echo ""

# You need to authenticate first
echo "Please ensure you're authenticated:"
echo "  gcloud auth login"
echo "  gcloud config set project melodic-now-463704-k1"
echo ""
echo "Press Enter to continue after authentication..."
read

# Set project
gcloud config set project melodic-now-463704-k1

# 1. Delete Cloud Run services
echo "Deleting Cloud Run services in asia-southeast2..."
for service in $(gcloud run services list --region=asia-southeast2 --format="value(name)" 2>/dev/null | grep -E "saleor"); do
    echo "Deleting service: $service"
    gcloud run services delete $service --region=asia-southeast2 --quiet
done

# 2. Delete Cloud Run jobs
echo "Deleting Cloud Run jobs in asia-southeast2..."
for job in $(gcloud run jobs list --region=asia-southeast2 --format="value(name)" 2>/dev/null | grep -E "saleor"); do
    echo "Deleting job: $job"
    gcloud run jobs delete $job --region=asia-southeast2 --quiet
done

# 3. Delete Cloud SQL instances
echo "Deleting Cloud SQL instances..."
for instance in $(gcloud sql instances list --format="value(name)" 2>/dev/null | grep -E "saleor"); do
    echo "Deleting SQL instance: $instance"
    gcloud sql instances delete $instance --quiet
done

# 4. Delete Redis instances
echo "Deleting Redis instances in asia-southeast2..."
for instance in $(gcloud redis instances list --region=asia-southeast2 --format="value(name)" 2>/dev/null | grep -E "saleor"); do
    echo "Deleting Redis instance: $instance"
    gcloud redis instances delete $instance --region=asia-southeast2 --quiet
done

# 5. Delete Storage buckets
echo "Deleting Storage buckets..."
for bucket in $(gcloud storage buckets list --format="value(name)" 2>/dev/null | grep -E "saleor"); do
    echo "Deleting bucket: $bucket"
    gcloud storage rm -r gs://$bucket --quiet
done

# 6. Delete Artifact Registry repositories
echo "Deleting Artifact Registry repositories in asia-southeast2..."
for repo in $(gcloud artifacts repositories list --location=asia-southeast2 --format="value(name)" 2>/dev/null | grep -E "saleor"); do
    echo "Deleting repository: $repo"
    gcloud artifacts repositories delete $repo --location=asia-southeast2 --quiet
done

# 7. Delete VPC networks
echo "Deleting VPC networks..."
for network in $(gcloud compute networks list --format="value(name)" 2>/dev/null | grep -E "saleor"); do
    # First delete associated subnets
    for subnet in $(gcloud compute networks subnets list --network=$network --format="value(name)" 2>/dev/null); do
        region=$(gcloud compute networks subnets list --network=$network --format="value(region)" 2>/dev/null | head -1)
        echo "Deleting subnet: $subnet in region: $region"
        gcloud compute networks subnets delete $subnet --region=$region --quiet
    done
    echo "Deleting network: $network"
    gcloud compute networks delete $network --quiet
done

# 8. Delete Load Balancers and related resources
echo "Deleting Load Balancer resources..."
# Forwarding rules
for rule in $(gcloud compute forwarding-rules list --global --format="value(name)" 2>/dev/null | grep -E "saleor"); do
    echo "Deleting forwarding rule: $rule"
    gcloud compute forwarding-rules delete $rule --global --quiet
done

# Target HTTPS proxies
for proxy in $(gcloud compute target-https-proxies list --format="value(name)" 2>/dev/null | grep -E "saleor"); do
    echo "Deleting target HTTPS proxy: $proxy"
    gcloud compute target-https-proxies delete $proxy --quiet
done

# URL maps
for urlmap in $(gcloud compute url-maps list --format="value(name)" 2>/dev/null | grep -E "saleor"); do
    echo "Deleting URL map: $urlmap"
    gcloud compute url-maps delete $urlmap --quiet
done

# Backend services
for backend in $(gcloud compute backend-services list --global --format="value(name)" 2>/dev/null | grep -E "saleor"); do
    echo "Deleting backend service: $backend"
    gcloud compute backend-services delete $backend --global --quiet
done

# Health checks
for healthcheck in $(gcloud compute health-checks list --format="value(name)" 2>/dev/null | grep -E "saleor"); do
    echo "Deleting health check: $healthcheck"
    gcloud compute health-checks delete $healthcheck --quiet
done

# SSL certificates
for cert in $(gcloud compute ssl-certificates list --format="value(name)" 2>/dev/null | grep -E "saleor"); do
    echo "Deleting SSL certificate: $cert"
    gcloud compute ssl-certificates delete $cert --quiet
done

# External IPs
for ip in $(gcloud compute addresses list --global --format="value(name)" 2>/dev/null | grep -E "saleor"); do
    echo "Deleting external IP: $ip"
    gcloud compute addresses delete $ip --global --quiet
done

# 9. Delete Service Accounts
echo "Deleting Service Accounts..."
for sa in $(gcloud iam service-accounts list --format="value(email)" 2>/dev/null | grep -E "saleor"); do
    echo "Deleting service account: $sa"
    gcloud iam service-accounts delete $sa --quiet
done

# 10. Delete Secrets
echo "Deleting Secrets..."
for secret in $(gcloud secrets list --format="value(name)" 2>/dev/null | grep -E "saleor"); do
    echo "Deleting secret: $secret"
    gcloud secrets delete $secret --quiet
done

# 11. Delete VPC Access Connectors
echo "Deleting VPC Access Connectors in asia-southeast2..."
for connector in $(gcloud compute networks vpc-access connectors list --region=asia-southeast2 --format="value(name)" 2>/dev/null | grep -E "saleor"); do
    echo "Deleting VPC connector: $connector"
    gcloud compute networks vpc-access connectors delete $connector --region=asia-southeast2 --quiet
done

# 12. Delete Service Networking Connections
echo "Checking Service Networking Connections..."
# This requires the servicenetworking.googleapis.com API
for network in $(gcloud compute networks list --format="value(name)" 2>/dev/null | grep -E "saleor|default"); do
    echo "Checking peering connections for network: $network"
    gcloud services vpc-peerings list --network=$network 2>/dev/null
done

echo ""
echo "========================================="
echo "Manual Cleanup Complete"
echo "========================================="
echo ""
echo "To verify all resources are deleted, run:"
echo "  ./check-indonesia-resources.sh"