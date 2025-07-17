"""image_storage_layer.py
New, self-contained helper for saving and fetching user-uploaded food images in Azure Cosmos DB.
This does NOT modify existing code – import and use where needed.

Key points
-----------
1.  Uses the same connection string as `backend/database.py`.
2.  Creates (if missing) a dedicated container called `user_images` with
    partition-key `/user_folder`.
3.  Each stored image document structure:
        id: <uuid>
        user_id: <user’s id>
        user_folder: images_<user_id>   # acts like a folder
        created_at: ISO timestamp
        filename: original filename provided by client
        image_base64: data:image/<ext>;base64,...
4.  Helper functions:
        save_user_image(user_id, image_bytes, filename) -> str  # returns document id
        get_images_for_user(user_id, limit=None) -> list[dict]
        get_image_by_id(image_id, user_id) -> dict | None

Admins can query all users or a specific user_folder later to inspect images.
"""

import base64
import uuid
import os
from datetime import datetime
from typing import List, Optional

from azure.cosmos import CosmosClient, PartitionKey
from dotenv import load_dotenv

# Reuse env variables
load_dotenv()
# Fall back to empty string so type checker accepts str, runtime will still raise if not set
COSMOS_CONNECTION_STRING: str = os.getenv("COSMO_DB_CONNECTION_STRING") or ""
COSMOS_DB_NAME = "diabetes_diet_manager"  # Same DB as rest of project
IMAGES_CONTAINER_NAME = "user_images"

# ---------------- Initialisation ---------------- #
_client = CosmosClient.from_connection_string(COSMOS_CONNECTION_STRING)
_db = _client.get_database_client(COSMOS_DB_NAME)

# Ensure container exists (idempotent)
try:
    _images_container = _db.get_container_client(IMAGES_CONTAINER_NAME)
    _images_container.read()  # Will raise if not exists
except Exception:
    # Create with /user_folder as the partition key for efficient per-user querying
    _images_container = _db.create_container_if_not_exists(
        id=IMAGES_CONTAINER_NAME,
        partition_key=PartitionKey(path="/user_folder"),
        offer_throughput=400,
    )

# ---------------- Public Helpers ---------------- #

def _to_base64_data_uri(image_bytes: bytes, filename: str) -> str:
    """Convert raw bytes to data-uri preserving extension (default jpg)."""
    ext = (filename.split(".")[-1] if "." in filename else "jpg").lower()
    b64 = base64.b64encode(image_bytes).decode()
    return f"data:image/{ext};base64,{b64}"


def save_user_image(user_id: str, image_bytes: bytes, filename: str) -> str:
    """Save image and return its document id."""
    doc_id = str(uuid.uuid4())
    folder_name = f"images_{user_id}"
    data_uri = _to_base64_data_uri(image_bytes, filename)

    doc = {
        "id": doc_id,
        "user_id": user_id,
        "user_folder": folder_name,  # partition key – functions like a folder
        "created_at": datetime.utcnow().isoformat(),
        "filename": filename,
        "image_base64": data_uri,
    }

    _images_container.create_item(body=doc)
    return doc_id


def get_images_for_user(user_id: str, limit: Optional[int] = None) -> List[dict]:
    folder_name = f"images_{user_id}"
    top_clause = f"TOP {limit} " if limit else ""
    query = (
        f"SELECT {top_clause}* FROM c WHERE c.user_folder = '{folder_name}' "
        "ORDER BY c.created_at DESC"
    )
    return list(_images_container.query_items(query=query, enable_cross_partition_query=False))


def get_image_by_id(image_id: str, user_id: str) -> Optional[dict]:
    folder_name = f"images_{user_id}"
    try:
        return _images_container.read_item(item=image_id, partition_key=folder_name)
    except Exception:
        return None 