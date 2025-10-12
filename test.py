import os
from azure.storage.blob import BlobServiceClient
from azure.identity import AzureDeveloperCliCredential
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Get Azure Storage configuration from environment variables
azure_storage_endpoint = os.getenv('AZURE_STORAGE_ENDPOINT')
azure_storage_container = os.getenv('AZURE_STORAGE_CONTAINER')
azure_credential = AzureDeveloperCliCredential(tenant_id=os.environ["AZURE_TENANT_ID"], process_timeout=60)


print(f"Azure Storage Endpoint: {azure_storage_endpoint}")
print(f"Azure Storage Container: {azure_storage_container}")
print(f"Using Tenant ID: {os.environ['AZURE_TENANT_ID']}")

blob_client = BlobServiceClient(
    account_url=azure_storage_endpoint,
      credential=azure_credential,
    max_single_put_size=4 * 1024 * 1024
)

# insert code to verify blob client
# List all containers to verify connection
container_client = blob_client.get_container_client(azure_storage_container)
if not container_client.exists():
    container_client.create_container()
existing_blobs = [blob.name for blob in container_client.list_blobs()]
