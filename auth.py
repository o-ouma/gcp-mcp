from google.oauth2 import service_account
from google.cloud import storage, bigquery, pubsub, secretmanager, monitoring, billing
from google.cloud.compute_v1 import InstancesClient, ForwardingRulesClient
import os
from dotenv import load_dotenv
import logging
from typing import Optional
from google.auth.credentials import Credentials


class GCPAuthError(Exception):
    """Custom exception for GCP authentication errors"""
    pass


class GCPAuth:
    """
    GCP Authentication manager with improved type safety and error handling.

    This class handles authentication to Google Cloud Platform services using
    service account credentials and provides typed client instances.
    """

    def __init__(self, credentials_path: Optional[str] = None) -> None:
        """
        Initialize GCP authentication.

        Args:
            credentials_path: Path to the service account credentials JSON file.
                            If None, will look for GOOGLE_APPLICATION_CREDENTIALS env var.

        Raises:
            GCPAuthError: If credentials cannot be loaded or file not found.
        """
        load_dotenv()
        self.credentials_path = credentials_path or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

        if not self.credentials_path:
            raise GCPAuthError(
                "No credentials path provided and GOOGLE_APPLICATION_CREDENTIALS not set"
            )

        # Convert to absolute path if relative
        if not os.path.isabs(self.credentials_path):
            self.credentials_path = os.path.abspath(self.credentials_path)
            
        logging.info(f"Using credentials file at: {self.credentials_path}")

        if not os.path.exists(self.credentials_path):
            raise GCPAuthError(f"Credentials file not found at: {self.credentials_path}")

        try:
            self.credentials: Credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path
            )
        except Exception as e:
            raise GCPAuthError(f"Failed to load credentials: {str(e)}")

    def get_storage_client(self) -> storage.Client:
        """Get authenticated Google Cloud Storage client."""
        try:
            return storage.Client(credentials=self.credentials)
        except Exception as e:
            raise GCPAuthError(f"Failed to create Storage client: {str(e)}")

    def get_compute_client(self) -> InstancesClient:
        """Get authenticated Google Cloud Compute client."""
        try:
            return InstancesClient(credentials=self.credentials)
        except Exception as e:
            raise GCPAuthError(f"Failed to create Compute client: {str(e)}")

    def get_bigquery_client(self) -> bigquery.Client:
        """Get authenticated Google Cloud BigQuery client."""
        try:
            return bigquery.Client(credentials=self.credentials)
        except Exception as e:
            raise GCPAuthError(f"Failed to create BigQuery client: {str(e)}")

    def get_pubsub_client(self) -> pubsub.PublisherClient:
        """Get authenticated Google Cloud Pub/Sub client."""
        try:
            return pubsub.PublisherClient(credentials=self.credentials)
        except Exception as e:
            raise GCPAuthError(f"Failed to create Pub/Sub client: {str(e)}")

    def get_secret_manager_client(self) -> secretmanager.SecretManagerServiceClient:
        """Get authenticated Google Cloud Secret Manager client."""
        try:
            return secretmanager.SecretManagerServiceClient(credentials=self.credentials)
        except Exception as e:
            raise GCPAuthError(f"Failed to create Secret Manager client: {str(e)}")

    def get_monitoring_client(self) -> monitoring.MetricServiceClient:
        """Get authenticated Google Cloud Monitoring client."""
        try:
            return monitoring.MetricServiceClient(credentials=self.credentials)
        except Exception as e:
            raise GCPAuthError(f"Failed to create Monitoring client: {str(e)}")

    def get_billing_client(self) -> billing.CloudBillingClient:
        """Get authenticated Google Cloud Billing client."""
        try:
            return billing.CloudBillingClient(credentials=self.credentials)
        except Exception as e:
            raise GCPAuthError(f"Failed to create Billing client: {str(e)}")

    def get_forwarding_rules_client(self) -> ForwardingRulesClient:
        """Get authenticated Google Cloud Forwarding Rules client."""
        try:
            return ForwardingRulesClient(credentials=self.credentials)
        except Exception as e:
            raise GCPAuthError(f"Failed to create Forwarding Rules client: {str(e)}")
