import boto3
import os
from botocore.exceptions import NoCredentialsError, ClientError
from fastapi import UploadFile
import uuid
from datetime import datetime
import logging
import tempfile
from .raw_processor import RawImageProcessor
import rawpy

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
        self.raw_processor = RawImageProcessor()
        
        if not self.bucket_name:
            raise ValueError("S3_BUCKET_NAME environment variable is required")
    
    async def upload_file(self, file: UploadFile) -> dict:
        """
        Upload file to S3 bucket with RAW processing support
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            dict: Upload result with URLs and metadata
        """
        try:
            # Generate unique filename
            file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            
            # Check if it's a RAW file
            is_raw = self.raw_processor.is_raw_format(file.filename)
            
            if is_raw:
                logger.info(f"Processing RAW file: {file.filename}")
                return await self._process_raw_file(file, timestamp, unique_id)
            else:
                logger.info(f"Processing regular image: {file.filename}")
                return await self._process_regular_file(file, timestamp, unique_id, file_extension)
                
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise Exception(f"Upload failed: {str(e)}")
    
    async def _process_raw_file(self, file: UploadFile, timestamp: str, unique_id: str) -> dict:
        """Process and upload RAW file"""
        try:
            # Save RAW file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                # Validate RAW file
                if not self.raw_processor.validate_raw_file(temp_file_path):
                    raise Exception("RAW file validation failed")
                
                # Open RAW file and get metadata
                with rawpy.imread(temp_file_path) as raw:
                    # Get RAW file metadata
                    raw_info = self.raw_processor.get_file_info(raw)
                    
                    # Convert to JPEG for web viewing
                    jpeg_bytes, content_type = self.raw_processor.process_raw_to_jpeg(temp_file_path)
                    
                    # Create thumbnail
                    thumbnail_bytes = self.raw_processor.create_thumbnail(temp_file_path)
                
                # Upload original RAW file
                raw_key = f"raw/{timestamp}_{unique_id}.{file.filename.split('.')[-1]}"
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=raw_key,
                    Body=content,
                    ContentType=file.content_type
                )
                
                # Upload converted JPEG
                jpeg_key = f"processed/{timestamp}_{unique_id}.jpg"
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=jpeg_key,
                    Body=jpeg_bytes,
                    ContentType='image/jpeg'
                )
                
                # Upload thumbnail
                thumb_key = f"thumbnails/{timestamp}_{unique_id}.jpg"
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=thumb_key,
                    Body=thumbnail_bytes,
                    ContentType='image/jpeg'
                )
                
                # Generate URLs
                region = os.getenv('AWS_REGION', 'us-east-1')
                if region == 'us-east-1':
                    base_url = f"https://{self.bucket_name}.s3.amazonaws.com"
                else:
                    base_url = f"https://{self.bucket_name}.s3.{region}.amazonaws.com"
                
                result = {
                    "message": "RAW file processed and uploaded successfully",
                    "filename": file.filename,
                    "file_size": len(content),
                    "is_raw": True,
                    "urls": {
                        "raw": f"{base_url}/{raw_key}",
                        "processed": f"{base_url}/{jpeg_key}",
                        "thumbnail": f"{base_url}/{thumb_key}"
                    },
                    "metadata": raw_info,
                    "processing_info": {
                        "original_format": file.filename.split('.')[-1],
                        "converted_to": "JPEG",
                        "thumbnail_created": True
                    }
                }
                
                logger.info(f"RAW file processed successfully: {result['urls']['raw']}")
                return result
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"RAW file processing failed: {e}")
            raise Exception(f"RAW file processing failed: {str(e)}")
    
    async def _process_regular_file(self, file: UploadFile, timestamp: str, unique_id: str, extension: str) -> dict:
        """Process and upload regular image file"""
        try:
            # Read file content
            file_content = await file.read()
            
            # Upload to S3
            s3_key = f"uploads/{timestamp}_{unique_id}.{extension}"
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=file.content_type
            )
            
            # Generate public URL with region
            region = os.getenv('AWS_REGION', 'us-east-1')
            if region == 'us-east-1':
                s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
            else:
                s3_url = f"https://{self.bucket_name}.s3.{region}.amazonaws.com/{s3_key}"
            
            result = {
                "message": "Image uploaded successfully",
                "filename": file.filename,
                "file_size": len(file_content),
                "is_raw": False,
                "urls": {
                    "image": s3_url
                },
                "processing_info": {
                    "format": extension,
                    "no_processing_needed": True
                }
            }
            
            logger.info(f"Regular file uploaded successfully: {s3_url}")
            return result
            
        except Exception as e:
            logger.error(f"Regular file upload failed: {e}")
            raise Exception(f"Regular file upload failed: {str(e)}")
    
    def test_connection(self) -> bool:
        """Test S3 connection and bucket access"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info("S3 connection successful")
            return True
        except Exception as e:
            logger.error(f"S3 connection failed: {e}")
            return False
