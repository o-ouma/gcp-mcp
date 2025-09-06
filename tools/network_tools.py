"""Network-related GCP tools (VPC networks, subnets, load balancers)"""

from typing import List, Dict, Any, Optional
from auth import GCPAuth
from google.cloud import compute_v1


def list_vpc_networks_and_subnets(project_id: str) -> List[Dict[str, Any]]:
    """List all VPC networks and their subnets in a project, including region and subnet info."""
    gcp_auth = GCPAuth()
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


def list_load_balancers(project_id: str, region: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all load balancers (forwarding rules) in a project, with type (external/internal) and associated IP addresses."""
    gcp_auth = GCPAuth()
    forwarding_rules_client = gcp_auth.get_forwarding_rules_client()
    load_balancers = []

    def parse_rule(rule, region_name=None):
        lb_type = "EXTERNAL" if rule.load_balancing_scheme == "EXTERNAL" else "INTERNAL"
        ip_address = getattr(rule, "IPAddress", None)
        ip_protocol = getattr(rule, "IPProtocol", None)
        return {
            "name": rule.name,
            "region": region_name or "global",
            "type": lb_type,
            "ip_address": ip_address,
            "ip_protocol": ip_protocol,
            "network_tier": getattr(rule, "network_tier", None),
            "load_balancing_scheme": rule.load_balancing_scheme,
            "target": rule.target,
            "description": rule.description,
        }

    if region:
        request = compute_v1.ListForwardingRulesRequest(project=project_id, region=region)
        for rule in forwarding_rules_client.list(request=request):
            load_balancers.append(parse_rule(rule, region))
    else:
        # List all regions
        regions_client = compute_v1.RegionsClient()
        regions_request = compute_v1.ListRegionsRequest(project=project_id)
        for region_obj in regions_client.list(request=regions_request):
            region_name = region_obj.name
            request = compute_v1.ListForwardingRulesRequest(project=project_id, region=region_name)
            for rule in forwarding_rules_client.list(request=request):
                load_balancers.append(parse_rule(rule, region_name))
        # List global forwarding rules (for global/external LBs)
        global_rules_client = compute_v1.GlobalForwardingRulesClient()
        for rule in global_rules_client.list(project=project_id):
            load_balancers.append(parse_rule(rule, "global"))
    return load_balancers
