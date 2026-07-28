# Terraform Infrastructure as Code (IaC) configuration for SkyConcierge

terraform {
  required_version = ">= 1.3.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Enable Secret Manager API
resource "google_project_service" "secretmanager_api" {
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

# 2. Secret Manager Secret for GEMINI_API_KEY
resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "GEMINI_API_KEY"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager_api]
}

# 3. Cloud Storage bucket for persistent agent storage and artifacts
resource "google_storage_bucket" "agent_artifacts" {
  name                     = "${var.project_id}-skyconcierge-artifacts"
  location                 = var.region
  force_destroy            = false
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }
}
