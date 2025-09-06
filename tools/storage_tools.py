"""Storage-related GCP tools (Cloud Storage buckets) with improved type safety"""

from typing import List, Union
from auth import GCPAuth, GCPAuthError
from models import (
    BucketCreateRequest,
    BucketDeleteRequest,
    BucketResponse,
    SuccessResponse,
    ErrorResponse
)
import logging


def list_buckets(project_id: str) -> Union[List[str], ErrorResponse]:
    """
    List all storage buckets in a project.

    Args:
        project_id: GCP project ID

    Returns:
        List of bucket names or error response
    """
    try:
        gcp_auth = GCPAuth()
        storage_client = gcp_auth.get_storage_client()
        buckets = storage_client.list_buckets(project=project_id)
        return [bucket.name for bucket in buckets]
    except GCPAuthError as e:
        logging.error(f"Authentication error listing buckets: {e}")
        return ErrorResponse(error=f"Authentication failed: {str(e)}")
    except Exception as e:
        logging.error(f"Error listing buckets: {e}")
        return ErrorResponse(error=f"Failed to list buckets: {str(e)}")


def create_bucket(
    project_id: str,
    bucket_name: str,
    location: str,
    storage_class: str = "STANDARD",
    versioning: bool = False
) -> Union[SuccessResponse, ErrorResponse]:
    """
    Create a new storage bucket with validation.

    Args:
        project_id: GCP project ID
        bucket_name: Name for the new bucket
        location: Bucket location/region
        storage_class: Storage class (STANDARD, NEARLINE, COLDLINE, ARCHIVE)
        versioning: Enable versioning on the bucket

    Returns:
        Success response or error response
    """
    try:
        # Validate input using Pydantic model
        request = BucketCreateRequest(
            project_id=project_id,
            bucket_name=bucket_name,
            location=location,
            storage_class=storage_class,
            versioning=versioning
        )

        gcp_auth = GCPAuth()
        storage_client = gcp_auth.get_storage_client()

        bucket = storage_client.create_bucket(
            request.bucket_name,
            location=request.location,
            storage_class=request.storage_class.value
        )

        if request.versioning:
            bucket.versioning_enabled = True
            bucket.patch()

        return SuccessResponse(
            message=f"Bucket {bucket.name} created successfully in {request.location}"
        )

    except ValueError as e:
        logging.error(f"Validation error creating bucket: {e}")
        return ErrorResponse(error=f"Invalid input: {str(e)}")
    except GCPAuthError as e:
        logging.error(f"Authentication error creating bucket: {e}")
        return ErrorResponse(error=f"Authentication failed: {str(e)}")
    except Exception as e:
        logging.error(f"Error creating bucket: {e}")
        return ErrorResponse(error=f"Failed to create bucket: {str(e)}")


def delete_bucket(project_id: str, bucket_name: str) -> Union[SuccessResponse, ErrorResponse]:
    """
    Delete a storage bucket with validation.

    Args:
        project_id: GCP project ID
        bucket_name: Name of the bucket to delete

    Returns:
        Success response or error response
    """
    try:
        # Validate input using Pydantic model
        request = BucketDeleteRequest(
            project_id=project_id,
            bucket_name=bucket_name
        )

        gcp_auth = GCPAuth()
        storage_client = gcp_auth.get_storage_client()
        bucket = storage_client.bucket(request.bucket_name)
        bucket.delete()

        return SuccessResponse(
            message=f"Bucket {request.bucket_name} deleted successfully"
        )

    except ValueError as e:
        logging.error(f"Validation error deleting bucket: {e}")
        return ErrorResponse(error=f"Invalid input: {str(e)}")
    except GCPAuthError as e:
        logging.error(f"Authentication error deleting bucket: {e}")
        return ErrorResponse(error=f"Authentication failed: {str(e)}")
    except Exception as e:
        logging.error(f"Error deleting bucket: {e}")
        return ErrorResponse(error=f"Failed to delete bucket: {str(e)}")
