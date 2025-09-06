"""Compute-related GCP tools (instances, disks, IP addresses)"""

from typing import List, Dict, Any, Optional
from auth import GCPAuth
from google.cloud import compute_v1


def list_instances(project_id: str, zone: Optional[str] = None) -> List[str]:
    """List all compute instances in a project/zone"""
    gcp_auth = GCPAuth()
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
    gcp_auth = GCPAuth()
    compute_client = gcp_auth.get_compute_client()
    # Implementation for instance creation
    return {"message": f"Instance {instance_name} creation initiated"}


def delete_instance(project_id: str, zone: str, instance_name: str) -> Dict[str, str]:
    """Delete a compute instance"""
    gcp_auth = GCPAuth()
    compute_client = gcp_auth.get_compute_client()
    compute_client.delete_instance(
        project=project_id,
        zone=zone,
        instance=instance_name
    )
    return {"message": f"Instance {instance_name} deleted successfully"}


def list_ip_addresses(project_id: str, region: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all IP addresses (both external and internal) in a project/region and their usage information"""
    gcp_auth = GCPAuth()
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


def list_persistent_disks(project_id: str, zone: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all persistent disks in a project/zone and their attachment information"""
    gcp_auth = GCPAuth()
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
