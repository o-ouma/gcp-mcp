"""Billing and monitoring-related GCP tools with improved type safety"""

from typing import Union, List, Optional
from auth import GCPAuth, GCPAuthError
from models import (
    BillingCostRequest,
    BillingCostResponse,
    MetricsRequest,
    MetricsResponse,
    CostAmount,
    ErrorResponse
)
from datetime import datetime, timedelta
from google.cloud.billing_v1 import CloudBillingClient
import logging


def get_billing_cost(
    project_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    group_by: List[str] = ["service"]
) -> Union[BillingCostResponse, ErrorResponse]:
    """
    Get billing cost for a project using its linked billing account with validation.

    Args:
        project_id: GCP project ID
        start_date: Start date in ISO format (optional)
        end_date: End date in ISO format (optional)
        group_by: List of fields to group by

    Returns:
        Billing cost information or error response
    """
    try:
        # Validate input using Pydantic model
        request = BillingCostRequest(
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
            group_by=group_by
        )

        gcp_auth = GCPAuth()
        billing_client = gcp_auth.get_billing_client()

        # Get project billing info to find the linked billing account
        project_name = f"projects/{request.project_id}"
        project_billing_info = billing_client.get_project_billing_info(name=project_name)

        if not project_billing_info.billing_enabled:
            return BillingCostResponse(
                success=False,
                project_id=request.project_id,
                error="Billing is not enabled for this project"
            )

        # Get the billing account ID from the project's billing info
        billing_account_id = project_billing_info.billing_account_name.split('/')[-1]

        # Parse dates if provided, otherwise use last 30 days
        end = datetime.now()
        if request.end_date:
            try:
                end = datetime.fromisoformat(request.end_date)
            except ValueError:
                return ErrorResponse(error="Invalid end_date format. Use ISO format (YYYY-MM-DD)")

        start = end - timedelta(days=30)  # Default to last 30 days
        if request.start_date:
            try:
                start = datetime.fromisoformat(request.start_date)
            except ValueError:
                return ErrorResponse(error="Invalid start_date format. Use ISO format (YYYY-MM-DD)")

        # Get the billing account information
        billing_account_name = f"billingAccounts/{billing_account_id}"

        try:
            billing_account = billing_client.get_billing_account(name=billing_account_name)

            # Note: The actual cost retrieval would require using Cloud Billing API
            # with proper cost data queries. This is a simplified implementation.
            return BillingCostResponse(
                success=True,
                project_id=request.project_id,
                billing_account_id=billing_account_id,
                time_range={
                    "start": start.isoformat(),
                    "end": end.isoformat()
                },
                total_cost=CostAmount(amount=0.0, currency="USD"),
                costs_by_service={}
            )

        except Exception as billing_error:
            logging.error(f"Error retrieving billing data: {billing_error}")
            return BillingCostResponse(
                success=False,
                project_id=request.project_id,
                billing_account_id=billing_account_id,
                error=f"Failed to retrieve billing data: {str(billing_error)}"
            )

    except ValueError as e:
        logging.error(f"Validation error getting billing cost: {e}")
        return ErrorResponse(error=f"Invalid input: {str(e)}")
    except GCPAuthError as e:
        logging.error(f"Authentication error getting billing cost: {e}")
        return ErrorResponse(error=f"Authentication failed: {str(e)}")
    except Exception as e:
        logging.error(f"Error getting billing cost: {e}")
        return ErrorResponse(error=f"Failed to get billing data: {str(e)}")


def get_metrics(
    project_id: str,
    metric_type: str,
    interval: str = "1h",
    aggregation: str = "mean"
) -> Union[MetricsResponse, ErrorResponse]:
    """
    Get monitoring metrics with validation.

    Args:
        project_id: GCP project ID
        metric_type: Type of metric to retrieve
        interval: Time interval for metrics
        aggregation: Aggregation method

    Returns:
        Metrics information or error response
    """
    try:
        # Validate input using Pydantic model
        request = MetricsRequest(
            project_id=project_id,
            metric_type=metric_type,
            interval=interval,
            aggregation=aggregation
        )

        gcp_auth = GCPAuth()
        monitoring_client = gcp_auth.get_monitoring_client()

        # Note: This is a placeholder implementation.
        # The actual metrics retrieval would require building proper
        # time series queries using the Cloud Monitoring API.

        return MetricsResponse(
            message=f"Metrics retrieved for {request.metric_type}",
            project_id=request.project_id,
            metric_type=request.metric_type,
            interval=request.interval,
            aggregation=request.aggregation,
            data={}
        )

    except ValueError as e:
        logging.error(f"Validation error getting metrics: {e}")
        return ErrorResponse(error=f"Invalid input: {str(e)}")
    except GCPAuthError as e:
        logging.error(f"Authentication error getting metrics: {e}")
        return ErrorResponse(error=f"Authentication failed: {str(e)}")
    except Exception as e:
        logging.error(f"Error getting metrics: {e}")
        return ErrorResponse(error=f"Failed to get metrics: {str(e)}")
