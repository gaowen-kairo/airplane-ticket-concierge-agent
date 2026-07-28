variable "project_id" {
  description = "The GCP project ID where SkyConcierge infrastructure will be deployed."
  type        = string
  default     = "skyconcierge-agent-project"
}

variable "region" {
  description = "GCP deployment region for Cloud Run, Artifact Registry, and Storage."
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment environment stage (development, staging, production)."
  type        = string
  default     = "production"
}
