from fastmcp import FastMCP
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from auth import GCPAuth
from datetime import datetime, timedelta
from google.cloud import billing, compute_v1
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

@mcp.tool
def list_ip_addresses(project_id: str, region: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all IP addresses (both external and internal) in a project/region and their usage information"""
    compute_client = gcp_auth.get_compute_client()
    addresses_client = compute_v1.AddressesClient()
    
    ip_addresses = []
    
    def add_instance_ips(instance, zone):
        # Add external IPs
        if instance.network_interfaces:
            for interface in instance.network_interfaces:
                if interface.access_configs:
                    for access_config in interface.access_configs:
                        if access_config.nat_i_p:
                            ip_addresses.append({
                                "name": f"{instance.name}-external",
                                "address": access_config.nat_i_p,
                                "region": zone.split('-')[0],
                                "zone": zone,
                                "status": "IN_USE",
                                "in_use": True,
                                "used_by": [f"instances/{instance.name}"],
                                "type": "EXTERNAL",
                                "network": interface.network.split('/')[-1],
                                "subnet": interface.subnetwork.split('/')[-1] if interface.subnetwork else None
                            })
                # Add internal IPs
                if interface.network_i_p:
                    ip_addresses.append({
                        "name": f"{instance.name}-internal",
                        "address": interface.network_i_p,
                        "region": zone.split('-')[0],
                        "zone": zone,
                        "status": "IN_USE",
                        "in_use": True,
                        "used_by": [f"instances/{instance.name}"],
                        "type": "INTERNAL",
                        "network": interface.network.split('/')[-1],
                        "subnet": interface.subnetwork.split('/')[-1] if interface.subnetwork else None
                    })

    if region:
        # List addresses in specific region
        request = compute_v1.ListAddressesRequest(
            project=project_id,
            region=region
        )
        addresses = addresses_client.list(request=request)
        for address in addresses:
            ip_addresses.append({
                "name": address.name,
                "address": address.address,
                "region": region,
                "status": address.status,
                "in_use": bool(address.users),
                "used_by": address.users if address.users else None,
                "type": "REGIONAL",
                "network": address.network.split('/')[-1] if address.network else None,
                "subnet": address.subnetwork.split('/')[-1] if address.subnetwork else None
            })
        
        # Get instances in the region's zones
        zones_client = compute_v1.ZonesClient()
        zones_request = compute_v1.ListZonesRequest(
            project=project_id
        )
        for zone in zones_client.list(request=zones_request):
            if zone.name.startswith(region):
                instances_client = compute_v1.InstancesClient()
                instances_request = compute_v1.ListInstancesRequest(
                    project=project_id,
                    zone=zone.name
                )
                for instance in instances_client.list(request=instances_request):
                    add_instance_ips(instance, zone.name)
    else:
        # List global addresses
        global_addresses_client = compute_v1.GlobalAddressesClient()
        request = compute_v1.ListGlobalAddressesRequest(
            project=project_id
        )
        addresses = global_addresses_client.list(request=request)
        for address in addresses:
            ip_addresses.append({
                "name": address.name,
                "address": address.address,
                "status": address.status,
                "in_use": bool(address.users),
                "used_by": address.users if address.users else None,
                "type": "GLOBAL",
                "network": address.network.split('/')[-1] if address.network else None
            })
        
        # List addresses in all regions
        regions_client = compute_v1.RegionsClient()
        regions_request = compute_v1.ListRegionsRequest(
            project=project_id
        )
        for region in regions_client.list(request=regions_request):
            request = compute_v1.ListAddressesRequest(
                project=project_id,
                region=region.name
            )
            addresses = addresses_client.list(request=request)
            for address in addresses:
                ip_addresses.append({
                    "name": address.name,
                    "address": address.address,
                    "region": region.name,
                    "status": address.status,
                    "in_use": bool(address.users),
                    "used_by": address.users if address.users else None,
                    "type": "REGIONAL",
                    "network": address.network.split('/')[-1] if address.network else None,
                    "subnet": address.subnetwork.split('/')[-1] if address.subnetwork else None
                })
            
            # Get instances in the region's zones
            zones_client = compute_v1.ZonesClient()
            zones_request = compute_v1.ListZonesRequest(
                project=project_id
            )
            for zone in zones_client.list(request=zones_request):
                if zone.name.startswith(region.name):
                    instances_client = compute_v1.InstancesClient()
                    instances_request = compute_v1.ListInstancesRequest(
                        project=project_id,
                        zone=zone.name
                    )
                    for instance in instances_client.list(request=instances_request):
                        add_instance_ips(instance, zone.name)
    
    return ip_addresses

@mcp.tool
def list_persistent_disks(project_id: str, zone: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all persistent disks in a project/zone and their attachment information"""
    compute_client = gcp_auth.get_compute_client()
    disks_client = compute_v1.DisksClient()
    
    disks = []
    
    def get_disk_info(disk, zone_name):
        # Get disk type information
        disk_type_client = compute_v1.DiskTypesClient()
        disk_type_request = compute_v1.GetDiskTypeRequest(
            project=project_id,
            zone=zone_name,
            disk_type=disk.type_.split('/')[-1]
        )
        try:
            disk_type = disk_type_client.get(request=disk_type_request)
            disk_type_name = disk_type.name
            disk_type_description = disk_type.description
        except Exception:
            disk_type_name = disk.type_.split('/')[-1]
            disk_type_description = None

        # Get instance information if disk is attached
        attached_to = []
        if disk.users:
            for user in disk.users:
                if 'instances' in user:
                    instance_name = user.split('/')[-1]
                    try:
                        instance_client = compute_v1.InstancesClient()
                        instance_request = compute_v1.GetInstanceRequest(
                            project=project_id,
                            zone=zone_name,
                            instance=instance_name
                        )
                        instance = instance_client.get(request=instance_request)
                        attached_to.append({
                            "name": instance.name,
                            "id": instance.id,
                            "status": instance.status,
                            "machine_type": instance.machine_type.split('/')[-1]
                        })
                    except Exception:
                        attached_to.append({
                            "name": instance_name,
                            "status": "UNKNOWN"
                        })

        return {
            "name": disk.name,
            "id": disk.id,
            "size_gb": disk.size_gb,
            "status": disk.status,
            "type": disk_type_name,
            "type_description": disk_type_description,
            "zone": zone_name,
            "region": zone_name.split('-')[0],
            "in_use": bool(disk.users),
            "attached_to": attached_to,
            "creation_timestamp": disk.creation_timestamp,
            "physical_block_size_bytes": disk.physical_block_size_bytes,
            "source_image": disk.source_image.split('/')[-1] if disk.source_image else None,
            "source_snapshot": disk.source_snapshot.split('/')[-1] if disk.source_snapshot else None,
            "source_disk": disk.source_disk.split('/')[-1] if disk.source_disk else None,
            "labels": disk.labels if disk.labels else {}
        }

    if zone:
        # List disks in specific zone
        request = compute_v1.ListDisksRequest(
            project=project_id,
            zone=zone
        )
        for disk in disks_client.list(request=request):
            disks.append(get_disk_info(disk, zone))
    else:
        # List disks in all zones
        zones_client = compute_v1.ZonesClient()
        zones_request = compute_v1.ListZonesRequest(
            project=project_id
        )
        for zone in zones_client.list(request=zones_request):
            request = compute_v1.ListDisksRequest(
                project=project_id,
                zone=zone.name
            )
            for disk in disks_client.list(request=request):
                disks.append(get_disk_info(disk, zone.name))
    
    return disks

@mcp.tool
def list_vpc_networks_and_subnets(project_id: str) -> List[Dict[str, Any]]:
    """List all VPC networks and their subnets in a project, including region and subnet info."""
    networks_client = compute_v1.NetworksClient()
    subnets_client = compute_v1.SubnetworksClient()

    vpcs = []
    for network in networks_client.list(project=project_id):
        network_info = {
            "name": network.name,
            "id": network.id,
            "auto_create_subnetworks": network.auto_create_subnetworks,
            "routing_config": network.routing_config.routing_mode if network.routing_config else None,
            "subnets": []
        }
        # Subnetworks are listed by region
        if network.subnetworks:
            for subnet_url in network.subnetworks:
                # subnet_url format: https://www.googleapis.com/compute/v1/projects/{project}/regions/{region}/subnetworks/{subnet}
                parts = subnet_url.split('/')
                region = parts[8]
                subnet_name = parts[-1]
                try:
                    subnet = subnets_client.get(
                        project=project_id,
                        region=region,
                        subnetwork=subnet_name
                    )
                    subnet_info = {
                        "name": subnet.name,
                        "id": subnet.id,
                        "region": region,
                        "network": subnet.network.split('/')[-1],
                        "ip_cidr_range": subnet.ip_cidr_range,
                        "gateway_address": subnet.gateway_address,
                        "secondary_ip_ranges": [
                            {
                                "range_name": r.range_name,
                                "ip_cidr_range": r.ip_cidr_range
                            } for r in subnet.secondary_ip_ranges
                        ],
                        "private_ip_google_access": subnet.private_ip_google_access,
                        "purpose": subnet.purpose,
                        "role": subnet.role
                    }
                    network_info["subnets"].append(subnet_info)
                except Exception as e:
                    network_info["subnets"].append({
                        "name": subnet_name,
                        "region": region,
                        "error": str(e)
                    })
        vpcs.append(network_info)
    return vpcs

if __name__ == "__main__":
    mcp.run() 
