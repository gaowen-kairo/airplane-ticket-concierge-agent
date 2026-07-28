output "gemini_secret_id" {
  description = "Resource ID of the Gemini API Key secret in Secret Manager."
  value       = google_secret_manager_secret.gemini_api_key.id
}

output "artifacts_bucket_url" {
  description = "GCS URL of the agent artifacts storage bucket."
  value       = google_storage_bucket.agent_artifacts.url
}
