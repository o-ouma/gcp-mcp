"""GCP Tools package for MCP server with improved type safety"""

from .storage_tools import list_buckets, create_bucket, delete_bucket
from .compute_tools import (
    list_instances,
    create_instance,
    delete_instance,
    list_ip_addresses,
    list_persistent_disks
)
from .network_tools import list_vpc_networks_and_subnets, list_load_balancers
from .billing_tools import get_billing_cost, get_metrics

# Import types for better IDE support and documentation
from typing import Union, List, Optional
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

__all__ = [
    # Storage tools
    "list_buckets",
    "create_bucket",
    "delete_bucket",
    # Compute tools
    "list_instances",
    "create_instance",
    "delete_instance",
    "list_ip_addresses",
    "list_persistent_disks",
    # Network tools
    "list_vpc_networks_and_subnets",
    "list_load_balancers",
    # Billing/monitoring tools
    "get_billing_cost",
    "get_metrics"
]

# Type aliases for better documentation
ListBucketsReturn = Union[List[str], ErrorResponse]
CreateBucketReturn = Union[SuccessResponse, ErrorResponse]
DeleteBucketReturn = Union[SuccessResponse, ErrorResponse]
ListInstancesReturn = Union[List[str], ErrorResponse]
CreateInstanceReturn = Union[SuccessResponse, ErrorResponse]
DeleteInstanceReturn = Union[SuccessResponse, ErrorResponse]
ListIPAddressesReturn = Union[List[IPAddressResponse], ErrorResponse]
ListPersistentDisksReturn = Union[List[PersistentDiskResponse], ErrorResponse]
ListVPCNetworksReturn = Union[List[VPCNetworkResponse], ErrorResponse]
ListLoadBalancersReturn = Union[List[LoadBalancerResponse], ErrorResponse]
GetBillingCostReturn = Union[BillingCostResponse, ErrorResponse]
GetMetricsReturn = Union[MetricsResponse, ErrorResponse]
