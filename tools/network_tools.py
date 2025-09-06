"""Network-related GCP tools (VPC networks, subnets, load balancers) with improved type safety"""

from typing import List, Union, Optional
from auth import GCPAuth, GCPAuthError
from models import (
    VPCNetworkResponse,
    SubnetResponse,
    LoadBalancerResponse,
    BaseRequest,
    RegionalRequest,
    ErrorResponse
)
from google.cloud import compute_v1
import logging


def list_vpc_networks_and_subnets(project_id: str) -> Union[List[VPCNetworkResponse], ErrorResponse]:
    """
    List all VPC networks and their subnets in a project with validation.

    Args:
        project_id: GCP project ID

    Returns:
        List of VPC network information or error response
    """
    try:
        # Validate input using Pydantic model
        request = BaseRequest(project_id=project_id)

        gcp_auth = GCPAuth()
        networks_client = compute_v1.NetworksClient(credentials=gcp_auth.credentials)
        subnets_client = compute_v1.SubnetworksClient(credentials=gcp_auth.credentials)

        vpcs = []

        for network in networks_client.list(project=request.project_id):
            subnets = []

            # Process subnetworks if they exist
            if network.subnetworks:
                for subnet_url in network.subnetworks:
                    # Parse subnet URL to extract region and subnet name
                    # Format: https://www.googleapis.com/compute/v1/projects/{project}/regions/{region}/subnetworks/{subnet}
                    parts = subnet_url.split('/')
                    if len(parts) >= 10:
                        region = parts[8]
                        subnet_name = parts[-1]

                        try:
                            subnet = subnets_client.get(
                                project=request.project_id,
                                region=region,
                                subnetwork=subnet_name
                            )

                            subnet_info = SubnetResponse(
                                name=subnet.name,
                                id=str(subnet.id) if subnet.id else None,
                                region=region,
                                network=subnet.network.split('/')[-1],
                                ip_cidr_range=subnet.ip_cidr_range,
                                gateway_address=subnet.gateway_address,
                                secondary_ip_ranges=[
                                    {
                                        "range_name": r.range_name,
                                        "ip_cidr_range": r.ip_cidr_range
                                    } for r in subnet.secondary_ip_ranges
                                ],
                                private_ip_google_access=subnet.private_ip_google_access,
                                purpose=subnet.purpose,
                                role=subnet.role
                            )
                            subnets.append(subnet_info)

                        except Exception as e:
                            logging.warning(f"Failed to get subnet {subnet_name} in region {region}: {e}")
                            # Add a basic subnet entry with error information
                            subnet_info = SubnetResponse(
                                name=subnet_name,
                                region=region,
                                network=network.name,
                                ip_cidr_range="unknown"
                            )
                            subnets.append(subnet_info)

            network_info = VPCNetworkResponse(
                name=network.name,
                id=str(network.id) if network.id else None,
                auto_create_subnetworks=network.auto_create_subnetworks,
                routing_config=network.routing_config.routing_mode if network.routing_config else None,
                subnets=subnets
            )
            vpcs.append(network_info)

        return vpcs

    except ValueError as e:
        logging.error(f"Validation error listing VPC networks: {e}")
        return ErrorResponse(error=f"Invalid input: {str(e)}")
    except GCPAuthError as e:
        logging.error(f"Authentication error listing VPC networks: {e}")
        return ErrorResponse(error=f"Authentication failed: {str(e)}")
    except Exception as e:
        logging.error(f"Error listing VPC networks: {e}")
        return ErrorResponse(error=f"Failed to list VPC networks: {str(e)}")


def list_load_balancers(project_id: str, region: Optional[str] = None) -> Union[List[LoadBalancerResponse], ErrorResponse]:
    """
    List all load balancers (forwarding rules) in a project with validation.

    Args:
        project_id: GCP project ID
        region: Optional specific region to list load balancers from

    Returns:
        List of load balancer information or error response
    """
    try:
        # Validate input using Pydantic model
        if region:
            request = RegionalRequest(project_id=project_id, region=region)
        else:
            request = BaseRequest(project_id=project_id)

        gcp_auth = GCPAuth()
        forwarding_rules_client = compute_v1.ForwardingRulesClient(credentials=gcp_auth.credentials)
        load_balancers = []

        def parse_rule(rule, region_name: Optional[str] = None) -> LoadBalancerResponse:
            """Helper function to parse forwarding rule into LoadBalancerResponse"""
            lb_type = "EXTERNAL" if rule.load_balancing_scheme == "EXTERNAL" else "INTERNAL"
            ip_address = getattr(rule, "IPAddress", None)
            ip_protocol = getattr(rule, "IPProtocol", None)

            return LoadBalancerResponse(
                name=rule.name,
                region=region_name or "global",
                type=lb_type,
                ip_address=ip_address,
                ip_protocol=ip_protocol,
                network_tier=getattr(rule, "network_tier", None),
                load_balancing_scheme=rule.load_balancing_scheme,
                target=rule.target,
                description=rule.description
            )

        if region:
            # List forwarding rules in specific region
            rules_request = compute_v1.ListForwardingRulesRequest(
                project=request.project_id,
                region=region
            )
            for rule in forwarding_rules_client.list(request=rules_request):
                load_balancers.append(parse_rule(rule, region))
        else:
            # List all regional forwarding rules
            regions_client = compute_v1.RegionsClient(credentials=gcp_auth.credentials)
            regions_request = compute_v1.ListRegionsRequest(project=request.project_id)

            for region_obj in regions_client.list(request=regions_request):
                region_name = region_obj.name
                rules_request = compute_v1.ListForwardingRulesRequest(
                    project=request.project_id,
                    region=region_name
                )
                for rule in forwarding_rules_client.list(request=rules_request):
                    load_balancers.append(parse_rule(rule, region_name))

            # List global forwarding rules
            global_rules_client = compute_v1.GlobalForwardingRulesClient(credentials=gcp_auth.credentials)
            global_request = compute_v1.ListGlobalForwardingRulesRequest(project=request.project_id)

            for rule in global_rules_client.list(request=global_request):
                load_balancers.append(parse_rule(rule, "global"))

        return load_balancers

    except ValueError as e:
        logging.error(f"Validation error listing load balancers: {e}")
        return ErrorResponse(error=f"Invalid input: {str(e)}")
    except GCPAuthError as e:
        logging.error(f"Authentication error listing load balancers: {e}")
        return ErrorResponse(error=f"Authentication failed: {str(e)}")
    except Exception as e:
        logging.error(f"Error listing load balancers: {e}")
        return ErrorResponse(error=f"Failed to list load balancers: {str(e)}")
