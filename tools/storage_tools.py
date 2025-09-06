"""Storage-related GCP tools (Cloud Storage buckets)"""

from typing import List, Dict
from auth import GCPAuth


def list_buckets(project_id: str) -> List[str]:
    """List all storage buckets in a project"""
    gcp_auth = GCPAuth()
    storage_client = gcp_auth.get_storage_client()
    buckets = storage_client.list_buckets(project=project_id)
    return [bucket.name for bucket in buckets]


def create_bucket(
    project_id: str,
    bucket_name: str,
    location: str,
    storage_class: str = "STANDARD",
    versioning: bool = False
) -> Dict[str, str]:
    """Create a new storage bucket"""
    gcp_auth = GCPAuth()
    storage_client = gcp_auth.get_storage_client()
    bucket = storage_client.create_bucket(
        bucket_name,
        location=location,
        storage_class=storage_class
    )
    if versioning:
        bucket.versioning_enabled = True
        bucket.patch()
    return {"message": f"Bucket {bucket.name} created successfully"}


def delete_bucket(project_id: str, bucket_name: str) -> Dict[str, str]:
    """Delete a storage bucket"""
    gcp_auth = GCPAuth()
    storage_client = gcp_auth.get_storage_client()
    bucket = storage_client.bucket(bucket_name)
    bucket.delete()
    return {"message": f"Bucket {bucket_name} deleted successfully"}
