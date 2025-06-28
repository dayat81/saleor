# Saleor Google Cloud Infrastructure
# This Terraform configuration deploys Saleor on Google Cloud Platform
# using serverless architecture with Cloud Run, Cloud SQL, and Cloud Memorystore

# Configure the Google Cloud Provider
provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "vpcaccess.googleapis.com",
    "sql-component.googleapis.com",
    "redis.googleapis.com",
    "storage.googleapis.com",
    "compute.googleapis.com",
    "cloudscheduler.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com"
  ])

  service = each.value
  
  disable_dependent_services = true
  disable_on_destroy = false
}

# Random suffix for unique resource names
resource "random_id" "suffix" {
  byte_length = 4
}

locals {
  # Common labels for all resources
  common_labels = {
    project     = "saleor"
    environment = var.environment
    managed_by  = "terraform"
  }
  
  # Unique suffix for resources
  suffix = random_id.suffix.hex
}

# VPC Network
resource "google_compute_network" "vpc_network" {
  name                    = "saleor-vpc-${local.suffix}"
  auto_create_subnetworks = false
  description             = "VPC network for Saleor application"
  
  depends_on = [google_project_service.required_apis]
}

# Subnet for GKE and other services
resource "google_compute_subnetwork" "subnet" {
  name          = "saleor-subnet-${local.suffix}"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc_network.id
  description   = "Subnet for Saleor application services"
  
  # Enable private Google access
  private_ip_google_access = true
  
  # Secondary IP ranges for GKE
  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = "10.1.0.0/16"
  }
  
  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = "10.2.0.0/20"
  }
}

# VPC Connector for Cloud Run private networking
resource "google_vpc_access_connector" "vpc_connector" {
  name          = "saleor-connector-${local.suffix}"
  region        = var.region
  ip_cidr_range = "10.8.0.0/28"
  network       = google_compute_network.vpc_network.name
  
  depends_on = [google_project_service.required_apis]
}

# Service Account for Cloud Run
resource "google_service_account" "cloud_run_sa" {
  account_id   = "saleor-cloud-run-${local.suffix}"
  display_name = "Saleor Cloud Run Service Account"
  description  = "Service account for Saleor Cloud Run services"
}

# IAM bindings for Cloud Run service account
resource "google_project_iam_member" "cloud_run_sa_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_project_iam_member" "cloud_run_sa_storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_project_iam_member" "cloud_run_sa_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Cloud Run Service
resource "google_cloud_run_v2_service" "saleor_app" {
  name     = "saleor-app-${local.suffix}"
  location = var.region
  
  template {
    service_account = google_service_account.cloud_run_sa.email
    
    vpc_access {
      connector = google_vpc_access_connector.vpc_connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }
    
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }
    
    containers {
      image = "${google_artifact_registry_repository.saleor_repo.location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.saleor_repo.name}/saleor:latest"
      
      ports {
        container_port = 8000
      }
      
      resources {
        limits = {
          cpu    = "1000m"
          memory = "1Gi"
        }
      }
      
      startup_probe {
        http_get {
          path = "/health/"
          port = 8000
        }
        initial_delay_seconds = 30
        timeout_seconds       = 10
        period_seconds        = 10
        failure_threshold     = 3
      }
      
      liveness_probe {
        http_get {
          path = "/health/"
          port = 8000
        }
        initial_delay_seconds = 30
        timeout_seconds       = 10
        period_seconds        = 30
        failure_threshold     = 3
      }
      
      env {
        name  = "DATABASE_URL"
        value = "postgres://${google_sql_user.saleor_user.name}:${google_sql_user.saleor_user.password}@${google_sql_database_instance.postgres.private_ip_address}:5432/${google_sql_database.saleor_db.name}"
      }
      
      env {
        name  = "REDIS_URL"
        value = "redis://${google_redis_instance.redis.host}:${google_redis_instance.redis.port}/0"
      }
      
      env {
        name  = "SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.django_secret_key.secret_id
            version = "latest"
          }
        }
      }
      
      env {
        name  = "DEBUG"
        value = var.environment == "development" ? "True" : "False"
      }
      
      env {
        name  = "ALLOWED_HOSTS"
        value = var.allowed_hosts
      }
      
      env {
        name  = "ALLOWED_CLIENT_HOSTS"
        value = var.allowed_client_hosts
      }
      
      env {
        name  = "DEFAULT_FROM_EMAIL"
        value = "noreply@${var.domain_name}"
      }
      
      env {
        name  = "EMAIL_URL"
        value = var.email_url
      }
      
      env {
        name  = "GS_BUCKET_NAME"
        value = google_storage_bucket.media_files.name
      }
      
      env {
        name  = "GS_STATIC_BUCKET_NAME"
        value = google_storage_bucket.static_files.name
      }
      
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      
      env {
        name  = "TELEMETRY_TRACER_CLASS"
        value = "saleor.core.telemetry.NoOpTelemetryTracer"
      }
      
      env {
        name  = "TELEMETRY_METER_CLASS"
        value = "saleor.core.telemetry.NoOpTelemetryMeter"
      }
    }
  }
  
  depends_on = [
    google_project_service.required_apis,
    google_sql_database_instance.postgres,
    google_redis_instance.redis
  ]
}

# Cloud Run Job for Celery Worker
resource "google_cloud_run_v2_job" "saleor_worker" {
  name     = "saleor-worker-${local.suffix}"
  location = var.region
  
  template {
    parallelism = 10
    task_count  = 1
    
    template {
      service_account = google_service_account.cloud_run_sa.email
      
      vpc_access {
        connector = google_vpc_access_connector.vpc_connector.id
        egress    = "PRIVATE_RANGES_ONLY"
      }
      
      containers {
        image = "${google_artifact_registry_repository.saleor_repo.location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.saleor_repo.name}/saleor:latest"
        
        command = ["celery"]
        args    = ["-A", "saleor", "worker", "--loglevel=info"]
        
        resources {
          limits = {
            cpu    = "1000m"
            memory = "1Gi"
          }
        }
        
        env {
          name  = "DATABASE_URL"
          value = "postgres://${google_sql_user.saleor_user.name}:${google_sql_user.saleor_user.password}@${google_sql_database_instance.postgres.private_ip_address}:5432/${google_sql_database.saleor_db.name}"
        }
        
        env {
          name  = "REDIS_URL"
          value = "redis://${google_redis_instance.redis.host}:${google_redis_instance.redis.port}/0"
        }
        
        env {
          name  = "SECRET_KEY"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.django_secret_key.secret_id
              version = "latest"
            }
          }
        }
        
        env {
          name  = "GOOGLE_CLOUD_PROJECT"
          value = var.project_id
        }
        
        env {
          name  = "TELEMETRY_TRACER_CLASS"
          value = "saleor.core.telemetry.NoOpTelemetryTracer"
        }
        
        env {
          name  = "TELEMETRY_METER_CLASS"
          value = "saleor.core.telemetry.NoOpTelemetryMeter"
        }
      }
    }
  }
  
  depends_on = [
    google_project_service.required_apis,
    google_sql_database_instance.postgres,
    google_redis_instance.redis
  ]
}

# Cloud NAT for outbound internet access
resource "google_compute_router" "router" {
  name    = "saleor-router-${local.suffix}"
  region  = var.region
  network = google_compute_network.vpc_network.id
}

resource "google_compute_router_nat" "nat" {
  name   = "saleor-nat-${local.suffix}"
  router = google_compute_router.router.name
  region = var.region

  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}


# Artifact Registry for container images
resource "google_artifact_registry_repository" "saleor_repo" {
  location      = var.region
  repository_id = "saleor-${local.suffix}"
  description   = "Saleor container images"
  format        = "DOCKER"
  
  labels = local.common_labels
  
  depends_on = [google_project_service.required_apis]
}

# Cloud Storage buckets
resource "google_storage_bucket" "static_files" {
  name          = "saleor-static-${var.project_id}-${local.suffix}"
  location      = var.region
  force_destroy = false
  storage_class = "STANDARD"
  
  labels = local.common_labels

  uniform_bucket_level_access = true
  
  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD"]
    response_header = ["*"]
    max_age_seconds = 3600
  }
  
  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
}

resource "google_storage_bucket" "media_files" {
  name          = "saleor-media-${var.project_id}-${local.suffix}"
  location      = var.region
  force_destroy = false
  storage_class = "STANDARD"
  
  labels = local.common_labels

  uniform_bucket_level_access = true
  
  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD", "POST", "PUT", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }
  
  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
}

resource "google_storage_bucket" "private_files" {
  name          = "saleor-private-${var.project_id}-${local.suffix}"
  location      = var.region
  force_destroy = false
  storage_class = "STANDARD"
  
  labels = local.common_labels

  uniform_bucket_level_access = true
  
  # No CORS for private files
  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
}

# Note: Public access to buckets removed due to organization policy restrictions
# Buckets can be made public manually in Google Cloud Console if needed
# or via bucket-level ACLs

# Cloud SQL instance
resource "google_sql_database_instance" "postgres" {
  name             = "saleor-postgres-${local.suffix}"
  database_version = "POSTGRES_15"
  region           = var.region
  
  deletion_protection = var.environment == "production"
  
  settings {
    tier              = var.db_tier
    availability_type = var.environment == "production" ? "REGIONAL" : "ZONAL"
    disk_type         = "PD_HDD"
    disk_size         = var.db_disk_size
    disk_autoresize   = true
    
    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      backup_retention_settings {
        retained_backups = var.environment == "production" ? 30 : 7
      }
    }
    
    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = google_compute_network.vpc_network.id
      enable_private_path_for_google_cloud_services = true
    }
    
    database_flags {
      name  = "max_connections"
      value = "200"
    }
    
    user_labels = local.common_labels
  }
  
  depends_on = [
    google_project_service.required_apis,
    google_service_networking_connection.private_vpc_connection
  ]
}

# Private service networking for Cloud SQL
resource "google_compute_global_address" "private_ip_address" {
  name          = "saleor-private-ip-${local.suffix}"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc_network.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc_network.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}

# Cloud SQL database
resource "google_sql_database" "saleor_db" {
  name     = "saleor"
  instance = google_sql_database_instance.postgres.name
}

# Cloud SQL user
resource "google_sql_user" "saleor_user" {
  name     = "saleor"
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
}

# Cloud Memorystore Redis instance
resource "google_redis_instance" "redis" {
  name           = "saleor-redis-${local.suffix}"
  tier           = var.redis_tier
  memory_size_gb = var.redis_memory_size
  region         = var.region
  
  authorized_network = google_compute_network.vpc_network.id
  
  redis_version = "REDIS_7_0"
  display_name  = "Saleor Redis Cache"
  
  labels = local.common_labels
  
  depends_on = [google_project_service.required_apis]
}

# Secret Manager secrets
resource "google_secret_manager_secret" "django_secret_key" {
  secret_id = "saleor-django-secret-key-${local.suffix}"
  
  labels = local.common_labels
  
  replication {
    auto {}
  }
  
  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "django_secret_key" {
  secret      = google_secret_manager_secret.django_secret_key.id
  secret_data = var.django_secret_key
}

resource "google_secret_manager_secret" "db_password" {
  secret_id = "saleor-db-password-${local.suffix}"
  
  labels = local.common_labels
  
  replication {
    auto {}
  }
  
  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = var.db_password
}

# Note: Kubernetes deployments will be handled via kubectl after cluster is created

# Load Balancer IP for GKE ingress
resource "google_compute_global_address" "lb_ip" {
  name = "saleor-lb-ip-${local.suffix}"
}

# Note: Load balancer will use Kubernetes ingress after cluster setup
# Backend service will be created by GKE ingress controller
resource "google_compute_backend_service" "saleor_backend" {
  name                  = "saleor-backend-${local.suffix}"
  protocol              = "HTTP"
  timeout_sec           = 900
  enable_cdn            = true
  load_balancing_scheme = "EXTERNAL"
  
  # Backend will be managed by GKE ingress
  
  cdn_policy {
    cache_mode                   = "CACHE_ALL_STATIC"
    default_ttl                  = 3600
    max_ttl                      = 86400
    negative_caching             = true
    negative_caching_policy {
      code = 404
      ttl  = 120
    }
    cache_key_policy {
      include_host = true
      include_protocol = true
      include_query_string = true
    }
  }
  
  log_config {
    enable      = true
    sample_rate = 1.0
  }
  
  health_checks = [google_compute_health_check.saleor_health_check.id]
}

# Health check for GKE service
resource "google_compute_health_check" "saleor_health_check" {
  name = "saleor-health-check-${local.suffix}"
  
  http_health_check {
    port         = 80
    request_path = "/health/"
  }
}

resource "google_compute_url_map" "saleor_url_map" {
  name            = "saleor-url-map-${local.suffix}"
  default_service = google_compute_backend_service.saleor_backend.id
}

resource "google_compute_target_https_proxy" "saleor_https_proxy" {
  name             = "saleor-https-proxy-${local.suffix}"
  url_map          = google_compute_url_map.saleor_url_map.id
  ssl_certificates = [google_compute_managed_ssl_certificate.saleor_ssl_cert.id]
}

resource "google_compute_global_forwarding_rule" "saleor_forwarding_rule" {
  name       = "saleor-forwarding-rule-${local.suffix}"
  target     = google_compute_target_https_proxy.saleor_https_proxy.id
  port_range = "443"
  ip_address = google_compute_global_address.lb_ip.id
}

resource "google_compute_managed_ssl_certificate" "saleor_ssl_cert" {
  name = "saleor-ssl-cert-${local.suffix}"
  
  managed {
    domains = [var.domain_name]
  }
}