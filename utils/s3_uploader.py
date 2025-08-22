import boto3
import os
from botocore.exceptions import NoCredentialsError, ClientError
from fastapi import UploadFile
import uuid
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class S3Uploader:
    def __init__(self):
        """Initialize S3 client with credentials from environment variables"""
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        
        if not self.bucket_name:
            raise ValueError("S3_BUCKET_NAME environment variable is required")
    
    async def upload_file(self, file: UploadFile) -> str:
        """
        Upload file to S3 bucket
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            str: Public URL of the uploaded file
        """
        try:
            # Generate unique filename
            file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            s3_key = f"uploads/{timestamp}_{unique_id}.{file_extension}"
            
            # Read file content
            file_content = await file.read()
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=file.content_type
                # ACL removed - bucket has ACLs disabled, using bucket policy instead
            )
            
            # Generate public URL with region
            region = os.getenv('AWS_REGION', 'us-east-1')
            if region == 'us-east-1':
                # Standard region doesn't need region in URL
                s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
            else:
                # Non-standard regions need region in URL
                s3_url = f"https://{self.bucket_name}.s3.{region}.amazonaws.com/{s3_key}"
            
            logger.info(f"File uploaded successfully: {s3_url}")
            return s3_url
            
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise Exception("AWS credentials not configured")
        except ClientError as e:
            logger.error(f"AWS S3 error: {e}")
            raise Exception(f"S3 upload failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise Exception(f"Upload failed: {e}")
    
    def test_connection(self) -> bool:
        """Test S3 connection and bucket access"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info("S3 connection successful")
            return True
        except Exception as e:
            logger.error(f"S3 connection failed: {e}")
            return False
