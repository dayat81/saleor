# Saleor Google Cloud deployment configuration
# Auto-generated for project: melodic-now-463704-k1

# Required variables
project_id         = "melodic-now-463704-k1"
domain_name        = "saleor-demo.example.com"
public_url         = "https://saleor-demo.example.com"
django_secret_key  = "demo-secret-key-change-in-production"
db_password        = "secure-db-password-123"

# Optional variables with demo values
region             = "asia-southeast2"
environment        = "development"

# Application configuration
allowed_hosts        = "saleor-demo.example.com,*.run.app"
allowed_client_hosts = "*.example.com,localhost"

# Email configuration (console backend for demo)
email_url = "console://"

# Database configuration
db_tier      = "db-custom-1-3840"  # 1 vCPU, 3.75GB RAM (demo size)
db_disk_size = 20                  # GB - minimal size for demo

# Redis configuration
redis_tier        = "BASIC"        # Basic tier for demo
redis_memory_size = 1              # GB

# Cloud Run configuration
min_instances = 0    # Scale to zero for cost savings
max_instances = 5    # Reasonable scale for demo

# Demo settings
enable_debug_features = true   # Enable for demo
enable_monitoring     = true
enable_cdn           = false   # Disable CDN for demo

# Cost optimization for demo
preemptible_workers = true

# Security (relaxed for demo)
enable_private_networking    = false  # Simplified networking for demo
enable_deletion_protection   = false  # Allow easy cleanup

# Backup configuration
backup_retention_days = 7  # Shorter retention for demo

# Additional labels for resource organization
additional_labels = {
  environment = "demo"
  purpose     = "saleor-testing"
}