from fastmcp import FastMCP
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
from auth import GCPAuth

# Import all tools from the tools package with type annotations
from tools import (
    # Storage tools
    list_buckets as _list_buckets,
    create_bucket as _create_bucket,
    delete_bucket as _delete_bucket,
    # Compute tools
    list_instances as _list_instances,
    create_instance as _create_instance,
    delete_instance as _delete_instance,
    list_ip_addresses as _list_ip_addresses,
    list_persistent_disks as _list_persistent_disks,
    # Network tools
    list_vpc_networks_and_subnets as _list_vpc_networks_and_subnets,
    list_load_balancers as _list_load_balancers,
    # Billing/monitoring tools
    get_billing_cost as _get_billing_cost,
    get_metrics as _get_metrics
)

# Import response models for type safety
from models import (
    ErrorResponse,
    SuccessResponse,
    IPAddressResponse,
    PersistentDiskResponse,
    VPCNetworkResponse,
    LoadBalancerResponse,
    BillingCostResponse,
    MetricsResponse
)

# Initialize the MCP application
mcp = FastMCP()

# Initialize GCP provider with our authentication
gcp_auth = GCPAuth()
gcp_provider = gcp_auth.credentials

class ResourceRequest(BaseModel):
    """Base model for resource requests"""
    project_id: str
    region: Optional[str] = None
    zone: Optional[str] = None

# Storage Tools
@mcp.tool
def list_buckets(project_id: str) -> Union[List[str], Dict[str, Any]]:
    """List all storage buckets in a project"""
    result = _list_buckets(project_id)
    if isinstance(result, ErrorResponse):
        return result.dict()
    return result

@mcp.tool
def create_bucket(
    project_id: str,
    bucket_name: str,
    location: str,
    storage_class: str = "STANDARD",
    versioning: bool = False
) -> Dict[str, Any]:
    """Create a new storage bucket"""
    result = _create_bucket(project_id, bucket_name, location, storage_class, versioning)
    return result.dict()

@mcp.tool
def delete_bucket(project_id: str, bucket_name: str) -> Dict[str, Any]:
    """Delete a storage bucket"""
    result = _delete_bucket(project_id, bucket_name)
    return result.dict()

# Compute Tools
@mcp.tool
def list_instances(project_id: str, zone: Optional[str] = None) -> Union[List[str], Dict[str, Any]]:
    """List all compute instances in a project/zone"""
    result = _list_instances(project_id, zone)
    if isinstance(result, ErrorResponse):
        return result.dict()
    return result

@mcp.tool
def create_instance(
    project_id: str,
    zone: str,
    instance_name: str,
    machine_type: str,
    image_family: str,
    disk_size_gb: int = 10,
    network: str = "default",
    subnetwork: Optional[str] = None,
    tags: List[str] = [],
    service_account: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new compute instance"""
    result = _create_instance(
        project_id, zone, instance_name, machine_type, image_family,
        disk_size_gb, network, subnetwork, tags, service_account
    )
    return result.dict()

@mcp.tool
def delete_instance(project_id: str, zone: str, instance_name: str) -> Dict[str, Any]:
    """Delete a compute instance"""
    result = _delete_instance(project_id, zone, instance_name)
    return result.dict()

@mcp.tool
def list_ip_addresses(project_id: str, region: Optional[str] = None) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """List all IP addresses (both external and internal) in a project/region and their usage information"""
    result = _list_ip_addresses(project_id, region)
    if isinstance(result, ErrorResponse):
        return result.dict()
    return [ip.dict() for ip in result]

@mcp.tool
def list_persistent_disks(project_id: str, zone: Optional[str] = None) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """List all persistent disks in a project/zone and their attachment information"""
    result = _list_persistent_disks(project_id, zone)
    if isinstance(result, ErrorResponse):
        return result.dict()
    return [disk.dict() for disk in result]

# Network Tools
@mcp.tool
def list_vpc_networks_and_subnets(project_id: str) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """List all VPC networks and their subnets in a project, including region and subnet info."""
    result = _list_vpc_networks_and_subnets(project_id)
    if isinstance(result, ErrorResponse):
        return result.dict()
    return [vpc.dict() for vpc in result]

@mcp.tool
def list_load_balancers(project_id: str, region: Optional[str] = None) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """List all load balancers (forwarding rules) in a project, with type (external/internal) and associated IP addresses."""
    result = _list_load_balancers(project_id, region)
    if isinstance(result, ErrorResponse):
        return result.dict()
    return [lb.dict() for lb in result]

# Billing/Monitoring Tools
@mcp.tool
def get_billing_cost(
    project_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    group_by: List[str] = ["service"]
) -> Dict[str, Any]:
    """Get billing cost for a project using its linked billing account"""
    result = _get_billing_cost(project_id, start_date, end_date, group_by)
    return result.dict()

@mcp.tool
def get_metrics(
    project_id: str,
    metric_type: str,
    interval: str = "1h",
    aggregation: str = "mean"
) -> Dict[str, Any]:
    """Get monitoring metrics"""
    result = _get_metrics(project_id, metric_type, interval, aggregation)
    return result.dict()

if __name__ == "__main__":
    mcp.run()
