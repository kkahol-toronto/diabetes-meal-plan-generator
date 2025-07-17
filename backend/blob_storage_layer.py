"""blob_storage_layer.py
Standalone utility for saving and listing user-uploaded images in Azure Blob Storage
without modifying any existing project files.

How it works
============
• Every user gets their own virtual "folder" inside a single container named
  `user-images` (you will see blobs like `images/<user_id>/<uuid>_<filename>`).
• The code creates the container automatically if it doesn't exist.
• Public access level remains private; the helper returns a signed SAS URL
  (valid 24 h) that front-end / admins can use to view the file.

Functions exposed
-----------------
upload_user_image(user_id: str, image_bytes: bytes, filename: str) -> str
    → uploads the file and returns its blob URL (SAS).

list_user_images(user_id: str, limit: int | None = None) -> list[str]
    → returns blob names for that user.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta
from typing import List

from azure.storage.blob import (
    BlobServiceClient,
    ContentSettings,
    generate_blob_sas,
    BlobSasPermissions,
)
from dotenv import load_dotenv

load_dotenv()

# ------------ Config ------------ #
AZURE_BLOB_CONNECTION_STRING: str = (
    os.getenv("AZURE_BLOB_CONNECTION_STRING") or ""
)  # type: ignore[assignment]
BLOB_CONTAINER_NAME = "user-images"

# Fail fast if connection string missing in runtime
if not AZURE_BLOB_CONNECTION_STRING:
    raise RuntimeError(
        "AZURE_BLOB_CONNECTION_STRING env var is required for blob storage layer"
    )

_service_client = BlobServiceClient.from_connection_string(
    AZURE_BLOB_CONNECTION_STRING
)

# Ensure container exists (idempotent)
try:
    _container_client = _service_client.get_container_client(BLOB_CONTAINER_NAME)
    _container_client.get_container_properties()
except Exception:
    _container_client = _service_client.create_container(BLOB_CONTAINER_NAME)


# ------------ Helpers ------------ #

def _blob_name(user_id: str, filename: str) -> str:
    safe_name = filename.replace("/", "_")
    return f"images/{user_id}/{uuid.uuid4().hex}_{safe_name}"


def upload_user_image(user_id: str, image_bytes: bytes, filename: str) -> str:
    """Upload image and return a time-limited SAS URL (24h)."""
    blob_name = _blob_name(user_id, filename)
    content_type = "image/jpeg"
    if "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()
        content_type = f"image/{ext}"

    blob_client = _container_client.get_blob_client(blob_name)
    blob_client.upload_blob(
        image_bytes,
        overwrite=False,
        content_settings=ContentSettings(content_type=content_type),
    )

    sas_token = generate_blob_sas(
        account_name=_service_client.account_name,
        container_name=BLOB_CONTAINER_NAME,
        blob_name=blob_name,
        account_key=_service_client.credential.account_key,  # type: ignore[attr-defined]
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=24),
    )

    url = f"https://{_service_client.account_name}.blob.core.windows.net/{BLOB_CONTAINER_NAME}/{blob_name}?{sas_token}"
    return url


def list_user_images(user_id: str, limit: int | None = None) -> List[str]:
    prefix = f"images/{user_id}/"
    blobs = _container_client.list_blobs(name_starts_with=prefix)
    names: List[str] = [b.name for b in blobs]
    names.sort(reverse=True)
    return names[:limit] if limit else names 