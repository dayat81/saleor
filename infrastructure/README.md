# Saleor Google Cloud Infrastructure

This directory contains Terraform configuration to deploy Saleor e-commerce platform on Google Cloud Platform using serverless architecture.

## Architecture Overview

- **Application**: Cloud Run (serverless containers)
- **Database**: Cloud SQL PostgreSQL
- **Cache**: Cloud Memorystore Redis
- **Storage**: Cloud Storage buckets
- **Networking**: Private VPC with Load Balancer
- **Container Registry**: Artifact Registry
- **Security**: IAM, Secret Manager, SSL termination

## Quick Start

### Prerequisites

1. **Google Cloud SDK**: Install and configure
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Terraform**: Install Terraform >= 1.5.0
   ```bash
   # macOS
   brew install terraform
   
   # Linux
   wget https://releases.hashicorp.com/terraform/1.5.0/terraform_1.5.0_linux_amd64.zip
   unzip terraform_1.5.0_linux_amd64.zip && sudo mv terraform /usr/local/bin/
   ```

3. **Docker**: Required for building container images

### Setup Instructions

1. **Clone and navigate**:
   ```bash
   cd infrastructure
   ```

2. **Configure variables**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

3. **Initialize Terraform**:
   ```bash
   terraform init
   ```

4. **Plan deployment**:
   ```bash
   terraform plan
   ```

5. **Deploy infrastructure**:
   ```bash
   terraform apply
   ```

6. **Build and deploy application**:
   ```bash
   # Configure Docker for Artifact Registry
   gcloud auth configure-docker us-central1-docker.pkg.dev
   
   # Build and push image
   docker build -t us-central1-docker.pkg.dev/YOUR_PROJECT_ID/saleor-SUFFIX/saleor:latest ..
   docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/saleor-SUFFIX/saleor:latest
   
   # Update Cloud Run service
   gcloud run services update saleor-app-SUFFIX --region=us-central1
   ```

## Configuration

### Required Variables

Edit `terraform.tfvars`:

```hcl
project_id         = "your-gcp-project-id"
domain_name        = "api.yourdomain.com"
public_url         = "https://api.yourdomain.com"
django_secret_key  = "your-super-secret-django-key"
db_password        = "your-secure-database-password"
```

### Optional Variables

```hcl
# Environment
environment = "production"  # development, staging, production

# Scaling
min_instances = 1
max_instances = 100

# Database
db_tier = "db-custom-2-8192"  # 2 vCPU, 8GB RAM
db_disk_size = 100            # GB

# Redis
redis_tier = "STANDARD_HA"
redis_memory_size = 5         # GB

# Email (choose one)
email_url = "console://"                                    # Development
email_url = "smtp://user:pass@smtp.gmail.com:587/?tls=True" # SMTP
sendgrid_api_key = "your-sendgrid-key"                     # SendGrid
```

## Managing Infrastructure

### View Infrastructure Status

```bash
# See all resources
terraform show

# Get specific outputs
terraform output cloud_run_service_url
terraform output load_balancer_ip
```

### Update Infrastructure

```bash
# Modify terraform.tfvars or .tf files
terraform plan
terraform apply
```

### Scaling

```bash
# Update variables in terraform.tfvars
min_instances = 2
max_instances = 200
db_tier = "db-custom-4-16384"

# Apply changes
terraform apply
```

## Application Deployment

### Automated Deployment

Use the included Cloud Build configuration:

```bash
# Deploy via Cloud Build
gcloud builds submit --config=../cloudbuild.yaml ..
```

### Manual Deployment

```bash
# 1. Build container image
docker build -t REGISTRY_URL/saleor:latest ..

# 2. Push to registry
docker push REGISTRY_URL/saleor:latest

# 3. Update Cloud Run
gcloud run services update SERVICE_NAME --region=REGION

# 4. Run migrations (if needed)
gcloud run jobs execute migration-job --region=REGION --wait
```

### Database Management

```bash
# Connect to database
gcloud sql connect INSTANCE_NAME --user=saleor

# Run migrations
gcloud run jobs execute migration-job --region=us-central1 --wait

# Create superuser
gcloud run jobs execute create-superuser-job --region=us-central1 --wait
```

## Monitoring & Maintenance

### Health Checks

- **Application**: `https://YOUR_DOMAIN/health/`
- **GraphQL**: `https://YOUR_DOMAIN/graphql/`
- **Cloud Run**: Available in Google Cloud Console

### Logs

```bash
# Cloud Run logs
gcloud logs read --project=PROJECT_ID --resource=cloud_run_revision

# Database logs
gcloud logs read --project=PROJECT_ID --resource=cloudsql_database

# Real-time monitoring
gcloud logs tail --project=PROJECT_ID
```

### Monitoring URLs

After deployment, access monitoring via:

- **Cloud Console**: `terraform output monitoring_urls`
- **Cloud Run Logs**: Available in outputs
- **Database Console**: Available in outputs
- **Redis Console**: Available in outputs

## Cost Optimization

### Development Environment

```hcl
environment = "development"
min_instances = 0          # Scale to zero
db_tier = "db-custom-1-3840"
redis_tier = "BASIC"
redis_memory_size = 1
preemptible_workers = true
```

### Production Environment

```hcl
environment = "production"
min_instances = 2          # Always warm
db_tier = "db-custom-4-16384"
redis_tier = "STANDARD_HA"
redis_memory_size = 10
enable_deletion_protection = true
backup_retention_days = 30
```

### Cost Monitoring

```bash
# View cost breakdown
terraform output cost_monitoring

# Set up budget alerts in Google Cloud Console
# Enable billing export to BigQuery for analysis
```

## Security

### Best Practices Applied

- **Private Networking**: All services use private IPs
- **SSL Termination**: HTTPS enforced at load balancer
- **Secret Management**: Credentials in Secret Manager
- **Minimal Permissions**: Least-privilege IAM
- **Network Security**: VPC with controlled egress
- **Database Security**: Private IP, SSL required

### Security Checklist

- [ ] Update `django_secret_key` from default
- [ ] Use strong `db_password`
- [ ] Configure proper `allowed_hosts`
- [ ] Set up proper DNS with your domain
- [ ] Enable Cloud Security Command Center
- [ ] Configure IAM policies for team access
- [ ] Set up monitoring and alerting

## Disaster Recovery

### Backups

- **Database**: Automated daily backups with point-in-time recovery
- **Storage**: Versioning enabled on all buckets
- **Code**: Version controlled in Git

### Recovery Procedures

```bash
# Restore database from backup
gcloud sql backups restore BACKUP_ID --restore-instance=INSTANCE_NAME

# Restore specific point in time
gcloud sql backups restore --restore-instance=INSTANCE_NAME \
  --backup-instance=SOURCE_INSTANCE --backup-time=TIMESTAMP
```

## Troubleshooting

### Common Issues

1. **Cloud Run not starting**:
   ```bash
   gcloud run services describe saleor-app-SUFFIX --region=us-central1
   gcloud logs read --resource=cloud_run_revision
   ```

2. **Database connection issues**:
   ```bash
   # Check VPC connector
   gcloud compute networks vpc-access connectors describe CONNECTOR_NAME

   # Test database connectivity
   gcloud sql connect INSTANCE_NAME --user=saleor
   ```

3. **Domain not resolving**:
   ```bash
   # Get load balancer IP
   terraform output load_balancer_ip
   
   # Configure DNS A record: yourdomain.com -> LOAD_BALANCER_IP
   ```

4. **SSL certificate not provisioning**:
   ```bash
   # Check certificate status
   gcloud compute ssl-certificates describe CERT_NAME --global
   
   # Ensure DNS is properly configured first
   ```

### Debug Mode

For development troubleshooting:

```hcl
# In terraform.tfvars
enable_debug_features = true
environment = "development"
```

## Cleanup & Destruction

### Complete Cleanup

```bash
# Destroy all infrastructure
terraform destroy

# Confirm by typing 'yes'
```

### Selective Cleanup

```bash
# Remove specific resources
terraform state rm google_storage_bucket.static_files
terraform apply
```

### Manual Cleanup

Some resources may need manual deletion:

```bash
# Delete container images
gcloud artifacts docker images delete REGISTRY_URL/saleor:latest

# Delete logs (if needed)
gcloud logging sinks delete SINK_NAME
```

## Support

### Getting Help

1. **Terraform Issues**: Check Terraform and Google provider documentation
2. **Google Cloud Issues**: Use `gcloud` CLI help and Google Cloud documentation
3. **Application Issues**: Check Saleor documentation and logs

### Useful Commands

```bash
# Terraform state management
terraform state list
terraform state show RESOURCE_NAME
terraform refresh

# Google Cloud resource inspection
gcloud compute instances list
gcloud sql instances list
gcloud run services list
gcloud storage buckets list

# Resource cleanup verification
gcloud projects get-iam-policy PROJECT_ID
gcloud billing accounts projects describe PROJECT_ID
```

## File Structure

```
infrastructure/
├── main.tf                 # Main infrastructure resources
├── variables.tf            # Input variable definitions
├── outputs.tf              # Output value definitions
├── versions.tf             # Provider version constraints
├── terraform.tfvars.example # Example configuration
├── terraform.tfvars        # Your configuration (not in git)
├── terraform.tfstate       # Terraform state (not in git)
└── README.md              # This file
```

## Next Steps

After successful deployment:

1. **Configure DNS**: Point your domain to the load balancer IP
2. **Set up CI/CD**: Use Cloud Build or GitHub Actions
3. **Configure monitoring**: Set up alerts and dashboards
4. **Load test**: Verify performance under expected load
5. **Security review**: Audit IAM policies and network security
6. **Backup testing**: Verify backup and restore procedures

## Contributing

When modifying this infrastructure:

1. Update variable descriptions and validation
2. Add new outputs for important resource information
3. Update this README with new features
4. Test changes in development environment first
5. Document any breaking changes