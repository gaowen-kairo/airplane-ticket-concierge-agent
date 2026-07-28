# Infrastructure as Code (IaC) - Terraform for SkyConcierge

This directory contains complete Terraform configurations for provisioning Google Cloud Platform (GCP) infrastructure to run the **SkyConcierge AI Agent** in production.

---

## Managed GCP Infrastructure Resources

1. **GCP APIs**: `secretmanager`, `run`, `artifactregistry`, `iam`
2. **Identity & Access Management (IAM)**:
   - Service Account: `skyconcierge-agent-sa`
   - Least-privilege IAM bindings (`roles/secretmanager.secretAccessor`, `roles/storage.objectAdmin`)
3. **Secret Manager**:
   - `GEMINI_API_KEY` secret storage and automatic binding to Cloud Run
4. **Artifact Registry**:
   - Docker container image repository (`skyconcierge-repo`)
5. **Cloud Storage**:
   - Version-enabled GCS bucket (`skyconcierge-artifacts`) for persistent agent data and database backups
6. **Cloud Run v2 Service**:
   - Scalable serverless service hosting the SkyConcierge AI Agent container

---

## Deployment Quickstart

### 1. Prerequisites

- [Terraform CLI](https://developer.hashicorp.com/terraform/downloads) (v1.3.0+)
- [Google Cloud SDK (gcloud CLI)](https://cloud.google.com/sdk/docs/install)
- Authenticate to GCP:
  ```bash
  gcloud auth application-default login
  ```

### 2. Configure Variables

Copy the example variables file:
```bash
cp terraform.tfvars.example terraform.tfvars
```
Edit `terraform.tfvars` with your GCP project ID and region.

### 3. Initialize & Deploy

```bash
# Initialize Terraform provider and modules
terraform init

# Validate configuration syntax
terraform validate

# Inspect deployment execution plan
terraform plan

# Apply changes to provision resources
terraform apply
```

### 4. Populate Secret Value

After provisioning Secret Manager, populate the `GEMINI_API_KEY` secret:
```bash
gcloud secrets versions add GEMINI_API_KEY --data-file=- <<EOF
YOUR_GEMINI_API_KEY_HERE
EOF
```

---

## Outputs

- `cloud_run_service_url`: Public HTTP endpoint for the SkyConcierge Agent service
- `gemini_secret_id`: Secret Manager resource ID
- `artifact_registry_url`: Container repository path for Docker pushes
- `artifacts_bucket_url`: GCS Storage bucket URI
