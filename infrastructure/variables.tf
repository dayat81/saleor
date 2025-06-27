# Variables for Saleor Google Cloud Infrastructure

variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "The Google Cloud region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  default     = "development"
  
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production."
  }
}

variable "domain_name" {
  description = "Domain name for the application (e.g., api.example.com)"
  type        = string
}

variable "allowed_hosts" {
  description = "Comma-separated list of allowed hosts for Django"
  type        = string
  default     = "*"
}

variable "allowed_client_hosts" {
  description = "Comma-separated list of allowed client hosts"
  type        = string
  default     = "*"
}

variable "public_url" {
  description = "Public URL of the application"
  type        = string
}

# Database configuration
variable "db_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-custom-2-8192"
}

variable "db_disk_size" {
  description = "Cloud SQL disk size in GB"
  type        = number
  default     = 100
}

variable "db_password" {
  description = "Password for the database user"
  type        = string
  sensitive   = true
}

# Redis configuration
variable "redis_tier" {
  description = "Redis instance tier (BASIC or STANDARD_HA)"
  type        = string
  default     = "STANDARD_HA"
  
  validation {
    condition     = contains(["BASIC", "STANDARD_HA"], var.redis_tier)
    error_message = "Redis tier must be either BASIC or STANDARD_HA."
  }
}

variable "redis_memory_size" {
  description = "Redis memory size in GB"
  type        = number
  default     = 5
}

# Cloud Run configuration
variable "min_instances" {
  description = "Minimum number of Cloud Run instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 100
}

# Application configuration
variable "django_secret_key" {
  description = "Django SECRET_KEY"
  type        = string
  sensitive   = true
}

variable "email_url" {
  description = "Email URL for Django email backend"
  type        = string
  default     = "console://"
  sensitive   = true
}

# Optional email configuration
variable "sendgrid_api_key" {
  description = "SendGrid API key for email sending"
  type        = string
  default     = ""
  sensitive   = true
}

variable "email_host" {
  description = "SMTP host for email sending"
  type        = string
  default     = ""
}

variable "email_port" {
  description = "SMTP port for email sending"
  type        = number
  default     = 587
}

variable "email_user" {
  description = "SMTP username for email sending"
  type        = string
  default     = ""
  sensitive   = true
}

variable "email_password" {
  description = "SMTP password for email sending"
  type        = string
  default     = ""
  sensitive   = true
}

# Monitoring and logging
variable "enable_monitoring" {
  description = "Enable enhanced monitoring and alerting"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "Number of days to retain logs"
  type        = number
  default     = 30
}

# Backup configuration
variable "backup_retention_days" {
  description = "Number of days to retain database backups"
  type        = number
  default     = 7
}

# CDN configuration
variable "enable_cdn" {
  description = "Enable Cloud CDN for static assets"
  type        = bool
  default     = true
}

variable "cdn_cache_mode" {
  description = "CDN cache mode"
  type        = string
  default     = "CACHE_ALL_STATIC"
  
  validation {
    condition = contains([
      "CACHE_ALL_STATIC",
      "USE_ORIGIN_HEADERS",
      "FORCE_CACHE_ALL"
    ], var.cdn_cache_mode)
    error_message = "CDN cache mode must be one of: CACHE_ALL_STATIC, USE_ORIGIN_HEADERS, FORCE_CACHE_ALL."
  }
}

# Security configuration
variable "enable_private_networking" {
  description = "Use private networking for all services"
  type        = bool
  default     = true
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection for critical resources"
  type        = bool
  default     = true
}

# Cost optimization
variable "preemptible_workers" {
  description = "Use preemptible instances for background workers"
  type        = bool
  default     = false
}

variable "auto_scaling_enabled" {
  description = "Enable auto-scaling for Cloud Run"
  type        = bool
  default     = true
}

# Development configuration
variable "enable_debug_features" {
  description = "Enable debug features (GraphQL playground, debug toolbar)"
  type        = bool
  default     = false
}

variable "cors_allowed_origins" {
  description = "CORS allowed origins"
  type        = list(string)
  default     = ["*"]
}

# Webhook configuration
variable "webhook_timeout" {
  description = "Webhook timeout in seconds"
  type        = number
  default     = 30
}

# Search configuration
variable "enable_elasticsearch" {
  description = "Enable Elasticsearch for advanced search"
  type        = bool
  default     = false
}

# Custom labels
variable "additional_labels" {
  description = "Additional labels to apply to all resources"
  type        = map(string)
  default     = {}
}

# Network configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC network"
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_cidr" {
  description = "CIDR block for application subnet"
  type        = string
  default     = "10.0.0.0/24"
}

variable "connector_cidr" {
  description = "CIDR block for VPC connector"
  type        = string
  default     = "10.8.0.0/28"
}