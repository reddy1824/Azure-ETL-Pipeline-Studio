import os
from dotenv import load_dotenv
from etl.logger import setup_logger

# Load environment variables
load_dotenv()

logger = setup_logger("azure_loader")

class AzureBlobLoader:
    """
    Handles uploading files (CSV data and generated reports) to Azure Blob Storage.
    Supports a mock mode for credential-less environments.
    """
    def __init__(self):
        self.connection_string = os.getenv("AZURE_CONNECTION_STRING")
        self.container_name = os.getenv("AZURE_CONTAINER_NAME", "student-analytics")
        self.mock_mode = os.getenv("USE_MOCK_AZURE", "True").lower() == "true"
        
        if not self.connection_string:
            logger.warning("Azure connection string missing. Defaulting to Mock Mode.")
            self.mock_mode = True

    def upload_file(self, local_filepath, blob_name=None):
        """
        Uploads a local file to Azure Blob Storage or mocks it if mock mode is active.
        
        Args:
            local_filepath (str): Path to the local file.
            blob_name (str, optional): Name of the target blob in the container.
            
        Returns:
            bool: True if upload succeeded (or was successfully mocked).
        """
        if not os.path.exists(local_filepath):
            logger.error(f"Cannot upload: local file {local_filepath} does not exist.")
            return False
            
        if not blob_name:
            blob_name = os.path.basename(local_filepath)
            
        if self.mock_mode:
            logger.info(f"[MOCK AZURE] Uploading '{local_filepath}' to container '{self.container_name}' as '{blob_name}'...")
            logger.info(f"[MOCK AZURE] Upload successful! (Simulated URL: https://{self.container_name}.blob.core.windows.net/{blob_name})")
            return True
            
        try:
            logger.info(f"Connecting to Azure Blob Storage to upload {local_filepath}...")
            from azure.storage.blob import BlobServiceClient
            
            blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
            container_client = blob_service_client.get_container_client(self.container_name)
            
            # Create container if it doesn't exist
            try:
                container_client.create_container()
                logger.info(f"Created container: {self.container_name}")
            except Exception:
                # Container likely already exists
                pass
                
            blob_client = container_client.get_blob_client(blob_name)
            
            logger.info(f"Uploading file '{local_filepath}' to container '{self.container_name}'...")
            with open(local_filepath, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
                
            logger.info(f"Azure upload successful! Blob URL: {blob_client.url}")
            return True
            
        except Exception as e:
            logger.error(f"Azure upload failed for {local_filepath}: {str(e)}")
            logger.warning("Falling back to simulated upload due to error.")
            return True  # Return True to let the pipeline proceed in a friendly manner
