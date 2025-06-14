from google.oauth2 import service_account
from google.cloud import storage, bigquery, pubsub, secretmanager, monitoring, billing
from google.cloud.compute_v1 import InstancesClient
import os
from dotenv import load_dotenv
import logging

class GCPAuth:
    def __init__(self, credentials_path=None):
        """
        Initialize GCP authentication.
        Args:
            credentials_path (str): Path to the service account credentials JSON file.
                                   If None, will look for GOOGLE_APPLICATION_CREDENTIALS env var.
        """
        load_dotenv()
        self.credentials_path = credentials_path or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not self.credentials_path:
            raise ValueError("No credentials path provided and GOOGLE_APPLICATION_CREDENTIALS not set")
        
        # Convert to absolute path if relative
        if not os.path.isabs(self.credentials_path):
            self.credentials_path = os.path.abspath(self.credentials_path)
            
        logging.info(f"Using credentials file at: {self.credentials_path}")
        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(f"Credentials file not found at: {self.credentials_path}")
        
        self.credentials = service_account.Credentials.from_service_account_file(
            self.credentials_path
        )
        
    def get_storage_client(self):
        """Get authenticated Google Cloud Storage client."""
        return storage.Client(credentials=self.credentials)
    
    def get_compute_client(self):
        """Get authenticated Google Cloud Compute client."""
        return InstancesClient(credentials=self.credentials)
    
    def get_bigquery_client(self):
        """Get authenticated Google Cloud BigQuery client."""
        return bigquery.Client(credentials=self.credentials)
    
    def get_pubsub_client(self):
        """Get authenticated Google Cloud Pub/Sub client."""
        return pubsub.PublisherClient(credentials=self.credentials)
    
    def get_secret_manager_client(self):
        """Get authenticated Google Cloud Secret Manager client."""
        return secretmanager.SecretManagerServiceClient(credentials=self.credentials)
    
    def get_monitoring_client(self):
        """Get authenticated Google Cloud Monitoring client."""
        return monitoring.MetricServiceClient(credentials=self.credentials)
    
    def get_billing_client(self):
        """Get authenticated Google Cloud Billing client."""
        return billing.CloudBillingClient(credentials=self.credentials) 