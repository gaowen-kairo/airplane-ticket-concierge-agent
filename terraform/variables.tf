variable "project_id" {
  description = "The GCP project ID to deploy resources into."
  type        = string
  default     = "skyconcierge-agent-project"
}

variable "region" {
  description = "GCP deployment region."
  type        = string
  default     = "us-central1"
}
