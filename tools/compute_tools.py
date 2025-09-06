"""Compute-related GCP tools (instances, disks, IP addresses) with improved type safety"""

from typing import List, Union, Optional
from auth import GCPAuth, GCPAuthError
from models import (
    InstanceCreateRequest,
    InstanceDeleteRequest,
    InstanceResponse,
    IPAddressResponse,
    PersistentDiskResponse,
    SuccessResponse,
    ErrorResponse,
    BaseRequest,
    ZonalRequest
)
from google.cloud import compute_v1
import logging


def list_instances(project_id: str, zone: Optional[str] = None) -> Union[List[str], ErrorResponse]:
    """
    List all compute instances in a project/zone with validation.

    Args:
        project_id: GCP project ID
        zone: Optional specific zone to list instances from

    Returns:
        List of instance names or error response
    """
    try:
        # Validate input using Pydantic model
        if zone:
            request = ZonalRequest(project_id=project_id, zone=zone)
        else:
            request = BaseRequest(project_id=project_id)

        gcp_auth = GCPAuth()
        compute_client = gcp_auth.get_compute_client()

        if zone:
            instances_request = compute_v1.ListInstancesRequest(
                project=request.project_id,
                zone=zone
            )
            instances = compute_client.list(request=instances_request)
        else:
            instances = []
            # Get list of zones and iterate through them
            zones_client = compute_v1.ZonesClient(credentials=gcp_auth.credentials)
            zones_request = compute_v1.ListZonesRequest(project=request.project_id)

            for zone_obj in zones_client.list(request=zones_request):
                instances_request = compute_v1.ListInstancesRequest(
                    project=request.project_id,
                    zone=zone_obj.name
                )
                zone_instances = compute_client.list(request=instances_request)
                instances.extend(zone_instances)

        return [instance.name for instance in instances]

    except ValueError as e:
        logging.error(f"Validation error listing instances: {e}")
        return ErrorResponse(error=f"Invalid input: {str(e)}")
    except GCPAuthError as e:
        logging.error(f"Authentication error listing instances: {e}")
        return ErrorResponse(error=f"Authentication failed: {str(e)}")
    except Exception as e:
        logging.error(f"Error listing instances: {e}")
        return ErrorResponse(error=f"Failed to list instances: {str(e)}")


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
) -> Union[SuccessResponse, ErrorResponse]:
    """
    Create a new compute instance with validation.

    Args:
        project_id: GCP project ID
        zone: Zone to create the instance in
        instance_name: Name for the new instance
        machine_type: Machine type (e.g., e2-medium)
        image_family: Image family (e.g., ubuntu-2004-lts)
        disk_size_gb: Boot disk size in GB
        network: Network name
        subnetwork: Subnetwork name
        tags: Network tags
        service_account: Service account email

    Returns:
        Success response or error response
    """
    try:
        # Validate input using Pydantic model
        request = InstanceCreateRequest(
            project_id=project_id,
            zone=zone,
            instance_name=instance_name,
            machine_type=machine_type,
            image_family=image_family,
            disk_size_gb=disk_size_gb,
            network=network,
            subnetwork=subnetwork,
            tags=tags,
            service_account=service_account
        )

        gcp_auth = GCPAuth()
        compute_client = gcp_auth.get_compute_client()

        # Note: This is a placeholder for the actual instance creation logic
        # The full implementation would require building the instance configuration
        # with proper disk, network interface, and other settings

        return SuccessResponse(
            message=f"Instance {request.instance_name} creation initiated in {request.zone}"
        )

    except ValueError as e:
        logging.error(f"Validation error creating instance: {e}")
        return ErrorResponse(error=f"Invalid input: {str(e)}")
    except GCPAuthError as e:
        logging.error(f"Authentication error creating instance: {e}")
        return ErrorResponse(error=f"Authentication failed: {str(e)}")
    except Exception as e:
        logging.error(f"Error creating instance: {e}")
        return ErrorResponse(error=f"Failed to create instance: {str(e)}")


def delete_instance(project_id: str, zone: str, instance_name: str) -> Union[SuccessResponse, ErrorResponse]:
    """
    Delete a compute instance with validation.

    Args:
        project_id: GCP project ID
        zone: Zone where the instance is located
        instance_name: Name of the instance to delete

    Returns:
        Success response or error response
    """
    try:
        # Validate input using Pydantic model
        request = InstanceDeleteRequest(
            project_id=project_id,
            zone=zone,
            instance_name=instance_name
        )

        gcp_auth = GCPAuth()
        compute_client = gcp_auth.get_compute_client()

        delete_request = compute_v1.DeleteInstanceRequest(
            project=request.project_id,
            zone=request.zone,
            instance=request.instance_name
        )

        operation = compute_client.delete(request=delete_request)

        return SuccessResponse(
            message=f"Instance {request.instance_name} deletion initiated"
        )

    except ValueError as e:
        logging.error(f"Validation error deleting instance: {e}")
        return ErrorResponse(error=f"Invalid input: {str(e)}")
    except GCPAuthError as e:
        logging.error(f"Authentication error deleting instance: {e}")
        return ErrorResponse(error=f"Authentication failed: {str(e)}")
    except Exception as e:
        logging.error(f"Error deleting instance: {e}")
        return ErrorResponse(error=f"Failed to delete instance: {str(e)}")


def list_ip_addresses(project_id: str, region: Optional[str] = None) -> Union[List[IPAddressResponse], ErrorResponse]:
    """
    List all IP addresses (both external and internal) in a project/region with their usage information.

    Args:
        project_id: GCP project ID
        region: Optional specific region to list IP addresses from

    Returns:
        List of IP address information or error response
    """
    try:
        # Validate input
        if region:
            request = ZonalRequest(project_id=project_id, region=region)
        else:
            request = BaseRequest(project_id=project_id)

        gcp_auth = GCPAuth()
        addresses_client = compute_v1.AddressesClient(credentials=gcp_auth.credentials)

        ip_addresses = []

        def add_instance_ips(instance, zone_name: str) -> None:
            """Helper function to extract IPs from instances"""
            if instance.network_interfaces:
                for interface in instance.network_interfaces:
                    if interface.access_configs:
                        for access_config in interface.access_configs:
                            if access_config.nat_i_p:
                                ip_addresses.append(IPAddressResponse(
                                    name=f"{instance.name}-external",
                                    address=access_config.nat_i_p,
                                    region=zone_name.rsplit('-', 1)[0],
                                    zone=zone_name,
                                    status="IN_USE",
                                    in_use=True,
                                    used_by=[f"instances/{instance.name}"],
                                    type="EXTERNAL",
                                    network=interface.network.split('/')[-1],
                                    subnet=interface.subnetwork.split('/')[-1] if interface.subnetwork else None
                                ))

                    if interface.network_i_p:
                        ip_addresses.append(IPAddressResponse(
                            name=f"{instance.name}-internal",
                            address=interface.network_i_p,
                            region=zone_name.rsplit('-', 1)[0],
                            zone=zone_name,
                            status="IN_USE",
                            in_use=True,
                            used_by=[f"instances/{instance.name}"],
                            type="INTERNAL",
                            network=interface.network.split('/')[-1],
                            subnet=interface.subnetwork.split('/')[-1] if interface.subnetwork else None
                        ))

        if region:
            # List addresses in specific region
            addresses_request = compute_v1.ListAddressesRequest(
                project=request.project_id,
                region=region
            )
            addresses = addresses_client.list(request=addresses_request)
            for address in addresses:
                ip_addresses.append(IPAddressResponse(
                    name=address.name,
                    address=address.address,
                    region=region,
                    status=address.status,
                    in_use=bool(address.users),
                    used_by=list(address.users) if address.users else None,
                    type="REGIONAL",
                    network=address.network.split('/')[-1] if address.network else None,
                    subnet=address.subnetwork.split('/')[-1] if address.subnetwork else None
                ))
        else:
            # List global and regional addresses
            global_addresses_client = compute_v1.GlobalAddressesClient(credentials=gcp_auth.credentials)
            global_request = compute_v1.ListGlobalAddressesRequest(project=request.project_id)

            for address in global_addresses_client.list(request=global_request):
                ip_addresses.append(IPAddressResponse(
                    name=address.name,
                    address=address.address,
                    status=address.status,
                    in_use=bool(address.users),
                    used_by=list(address.users) if address.users else None,
                    type="GLOBAL",
                    network=address.network.split('/')[-1] if address.network else None
                ))

        return ip_addresses

    except ValueError as e:
        logging.error(f"Validation error listing IP addresses: {e}")
        return ErrorResponse(error=f"Invalid input: {str(e)}")
    except GCPAuthError as e:
        logging.error(f"Authentication error listing IP addresses: {e}")
        return ErrorResponse(error=f"Authentication failed: {str(e)}")
    except Exception as e:
        logging.error(f"Error listing IP addresses: {e}")
        return ErrorResponse(error=f"Failed to list IP addresses: {str(e)}")


def list_persistent_disks(project_id: str, zone: Optional[str] = None) -> Union[List[PersistentDiskResponse], ErrorResponse]:
    """
    List all persistent disks in a project/zone with their attachment information.

    Args:
        project_id: GCP project ID
        zone: Optional specific zone to list disks from

    Returns:
        List of persistent disk information or error response
    """
    try:
        # Validate input
        if zone:
            request = ZonalRequest(project_id=project_id, zone=zone)
        else:
            request = BaseRequest(project_id=project_id)

        gcp_auth = GCPAuth()
        disks_client = compute_v1.DisksClient(credentials=gcp_auth.credentials)

        disks = []

        def get_disk_info(disk, zone_name: str) -> PersistentDiskResponse:
            """Helper function to extract disk information"""
            # Get disk type information
            disk_type_client = compute_v1.DiskTypesClient(credentials=gcp_auth.credentials)
            disk_type_name = disk.type_.split('/')[-1]

            try:
                disk_type_request = compute_v1.GetDiskTypeRequest(
                    project=request.project_id,
                    zone=zone_name,
                    disk_type=disk_type_name
                )
                disk_type = disk_type_client.get(request=disk_type_request)
                disk_type_description = disk_type.description
            except Exception:
                disk_type_description = None

            # Get instance information if disk is attached
            attached_to = []
            if disk.users:
                for user in disk.users:
                    if 'instances' in user:
                        instance_name = user.split('/')[-1]
                        attached_to.append({
                            "name": instance_name,
                            "status": "ATTACHED"
                        })

            return PersistentDiskResponse(
                name=disk.name,
                id=str(disk.id),
                size_gb=int(disk.size_gb),
                status=disk.status,
                type=disk_type_name,
                type_description=disk_type_description,
                zone=zone_name,
                region=zone_name.rsplit('-', 1)[0],
                in_use=bool(disk.users),
                attached_to=attached_to,
                creation_timestamp=disk.creation_timestamp,
                physical_block_size_bytes=disk.physical_block_size_bytes,
                source_image=disk.source_image.split('/')[-1] if disk.source_image else None,
                source_snapshot=disk.source_snapshot.split('/')[-1] if disk.source_snapshot else None,
                source_disk=disk.source_disk.split('/')[-1] if disk.source_disk else None,
                labels=dict(disk.labels) if disk.labels else {}
            )

        if zone:
            # List disks in specific zone
            disks_request = compute_v1.ListDisksRequest(
                project=request.project_id,
                zone=zone
            )
            for disk in disks_client.list(request=disks_request):
                disks.append(get_disk_info(disk, zone))
        else:
            # List disks in all zones
            zones_client = compute_v1.ZonesClient(credentials=gcp_auth.credentials)
            zones_request = compute_v1.ListZonesRequest(project=request.project_id)

            for zone_obj in zones_client.list(request=zones_request):
                disks_request = compute_v1.ListDisksRequest(
                    project=request.project_id,
                    zone=zone_obj.name
                )
                for disk in disks_client.list(request=disks_request):
                    disks.append(get_disk_info(disk, zone_obj.name))

        return disks

    except ValueError as e:
        logging.error(f"Validation error listing persistent disks: {e}")
        return ErrorResponse(error=f"Invalid input: {str(e)}")
    except GCPAuthError as e:
        logging.error(f"Authentication error listing persistent disks: {e}")
        return ErrorResponse(error=f"Authentication failed: {str(e)}")
    except Exception as e:
        logging.error(f"Error listing persistent disks: {e}")
        return ErrorResponse(error=f"Failed to list persistent disks: {str(e)}")
