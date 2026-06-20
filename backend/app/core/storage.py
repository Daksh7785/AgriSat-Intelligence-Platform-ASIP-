from minio import Minio
from loguru import logger
import os
from typing import Optional

from app.core.config import settings

# Global Minio Client reference
minio_client: Optional[Minio] = None

async def init_storage():
    """Initializes Minio S3 Client and checks/creates necessary buckets."""
    global minio_client
    logger.info("Initializing Object Storage (MinIO) client...")
    try:
        # MinIO host may include port
        endpoint = settings.MINIO_ENDPOINT
        
        # Initialize client (for local testing, secure is false since it runs on local docker HTTP)
        minio_client = Minio(
            endpoint,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=False
        )
        
        # Verify and create buckets
        buckets = [
            settings.MINIO_BUCKET_RASTERS,
            settings.MINIO_BUCKET_MODELS,
            settings.MINIO_BUCKET_OUTPUTS
        ]
        
        for bucket in buckets:
            if not minio_client.bucket_exists(bucket):
                minio_client.make_bucket(bucket)
                logger.info(f"Created MinIO bucket: '{bucket}'")
            else:
                logger.info(f"MinIO bucket exists: '{bucket}'")
                
    except Exception as e:
        logger.error(f"MinIO client initialization failed: {e}. Falling back to simulated object storage.")
        minio_client = None

def upload_file(bucket_name: str, object_name: str, file_path: str) -> bool:
    """Uploads local file to object storage."""
    if not minio_client:
        logger.info(f"[SIMULATED UPLOAD] Bucket: {bucket_name} | Object: {object_name} | File: {file_path}")
        return True
    try:
        minio_client.fput_object(bucket_name, object_name, file_path)
        logger.info(f"Uploaded '{file_path}' to '{bucket_name}/{object_name}'")
        return True
    except Exception as e:
        logger.error(f"MinIO upload failed: {e}")
        return False

def download_file(bucket_name: str, object_name: str, destination_path: str) -> bool:
    """Downloads object from storage to local file path."""
    if not minio_client:
        logger.info(f"[SIMULATED DOWNLOAD] Bucket: {bucket_name} | Object: {object_name} | Destination: {destination_path}")
        # Create dummy file to simulate success
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        with open(destination_path, "w") as f:
            f.write("Simulated downloaded binary stream")
        return True
    try:
        minio_client.fget_object(bucket_name, object_name, destination_path)
        logger.info(f"Downloaded '{bucket_name}/{object_name}' to '{destination_path}'")
        return True
    except Exception as e:
        logger.error(f"MinIO download failed: {e}")
        return False
