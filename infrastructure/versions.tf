# Terraform version and provider constraints

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.4"
    }
  }
  
  # Uncomment and configure backend for production use
  # backend "gcs" {
  #   bucket = "your-terraform-state-bucket"
  #   prefix = "saleor/terraform/state"
  # }
}