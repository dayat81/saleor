# Saleor Google Cloud Infrastructure
# This Terraform configuration deploys Saleor on Google Cloud Platform
# using serverless architecture with Cloud Run, Cloud SQL, and Cloud Memorystore

terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
}

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
    "sql-component.googleapis.com",
    "redis.googleapis.com",
    "storage.googleapis.com",
    "compute.googleapis.com",
    "cloudscheduler.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "vpcaccess.googleapis.com"
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

# Subnet for Cloud Run and other services
resource "google_compute_subnetwork" "subnet" {
  name          = "saleor-subnet-${local.suffix}"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc_network.id
  description   = "Subnet for Saleor application services"
  
  # Enable private Google access
  private_ip_google_access = true
}

# VPC Connector for Cloud Run
resource "google_vpc_access_connector" "connector" {
  provider = google-beta
  
  name          = "saleor-connector-${local.suffix}"
  region        = var.region
  ip_cidr_range = "10.8.0.0/28"
  network       = google_compute_network.vpc_network.name
  
  depends_on = [google_project_service.required_apis]
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

# Service Account for Cloud Run
resource "google_service_account" "cloud_run_sa" {
  account_id   = "saleor-cloud-run-${local.suffix}"
  display_name = "Saleor Cloud Run Service Account"
  description  = "Service account for Saleor Cloud Run instances"
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

# Make static and media buckets publicly readable
resource "google_storage_bucket_iam_member" "static_files_public" {
  bucket = google_storage_bucket.static_files.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

resource "google_storage_bucket_iam_member" "media_files_public" {
  bucket = google_storage_bucket.media_files.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

# Cloud SQL instance
resource "google_sql_database_instance" "postgres" {
  name             = "saleor-postgres-${local.suffix}"
  database_version = "POSTGRES_15"
  region           = var.region
  
  deletion_protection = var.environment == "production"
  
  settings {
    tier              = var.db_tier
    availability_type = var.environment == "production" ? "REGIONAL" : "ZONAL"
    disk_type         = "PD_SSD"
    disk_size         = var.db_disk_size
    disk_autoresize   = true
    
    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      backup_retention_days          = var.environment == "production" ? 30 : 7
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
    
    database_flags {
      name  = "shared_preload_libraries"
      value = "pg_stat_statements"
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

# Cloud Run service
resource "google_cloud_run_v2_service" "saleor_app" {
  name     = "saleor-app-${local.suffix}"
  location = var.region
  
  labels = local.common_labels
  
  template {
    labels = local.common_labels
    
    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "ALL_TRAFFIC"
    }
    
    service_account = google_service_account.cloud_run_sa.email
    
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }
    
    containers {
      image = "${google_artifact_registry_repository.saleor_repo.location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.saleor_repo.repository_id}/saleor:latest"
      
      ports {
        container_port = 8000
      }
      
      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
        cpu_idle = false
      }
      
      startup_probe {
        http_get {
          path = "/health/"
          port = 8000
        }
        initial_delay_seconds = 30
        timeout_seconds      = 10
        period_seconds       = 10
        failure_threshold    = 3
      }
      
      liveness_probe {
        http_get {
          path = "/health/"
          port = 8000
        }
        initial_delay_seconds = 30
        timeout_seconds      = 10
        period_seconds       = 30
        failure_threshold    = 3
      }
      
      env {
        name  = "DEBUG"
        value = "False"
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
        name  = "PUBLIC_URL"
        value = var.public_url
      }
      
      env {
        name  = "DATABASE_URL"
        value = "postgresql://${google_sql_user.saleor_user.name}:${var.db_password}@${google_sql_database_instance.postgres.private_ip_address}:5432/${google_sql_database.saleor_db.name}"
      }
      
      env {
        name  = "REDIS_URL"
        value = "redis://${google_redis_instance.redis.host}:${google_redis_instance.redis.port}/0"
      }
      
      env {
        name  = "CELERY_BROKER_URL"
        value = "redis://${google_redis_instance.redis.host}:${google_redis_instance.redis.port}/0"
      }
      
      env {
        name  = "GS_PROJECT_ID"
        value = var.project_id
      }
      
      env {
        name  = "GS_BUCKET_NAME"
        value = google_storage_bucket.static_files.name
      }
      
      env {
        name  = "GS_MEDIA_BUCKET_NAME"
        value = google_storage_bucket.media_files.name
      }
      
      env {
        name  = "GS_MEDIA_PRIVATE_BUCKET_NAME"
        value = google_storage_bucket.private_files.name
      }
      
      env {
        name = "SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.django_secret_key.secret_id
            version = "latest"
          }
        }
      }
      
      env {
        name  = "EMAIL_URL"
        value = var.email_url
      }
      
      env {
        name  = "ENABLE_DEBUG_TOOLBAR"
        value = "False"
      }
      
      env {
        name  = "PLAYGROUND_ENABLED"
        value = var.environment == "production" ? "False" : "True"
      }
    }
  }
  
  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
  
  depends_on = [
    google_project_service.required_apis,
    google_vpc_access_connector.connector,
    google_sql_database_instance.postgres,
    google_redis_instance.redis
  ]
}

# Cloud Run IAM policy for public access
resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.saleor_app.location
  service  = google_cloud_run_v2_service.saleor_app.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Cloud Run Job for Celery workers
resource "google_cloud_run_v2_job" "saleor_worker" {
  name     = "saleor-worker-${local.suffix}"
  location = var.region
  
  labels = local.common_labels
  
  template {
    labels = local.common_labels
    
    template {
      vpc_access {
        connector = google_vpc_access_connector.connector.id
        egress    = "ALL_TRAFFIC"
      }
      
      service_account = google_service_account.cloud_run_sa.email
      
      parallelism = 10
      task_count  = 1
      
      template {
        containers {
          image   = "${google_artifact_registry_repository.saleor_repo.location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.saleor_repo.repository_id}/saleor:latest"
          command = ["celery"]
          args    = ["-A", "saleor.celeryconf:app", "worker", "-E"]
          
          resources {
            limits = {
              cpu    = "1"
              memory = "1Gi"
            }
          }
          
          # Same environment variables as Cloud Run service
          env {
            name  = "DATABASE_URL"
            value = "postgresql://${google_sql_user.saleor_user.name}:${var.db_password}@${google_sql_database_instance.postgres.private_ip_address}:5432/${google_sql_database.saleor_db.name}"
          }
          
          env {
            name  = "REDIS_URL"
            value = "redis://${google_redis_instance.redis.host}:${google_redis_instance.redis.port}/0"
          }
          
          env {
            name  = "CELERY_BROKER_URL"
            value = "redis://${google_redis_instance.redis.host}:${google_redis_instance.redis.port}/0"
          }
          
          env {
            name  = "GS_PROJECT_ID"
            value = var.project_id
          }
          
          env {
            name  = "GS_BUCKET_NAME"
            value = google_storage_bucket.static_files.name
          }
          
          env {
            name  = "GS_MEDIA_BUCKET_NAME"
            value = google_storage_bucket.media_files.name
          }
          
          env {
            name  = "GS_MEDIA_PRIVATE_BUCKET_NAME"
            value = google_storage_bucket.private_files.name
          }
          
          env {
            name = "SECRET_KEY"
            value_source {
              secret_key_ref {
                secret  = google_secret_manager_secret.django_secret_key.secret_id
                version = "latest"
              }
            }
          }
        }
      }
    }
  }
  
  depends_on = [
    google_project_service.required_apis,
    google_vpc_access_connector.connector,
    google_sql_database_instance.postgres,
    google_redis_instance.redis
  ]
}

# Cloud Scheduler job to run Celery workers periodically
resource "google_cloud_scheduler_job" "worker_scheduler" {
  name      = "saleor-worker-scheduler-${local.suffix}"
  region    = var.region
  schedule  = "*/5 * * * *" # Every 5 minutes
  time_zone = "UTC"
  
  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${google_cloud_run_v2_job.saleor_worker.name}:run"
    
    oauth_token {
      service_account_email = google_service_account.cloud_run_sa.email
    }
  }
  
  depends_on = [google_project_service.required_apis]
}

# Load Balancer for HTTPS termination
resource "google_compute_global_address" "lb_ip" {
  name = "saleor-lb-ip-${local.suffix}"
}

resource "google_compute_backend_service" "saleor_backend" {
  name                  = "saleor-backend-${local.suffix}"
  protocol              = "HTTP"
  timeout_sec           = 900
  enable_cdn            = true
  load_balancing_scheme = "EXTERNAL"
  
  backend {
    group = google_compute_region_network_endpoint_group.saleor_neg.id
  }
  
  cdn_policy {
    cache_mode                   = "CACHE_ALL_STATIC"
    default_ttl                  = 3600
    max_ttl                      = 86400
    negative_caching             = true
    negative_caching_policy {
      code = 404
      ttl  = 120
    }
  }
  
  log_config {
    enable      = true
    sample_rate = 1.0
  }
}

resource "google_compute_region_network_endpoint_group" "saleor_neg" {
  name                  = "saleor-neg-${local.suffix}"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  
  cloud_run {
    service = google_cloud_run_v2_service.saleor_app.name
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