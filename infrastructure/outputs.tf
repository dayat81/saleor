# Outputs for Saleor Google Cloud Infrastructure

output "project_id" {
  description = "Google Cloud Project ID"
  value       = var.project_id
}

output "region" {
  description = "Google Cloud region"
  value       = var.region
}

output "environment" {
  description = "Environment name"
  value       = var.environment
}

# Network outputs
output "vpc_network_name" {
  description = "Name of the VPC network"
  value       = google_compute_network.vpc_network.name
}

output "vpc_network_id" {
  description = "ID of the VPC network"
  value       = google_compute_network.vpc_network.id
}

output "subnet_name" {
  description = "Name of the application subnet"
  value       = google_compute_subnetwork.subnet.name
}

output "cloud_run_service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_v2_service.saleor_app.name
}

output "cloud_run_service_url" {
  description = "URL of the Cloud Run service"
  value       = google_cloud_run_v2_service.saleor_app.uri
}

output "cloud_run_job_name" {
  description = "Name of the Cloud Run job"
  value       = google_cloud_run_v2_job.saleor_worker.name
}

# Database outputs
output "database_instance_name" {
  description = "Name of the Cloud SQL instance"
  value       = google_sql_database_instance.postgres.name
}

output "database_connection_name" {
  description = "Connection name for Cloud SQL instance"
  value       = google_sql_database_instance.postgres.connection_name
}

output "database_private_ip" {
  description = "Private IP address of the database"
  value       = google_sql_database_instance.postgres.private_ip_address
  sensitive   = true
}

output "database_name" {
  description = "Name of the Saleor database"
  value       = google_sql_database.saleor_db.name
}

output "database_user" {
  description = "Database username"
  value       = google_sql_user.saleor_user.name
}

# Redis outputs
output "redis_instance_name" {
  description = "Name of the Redis instance"
  value       = google_redis_instance.redis.name
}

output "redis_host" {
  description = "Host address of the Redis instance"
  value       = google_redis_instance.redis.host
  sensitive   = true
}

output "redis_port" {
  description = "Port of the Redis instance"
  value       = google_redis_instance.redis.port
}

output "redis_url" {
  description = "Redis connection URL"
  value       = "redis://${google_redis_instance.redis.host}:${google_redis_instance.redis.port}/0"
  sensitive   = true
}

# Storage outputs
output "static_bucket_name" {
  description = "Name of the static files bucket"
  value       = google_storage_bucket.static_files.name
}

output "static_bucket_url" {
  description = "URL of the static files bucket"
  value       = google_storage_bucket.static_files.url
}

output "media_bucket_name" {
  description = "Name of the media files bucket"
  value       = google_storage_bucket.media_files.name
}

output "media_bucket_url" {
  description = "URL of the media files bucket"
  value       = google_storage_bucket.media_files.url
}

output "private_bucket_name" {
  description = "Name of the private files bucket"
  value       = google_storage_bucket.private_files.name
}

# Container Registry outputs
output "artifact_registry_repository" {
  description = "Artifact Registry repository name"
  value       = google_artifact_registry_repository.saleor_repo.name
}

output "container_image_url" {
  description = "Base URL for container images"
  value       = "${google_artifact_registry_repository.saleor_repo.location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.saleor_repo.repository_id}"
}

# Cloud Run outputs
output "cloud_run_service_account_email" {
  description = "Email of the Cloud Run service account"
  value       = google_service_account.cloud_run_sa.email
}

output "cloud_run_service_account_id" {
  description = "ID of the Cloud Run service account"
  value       = google_service_account.cloud_run_sa.account_id
}

output "vpc_connector_name" {
  description = "Name of the VPC connector"
  value       = google_vpc_access_connector.vpc_connector.name
}

# Load Balancer outputs
output "load_balancer_ip" {
  description = "External IP address of the load balancer"
  value       = google_compute_global_address.lb_ip.address
}

output "load_balancer_ip_name" {
  description = "Name of the load balancer IP address"
  value       = google_compute_global_address.lb_ip.name
}

output "ssl_certificate_name" {
  description = "Name of the managed SSL certificate"
  value       = google_compute_managed_ssl_certificate.saleor_ssl_cert.name
}

# Secret Manager outputs
output "django_secret_key_id" {
  description = "Secret Manager secret ID for Django secret key"
  value       = google_secret_manager_secret.django_secret_key.secret_id
}

output "db_password_secret_id" {
  description = "Secret Manager secret ID for database password"
  value       = google_secret_manager_secret.db_password.secret_id
}

# Environment variables for application
output "environment_variables" {
  description = "Environment variables for the application"
  value = {
    PROJECT_ID                   = var.project_id
    DATABASE_URL                 = "postgresql://${google_sql_user.saleor_user.name}:${var.db_password}@${google_sql_database_instance.postgres.private_ip_address}:5432/${google_sql_database.saleor_db.name}"
    REDIS_URL                    = "redis://${google_redis_instance.redis.host}:${google_redis_instance.redis.port}/0"
    CELERY_BROKER_URL           = "redis://${google_redis_instance.redis.host}:${google_redis_instance.redis.port}/0"
    GS_PROJECT_ID               = var.project_id
    GS_BUCKET_NAME              = google_storage_bucket.static_files.name
    GS_MEDIA_BUCKET_NAME        = google_storage_bucket.media_files.name
    GS_MEDIA_PRIVATE_BUCKET_NAME = google_storage_bucket.private_files.name
    PUBLIC_URL                  = var.public_url
    ALLOWED_HOSTS               = var.allowed_hosts
    ALLOWED_CLIENT_HOSTS        = var.allowed_client_hosts
  }
  sensitive = true
}

# Deployment information
output "deployment_commands" {
  description = "Commands to deploy the application"
  value = [
    "# Configure Docker authentication:",
    "gcloud auth configure-docker ${google_artifact_registry_repository.saleor_repo.location}-docker.pkg.dev",
    "",
    "# Build and push Docker image:",
    "docker build -t ${google_artifact_registry_repository.saleor_repo.location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.saleor_repo.repository_id}/saleor:latest ..",
    "docker push ${google_artifact_registry_repository.saleor_repo.location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.saleor_repo.repository_id}/saleor:latest",
    "",
    "# Deploy to Cloud Run:",
    "gcloud run services update ${google_cloud_run_v2_service.saleor_app.name} --region=${var.region}",
    "",
    "# Configure DNS to point to:",
    "IP: ${google_compute_global_address.lb_ip.address}"
  ]
}

# Health check URLs
output "health_check_urls" {
  description = "URLs for health checks"
  value = {
    application      = "https://${var.domain_name}/health/"
    graphql_endpoint = "https://${var.domain_name}/graphql/"
  }
}

# Connection strings
output "connection_strings" {
  description = "Connection strings for external tools"
  value = {
    cloud_sql_proxy = "gcloud sql connect ${google_sql_database_instance.postgres.name} --user=${google_sql_user.saleor_user.name}"
    psql_direct     = "PGPASSWORD='${var.db_password}' psql -h ${google_sql_database_instance.postgres.private_ip_address} -U ${google_sql_user.saleor_user.name} -d ${google_sql_database.saleor_db.name}"
  }
  sensitive = true
}

# Monitoring URLs
output "monitoring_urls" {
  description = "URLs for monitoring and logging"
  value = {
    cloud_console     = "https://console.cloud.google.com/home/dashboard?project=${var.project_id}"
    cloud_run_console = "https://console.cloud.google.com/run/detail/${var.region}/${google_cloud_run_v2_service.saleor_app.name}/overview?project=${var.project_id}"
    cloud_sql_console = "https://console.cloud.google.com/sql/instances/${google_sql_database_instance.postgres.name}/overview?project=${var.project_id}"
    redis_console     = "https://console.cloud.google.com/memorystore/redis/locations/${var.region}/instances/${google_redis_instance.redis.name}/overview?project=${var.project_id}"
    storage_console   = "https://console.cloud.google.com/storage/browser?project=${var.project_id}"
  }
}

# Cost monitoring
output "cost_monitoring" {
  description = "Information for cost monitoring"
  value = {
    billing_account_url = "https://console.cloud.google.com/billing?project=${var.project_id}"
    budget_alerts       = "Set up budget alerts in Google Cloud Console"
    cost_breakdown = {
      gke_cluster   = "Per-node cost based on machine type"
      cloud_sql     = "Fixed cost based on tier: ${var.db_tier}"
      redis         = "Fixed cost based on memory: ${var.redis_memory_size}GB"
      storage       = "Pay-per-GB stored + operations"
      networking    = "Pay-per-GB egress traffic"
      load_balancer = "Fixed cost + per-rule charges"
    }
  }
}

# Security information
output "security_information" {
  description = "Security configuration details"
  value = {
    private_networking = "All services use private IPs within VPC"
    ssl_termination   = "HTTPS enforced at load balancer"
    secret_management = "Credentials stored in Secret Manager"
    service_account   = "Minimal permissions for Cloud Run service account"
    database_security = "Cloud SQL with private IP and SSL required"
    storage_security  = "Bucket-level permissions with IAM"
  }
}

# Backup information
output "backup_information" {
  description = "Backup configuration details"
  value = {
    database_backups = {
      frequency         = "Daily at 03:00 UTC"
      retention_days   = var.environment == "production" ? 30 : 7
      point_in_time    = "Enabled for ${var.environment == "production" ? 30 : 7} days"
    }
    storage_versioning = "Enabled on all buckets"
    disaster_recovery = "Cross-region replication recommended for production"
  }
}