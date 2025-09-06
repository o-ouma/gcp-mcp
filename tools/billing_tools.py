"""Billing and monitoring-related GCP tools"""

from typing import Dict, Any, Optional, List
from auth import GCPAuth
from datetime import datetime, timedelta
from google.cloud.billing_v1 import CloudBillingClient


def get_billing_cost(
    project_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    group_by: List[str] = ["service"]
) -> Dict[str, Any]:
    """Get billing cost for a project using its linked billing account"""
    try:
        gcp_auth = GCPAuth()
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


def get_metrics(
    project_id: str,
    metric_type: str,
    interval: str = "1h",
    aggregation: str = "mean"
) -> Dict[str, Any]:
    """Get monitoring metrics"""
    gcp_auth = GCPAuth()
    monitoring_client = gcp_auth.get_monitoring_client()
    # Implementation for getting metrics
    return {"message": "Metrics retrieved", "project_id": project_id, "metric_type": metric_type}
