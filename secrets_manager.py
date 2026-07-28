"""Secure Secret Manager Integration Module.

Provides integration with Google Cloud Secret Manager and environment key stores
to ensure API keys and database credentials are never hardcoded in source code or repositories.
"""

import os
from typing import Optional
from logging_tracing import logger


def fetch_secret_from_gcp_secret_manager(secret_id: str, project_id: Optional[str] = None) -> Optional[str]:
    """Attempts to retrieve secret value from GCP Secret Manager API.

    Args:
        secret_id: The secret name ID in Secret Manager.
        project_id: Optional GCP project ID. Reads GCP_PROJECT env var if omitted.

    Returns:
        Secret string if successfully retrieved, None otherwise.
    """
    gcp_project = project_id or os.environ.get("GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not gcp_project:
        return None

    try:
        from google.cloud import secretmanager
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{gcp_project}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        secret_val = response.payload.data.decode("UTF-8")
        logger.log("INFO", f"Successfully fetched secret '{secret_id}' from GCP Secret Manager.")
        return secret_val
    except Exception as e:
        logger.log("WARN", f"GCP Secret Manager lookup for '{secret_id}' skipped or unavailable: {e}")
        return None


def get_secret(secret_name: str, default: Optional[str] = None) -> Optional[str]:
    """Retrieves secret string prioritizing Secret Manager -> Environment Variables -> Default Fallback.

    Args:
        secret_name: Name of the secret (e.g., 'GEMINI_API_KEY', 'DATABASE_URL').
        default: Optional fallback default string if secret is not set.

    Returns:
        Secret string value.
    """
    # 1. Check GCP Secret Manager first if available
    gcp_secret = fetch_secret_from_gcp_secret_manager(secret_name)
    if gcp_secret:
        return gcp_secret

    # 2. Fallback to Environment Variables
    env_secret = os.environ.get(secret_name)
    if env_secret:
        logger.log("INFO", f"Loaded secret '{secret_name}' from environment variable.")
        return env_secret

    # 3. Return default fallback
    if default:
        logger.log("WARN", f"Secret '{secret_name}' not found in Secret Manager or env. Using default fallback.")
        return default

    logger.log("WARN", f"Secret '{secret_name}' is not configured.")
    return None
