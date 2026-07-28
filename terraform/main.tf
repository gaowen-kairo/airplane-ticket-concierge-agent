# Infrastructure as Code (IaC) Terraform Configuration for SkyConcierge AI Agent

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

# 1. Enable Required GCP APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "secretmanager.googleapis.com",
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "iam.googleapis.com",
  ])
  service            = each.key
  disable_on_destroy = false
}

# 2. Service Account for SkyConcierge Execution
resource "google_service_account" "skyconcierge_sa" {
  account_id   = "skyconcierge-agent-sa"
  display_name = "SkyConcierge Agent Service Account"
  description  = "Service Account for running SkyConcierge AI Agent with least-privilege permissions."
  depends_on   = [google_project_service.required_apis]
}

# 3. Secret Manager Secret for GEMINI_API_KEY
resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "GEMINI_API_KEY"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

# Grant Service Account secretAccessor role on the API key secret
resource "google_secret_manager_secret_iam_member" "secret_access" {
  secret_id = google_secret_manager_secret.gemini_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.skyconcierge_sa.email}"
}

# 4. Artifact Registry Repository for Docker Container Images
resource "google_artifact_registry_repository" "skyconcierge_repo" {
  location      = var.region
  repository_id = "skyconcierge-repo"
  description   = "Docker container repository for SkyConcierge Agent images"
  format        = "DOCKER"

  depends_on = [google_project_service.required_apis]
}

# 5. Cloud Storage Bucket for Persistent Agent Artifacts & Database Backups
resource "google_storage_bucket" "agent_artifacts" {
  name                        = "${var.project_id}-skyconcierge-artifacts"
  location                    = var.region
  force_destroy               = false
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }
}

# Grant Service Account objectAdmin on the artifacts bucket
resource "google_storage_bucket_iam_member" "bucket_access" {
  bucket = google_storage_bucket.agent_artifacts.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.skyconcierge_sa.email}"
}

# 6. Cloud Run v2 Service for SkyConcierge Deployment
resource "google_cloud_run_v2_service" "skyconcierge_service" {
  name     = "skyconcierge-agent-service"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.skyconcierge_sa.email

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.skyconcierge_repo.repository_id}/agent:latest"

      env {
        name  = "GCP_PROJECT"
        value = var.project_id
      }

      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gemini_api_key.secret_id
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = "2000m"
          memory = "2Gi"
        }
      }
    }
  }

  depends_on = [
    google_project_service.required_apis,
    google_secret_manager_secret_iam_member.secret_access,
  ]
}
