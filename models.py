"""Pydantic models for type validation and data structures"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union, Literal
from datetime import datetime
from enum import Enum


# Enums for better type safety
class StorageClass(str, Enum):
    STANDARD = "STANDARD"
    NEARLINE = "NEARLINE"
    COLDLINE = "COLDLINE"
    ARCHIVE = "ARCHIVE"


class MachineFamily(str, Enum):
    E2 = "e2"
    N1 = "n1"
    N2 = "n2"
    N2D = "n2d"
    C2 = "c2"
    C2D = "c2d"
    M1 = "m1"
    M2 = "m2"


class DiskType(str, Enum):
    PD_STANDARD = "pd-standard"
    PD_SSD = "pd-ssd"
    PD_BALANCED = "pd-balanced"
    LOCAL_SSD = "local-ssd"


class InstanceStatus(str, Enum):
    PROVISIONING = "PROVISIONING"
    STAGING = "STAGING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    SUSPENDING = "SUSPENDING"
    SUSPENDED = "SUSPENDED"
    TERMINATED = "TERMINATED"


class AddressType(str, Enum):
    EXTERNAL = "EXTERNAL"
    INTERNAL = "INTERNAL"
    REGIONAL = "REGIONAL"
    GLOBAL = "GLOBAL"


class LoadBalancerType(str, Enum):
    EXTERNAL = "EXTERNAL"
    INTERNAL = "INTERNAL"


# Base request models
class BaseRequest(BaseModel):
    """Base model for all GCP requests"""
    project_id: str = Field(..., description="GCP project ID", min_length=6, max_length=63)

    @validator('project_id')
    def validate_project_id(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Project ID must contain only letters, numbers, hyphens, and underscores')
        return v


class RegionalRequest(BaseRequest):
    """Base model for regional resource requests"""
    region: Optional[str] = Field(None, description="GCP region (e.g., us-central1)")


class ZonalRequest(RegionalRequest):
    """Base model for zonal resource requests"""
    zone: Optional[str] = Field(None, description="GCP zone (e.g., us-central1-a)")


# Storage models
class BucketCreateRequest(BaseRequest):
    """Request model for creating a storage bucket"""
    bucket_name: str = Field(..., description="Bucket name", min_length=3, max_length=63)
    location: str = Field(..., description="Bucket location")
    storage_class: StorageClass = Field(StorageClass.STANDARD, description="Storage class")
    versioning: bool = Field(False, description="Enable versioning")

    @validator('bucket_name')
    def validate_bucket_name(cls, v):
        if not v.replace('-', '').replace('_', '').replace('.', '').isalnum():
            raise ValueError('Bucket name must contain only lowercase letters, numbers, hyphens, underscores, and dots')
        if v != v.lower():
            raise ValueError('Bucket name must be lowercase')
        return v


class BucketResponse(BaseModel):
    """Response model for bucket operations"""
    name: str
    location: str
    storage_class: str
    versioning_enabled: bool
    creation_time: Optional[datetime] = None


class BucketDeleteRequest(BaseRequest):
    """Request model for deleting a storage bucket"""
    bucket_name: str = Field(..., description="Bucket name to delete")


# Compute models
class InstanceCreateRequest(ZonalRequest):
    """Request model for creating a compute instance"""
    instance_name: str = Field(..., description="Instance name", min_length=1, max_length=63)
    machine_type: str = Field(..., description="Machine type (e.g., e2-medium)")
    image_family: str = Field(..., description="Image family (e.g., ubuntu-2004-lts)")
    disk_size_gb: int = Field(10, description="Boot disk size in GB", ge=10, le=65536)
    network: str = Field("default", description="Network name")
    subnetwork: Optional[str] = Field(None, description="Subnetwork name")
    tags: List[str] = Field(default_factory=list, description="Network tags")
    service_account: Optional[str] = Field(None, description="Service account email")

    @validator('instance_name')
    def validate_instance_name(cls, v):
        if not v.replace('-', '').isalnum():
            raise ValueError('Instance name must contain only lowercase letters, numbers, and hyphens')
        if v != v.lower():
            raise ValueError('Instance name must be lowercase')
        return v


class InstanceResponse(BaseModel):
    """Response model for instance information"""
    name: str
    id: Optional[str] = None
    status: InstanceStatus
    machine_type: str
    zone: str
    region: str
    creation_timestamp: Optional[str] = None
    network_interfaces: List[Dict[str, Any]] = Field(default_factory=list)
    disks: List[Dict[str, Any]] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class InstanceDeleteRequest(ZonalRequest):
    """Request model for deleting a compute instance"""
    instance_name: str = Field(..., description="Instance name to delete")


class IPAddressResponse(BaseModel):
    """Response model for IP address information"""
    name: str
    address: str
    region: Optional[str] = None
    zone: Optional[str] = None
    status: str
    in_use: bool
    used_by: Optional[List[str]] = None
    type: AddressType
    network: Optional[str] = None
    subnet: Optional[str] = None


class PersistentDiskResponse(BaseModel):
    """Response model for persistent disk information"""
    name: str
    id: Optional[str] = None
    size_gb: int
    status: str
    type: str
    type_description: Optional[str] = None
    zone: str
    region: str
    in_use: bool
    attached_to: List[Dict[str, Any]] = Field(default_factory=list)
    creation_timestamp: Optional[str] = None
    physical_block_size_bytes: Optional[int] = None
    source_image: Optional[str] = None
    source_snapshot: Optional[str] = None
    source_disk: Optional[str] = None
    labels: Dict[str, str] = Field(default_factory=dict)


# Network models
class SubnetResponse(BaseModel):
    """Response model for subnet information"""
    name: str
    id: Optional[str] = None
    region: str
    network: str
    ip_cidr_range: str
    gateway_address: Optional[str] = None
    secondary_ip_ranges: List[Dict[str, str]] = Field(default_factory=list)
    private_ip_google_access: Optional[bool] = None
    purpose: Optional[str] = None
    role: Optional[str] = None


class VPCNetworkResponse(BaseModel):
    """Response model for VPC network information"""
    name: str
    id: Optional[str] = None
    auto_create_subnetworks: Optional[bool] = None
    routing_config: Optional[str] = None
    subnets: List[SubnetResponse] = Field(default_factory=list)


class LoadBalancerResponse(BaseModel):
    """Response model for load balancer information"""
    name: str
    region: str
    type: LoadBalancerType
    ip_address: Optional[str] = None
    ip_protocol: Optional[str] = None
    network_tier: Optional[str] = None
    load_balancing_scheme: str
    target: Optional[str] = None
    description: Optional[str] = None


# Billing models
class BillingCostRequest(BaseRequest):
    """Request model for billing cost queries"""
    start_date: Optional[str] = Field(None, description="Start date in ISO format")
    end_date: Optional[str] = Field(None, description="End date in ISO format")
    group_by: List[str] = Field(["service"], description="Group by fields")


class CostAmount(BaseModel):
    """Model for cost amount with currency"""
    amount: float = Field(..., ge=0, description="Cost amount")
    currency: str = Field(..., description="Currency code")


class BillingCostResponse(BaseModel):
    """Response model for billing cost information"""
    success: bool
    project_id: str
    billing_account_id: Optional[str] = None
    time_range: Optional[Dict[str, str]] = None
    total_cost: Optional[CostAmount] = None
    costs_by_service: Dict[str, CostAmount] = Field(default_factory=dict)
    error: Optional[str] = None


# Monitoring models
class MetricsRequest(BaseRequest):
    """Request model for monitoring metrics"""
    metric_type: str = Field(..., description="Metric type to query")
    interval: str = Field("1h", description="Time interval")
    aggregation: str = Field("mean", description="Aggregation method")


class MetricsResponse(BaseModel):
    """Response model for monitoring metrics"""
    message: str
    project_id: str
    metric_type: str
    interval: str
    aggregation: str
    data: Optional[Dict[str, Any]] = None


# Generic response models
class SuccessResponse(BaseModel):
    """Generic success response"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Generic error response"""
    error: str
    success: bool = False
    details: Optional[Dict[str, Any]] = None
