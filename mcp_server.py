from fastmcp import FastMCP
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from auth import GCPAuth
from datetime import datetime, timedelta
from google.cloud import billing
from google.cloud.billing_v1 import CloudBillingClient, CloudCatalogClient
from google.cloud.billing_v1.types import cloud_catalog

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

@mcp.tool
def list_buckets(project_id: str) -> List[str]:
    """List all storage buckets in a project"""
    storage_client = gcp_auth.get_storage_client()
    buckets = storage_client.list_buckets(project=project_id)
    return [bucket.name for bucket in buckets]

@mcp.tool
def create_bucket(
    project_id: str,
    bucket_name: str,
    location: str,
    storage_class: str = "STANDARD",
    versioning: bool = False
) -> Dict[str, str]:
    """Create a new storage bucket"""
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

@mcp.tool
def delete_bucket(project_id: str, bucket_name: str) -> Dict[str, str]:
    """Delete a storage bucket"""
    storage_client = gcp_auth.get_storage_client()
    bucket = storage_client.bucket(bucket_name)
    bucket.delete()
    return {"message": f"Bucket {bucket_name} deleted successfully"}

@mcp.tool
def list_instances(project_id: str, zone: Optional[str] = None) -> List[str]:
    """List all compute instances in a project/zone"""
    compute_client = gcp_auth.get_compute_client()
    if zone:
        request = {
            "project": project_id,
            "zone": zone
        }
        instances = compute_client.list(request=request)
    else:
        instances = []
        # Get list of zones
        zones_client = gcp_auth.get_compute_client()
        zones_request = {"project": project_id}
        for zone in zones_client.list_zones(request=zones_request):
            request = {
                "project": project_id,
                "zone": zone.name
            }
            zone_instances = compute_client.list(request=request)
            instances.extend(zone_instances)
    return [instance.name for instance in instances]

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
) -> Dict[str, str]:
    """Create a new compute instance"""
    compute_client = gcp_auth.get_compute_client()
    # Implementation for instance creation
    return {"message": f"Instance {instance_name} creation initiated"}

@mcp.tool
def delete_instance(project_id: str, zone: str, instance_name: str) -> Dict[str, str]:
    """Delete a compute instance"""
    compute_client = gcp_auth.get_compute_client()
    compute_client.delete_instance(
        project=project_id,
        zone=zone,
        instance=instance_name
    )
    return {"message": f"Instance {instance_name} deleted successfully"}

@mcp.tool
def get_metrics(
    project_id: str,
    metric_type: str,
    interval: str = "1h",
    aggregation: str = "mean"
) -> Dict[str, Any]:
    """Get monitoring metrics"""
    monitoring_client = gcp_auth.get_monitoring_client()
    # Implementation for getting metrics
    return {"message": "Metrics retrieved", "project_id": project_id, "metric_type": metric_type}

@mcp.tool
def get_billing_cost(
    project_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    group_by: List[str] = ["service"]
) -> Dict[str, Any]:
    """Get billing cost for a project using its linked billing account"""
    try:
        billing_client = gcp_auth.get_billing_client()
        
        # Get project billing info to find the linked billing account
        project_name = f"projects/{project_id}"
        project_billing_info = billing_client.get_project_billing_info(name=project_name)
        
        if not project_billing_info.billing_enabled:
            return {
                "success": False,
                "error": "Billing is not enabled for this project",
                "project_id": project_id
            }
        
        # Get the billing account ID from the project's billing info
        billing_account_id = project_billing_info.billing_account_name.split('/')[-1]
        
        # Parse dates if provided, otherwise use last 30 days
        end = datetime.now()
        if end_date:
            end = datetime.fromisoformat(end_date)
        
        start = end - timedelta(days=30)  # Default to last 30 days
        if start_date:
            start = datetime.fromisoformat(start_date)
        
        # Get cost data using Cloud Billing API
        billing_data_client = CloudBillingClient()
        
        # Get the billing account costs
        billing_account_name = f"billingAccounts/{billing_account_id}"
        
        # Get the current month's costs
        costs = billing_data_client.get_billing_account(
            name=billing_account_name
        )
        
        # Get service costs
        service_costs = {}
        for service in costs.services:
            service_costs[service.name] = {
                'amount': float(service.cost.amount),
                'currency': service.cost.currency_code
            }
        
        return {
            "success": True,
            "project_id": project_id,
            "billing_account_id": billing_account_id,
            "time_range": {
                "start": start.isoformat(),
                "end": end.isoformat()
            },
            "total_cost": {
                "amount": float(costs.total_cost.amount),
                "currency": costs.total_cost.currency_code
            },
            "costs_by_service": service_costs
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get billing data: {str(e)}",
            "project_id": project_id,
            "billing_account_id": billing_account_id if 'billing_account_id' in locals() else None
        }

if __name__ == "__main__":
    mcp.run() 
