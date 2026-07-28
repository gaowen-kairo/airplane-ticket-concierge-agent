output "service_account_email" {
  description = "Email of the SkyConcierge dedicated service account."
  value       = google_service_account.skyconcierge_sa.email
}

output "gemini_secret_id" {
  description = "Secret Manager secret ID for GEMINI_API_KEY."
  value       = google_secret_manager_secret.gemini_api_key.secret_id
}

output "artifact_registry_url" {
  description = "Artifact Registry Docker repository URL."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.skyconcierge_repo.repository_id}"
}

output "artifacts_bucket_url" {
  description = "GCS Storage Bucket URL for persistent agent artifacts and backups."
  value       = google_storage_bucket.agent_artifacts.url
}

output "cloud_run_service_url" {
  description = "HTTP endpoint URL of the deployed Cloud Run agent service."
  value       = google_cloud_run_v2_service.skyconcierge_service.uri
}
