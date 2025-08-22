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
from PIL import Image
import io
import json

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
        
        # Initialize file mapping
        self.mapping_file = "file_mapping.json"
        self._ensure_mapping_file()
    
    def _ensure_mapping_file(self):
        """Ensure the mapping file exists and is valid"""
        try:
            if not os.path.exists(self.mapping_file):
                with open(self.mapping_file, 'w') as f:
                    json.dump({"file_mappings": {}, "last_updated": None}, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not create mapping file: {e}")
    
    def _save_file_mapping(self, uploaded_filename: str, original_filename: str, file_url: str, file_type: str = "regular"):
        """Save file mapping to JSON"""
        try:
            # Load existing mapping
            if os.path.exists(self.mapping_file):
                with open(self.mapping_file, 'r') as f:
                    mapping_data = json.load(f)
            else:
                mapping_data = {"file_mappings": {}, "last_updated": None}
            
            # Add new mapping
            mapping_data["file_mappings"][uploaded_filename] = {
                "original_filename": original_filename,
                "file_url": file_url,
                "file_type": file_type,
                "mapped_at": datetime.now().isoformat()
            }
            mapping_data["last_updated"] = datetime.now().isoformat()
            
            # Save back to file
            with open(self.mapping_file, 'w') as f:
                json.dump(mapping_data, f, indent=2)
                
            logger.info(f"Saved file mapping: {uploaded_filename} -> {original_filename} ({file_type})")
            
        except Exception as e:
            logger.warning(f"Could not save file mapping: {e}")
    
    def _get_raw_url_from_mapping(self, processed_filename: str) -> str:
        """Get RAW URL from mapping file"""
        try:
            if os.path.exists(self.mapping_file):
                with open(self.mapping_file, 'r') as f:
                    mapping_data = json.load(f)
                
                if processed_filename in mapping_data["file_mappings"]:
                    mapping = mapping_data["file_mappings"][processed_filename]
                    if mapping.get("file_type") == "raw":
                        return mapping.get("file_url")
                    else:
                        # For regular files, return the main file URL
                        return mapping.get("file_url")
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not read file mapping: {e}")
            return None
    
    def create_thumbnail_from_bytes(self, image_bytes: bytes, content_type: str, size: tuple = (300, 300)) -> bytes:
        """Create thumbnail from image bytes"""
        try:
            # Open image from bytes
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            # Create thumbnail
            image.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Convert to JPEG bytes
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
            raise Exception(f"Failed to create thumbnail: {str(e)}")
    
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
                
                # Save file mapping for RAW files
                processed_filename = f"{timestamp}_{unique_id}.jpg"
                raw_filename = f"{timestamp}_{unique_id}.{file.filename.split('.')[-1]}"
                raw_url = f"{base_url}/{raw_key}"
                
                self._save_file_mapping(processed_filename, raw_filename, raw_url, "raw")
                
                result = {
                    "message": "RAW file processed and uploaded successfully",
                    "filename": file.filename,
                    "file_size": len(content),
                    "is_raw": True,
                    "upload_time": timestamp,
                    "unique_id": unique_id,
                    "urls": {
                        "raw": raw_url,
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
            
            # Create thumbnail
            thumbnail_bytes = self.create_thumbnail_from_bytes(file_content, file.content_type)
            
            # Upload original file
            s3_key = f"uploads/{timestamp}_{unique_id}.{extension}"
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=file.content_type
            )
            
            # Upload thumbnail
            thumb_key = f"thumbnails/{timestamp}_{unique_id}.jpg"
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=thumb_key,
                Body=thumbnail_bytes,
                ContentType='image/jpeg'
            )
            
            # Generate public URL with region
            region = os.getenv('AWS_REGION', 'us-east-1')
            if region == 'us-east-1':
                base_url = f"https://{self.bucket_name}.s3.amazonaws.com"
            else:
                base_url = f"https://{self.bucket_name}.s3.{region}.amazonaws.com"
            
            # Save file mapping for regular files too
            uploaded_filename = f"{timestamp}_{unique_id}.{extension}"
            original_filename = file.filename
            image_url = f"{base_url}/{s3_key}"
            
            self._save_file_mapping(uploaded_filename, original_filename, image_url)
            
            result = {
                "message": "Image uploaded successfully",
                "filename": file.filename,
                "file_size": len(file_content),
                "is_raw": False,
                "upload_time": timestamp,
                "unique_id": unique_id,
                "urls": {
                    "image": image_url,
                    "thumbnail": f"{base_url}/{thumb_key}"
                },
                "processing_info": {
                    "format": extension,
                    "thumbnail_created": True
                }
            }
            
            logger.info(f"Regular file uploaded successfully: {result['urls']['image']}")
            return result
            
        except Exception as e:
            logger.error(f"Regular file upload failed: {e}")
            raise Exception(f"Regular file upload failed: {str(e)}")
    
    async def list_images(self, limit: int = 50) -> list:
        """List all images in the bucket with their metadata"""
        try:
            images = []
            
            # List files from different folders
            folders = ['uploads', 'processed', 'raw']
            
            for folder in folders:
                try:
                    response = self.s3_client.list_objects_v2(
                        Bucket=self.bucket_name,
                        Prefix=folder + '/',
                        MaxKeys=limit
                    )
                    
                    if 'Contents' in response:
                        for obj in response['Contents']:
                            key = obj['Key']
                            if key.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.cr2', '.nef', '.arw', '.raf', '.dng')):
                                # Extract metadata from key
                                parts = key.split('/')
                                if len(parts) >= 2:
                                    filename = parts[1]
                                    if '_' in filename:
                                        timestamp_part = filename.split('_')[0:2]
                                        timestamp = '_'.join(timestamp_part)
                                        
                                        # Determine image type based on folder and extension
                                        # A file is RAW if it's in the raw folder OR processed folder OR has a RAW extension
                                        is_raw = (folder == 'raw' or 
                                                 folder == 'processed' or
                                                 any(key.lower().endswith(ext) for ext in ['.cr2', '.nef', '.arw', '.raf', '.dng', '.cr3', '.nrw', '.sr2', '.rw2', '.orf', '.pef', '.raw', '.rwz', '.3fr', '.fff', '.hdr', '.srw', '.mrw', '.mef', '.mos', '.bay', '.dcr', '.kdc', '.erf', '.mdc', '.x3f', '.r3d', '.cine', '.dpx', '.exr', '.tga', '.tif', '.tiff']))
                                        
                                        # Debug logging
                                        logger.info(f"File: {filename}, Folder: {folder}, Extension: {key.split('.')[-1]}, Is RAW: {is_raw}")
                                        
                                        # Generate base URL
                                        region = os.getenv('AWS_REGION', 'us-east-1')
                                        if region == 'us-east-1':
                                            base_url = f"https://{self.bucket_name}.s3.amazonaws.com"
                                        else:
                                            base_url = f"https://{self.bucket_name}.s3.{region}.amazonaws.com"
                                        
                                        # Generate URLs - Use original images for better quality, thumbnails only for very small previews
                                        if folder == 'uploads':
                                            # Regular image - use original for display
                                            thumbnail_url = f"{base_url}/thumbnails/{filename.split('.')[0]}.jpg"
                                            display_url = f"{base_url}/{key}"  # Original image for display
                                        elif folder == 'raw':
                                            # RAW file - use processed JPEG for display
                                            thumbnail_url = f"{base_url}/thumbnails/{filename.split('.')[0]}.jpg"
                                            display_url = f"{base_url}/processed/{filename.split('.')[0]}.jpg"  # Processed JPEG
                                        elif folder == 'processed':
                                            # Processed RAW file - use it directly for display
                                            thumbnail_url = f"{base_url}/thumbnails/{filename.split('.')[0]}.jpg"
                                            display_url = f"{base_url}/{key}"
                                        else:
                                            # Other folders - use thumbnail
                                            thumbnail_url = f"{base_url}/thumbnails/{filename.split('.')[0]}.jpg"
                                            display_url = f"{base_url}/{key}"
                                        
                                        # For RAW files, provide access to both processed and original versions
                                        if is_raw:
                                            if folder == 'raw':
                                                # This is the original RAW file, skip it in gallery (we'll show processed version)
                                                continue
                                            elif folder == 'processed':
                                                # This is the processed JPEG, get RAW URL from mapping
                                                raw_original_url = self._get_raw_url_from_mapping(filename)
                                                if raw_original_url:
                                                    logger.info(f"Found RAW URL from mapping: {raw_original_url}")
                                                else:
                                                    # Fallback: try to reconstruct (for backward compatibility)
                                                    filename_parts = filename.split('_')
                                                    if len(filename_parts) >= 3:
                                                        base_name = '_'.join(filename_parts[:3])
                                                        raw_original_url = f"{base_url}/raw/{base_name}"
                                                        logger.warning(f"Using fallback RAW URL: {raw_original_url}")
                                                    else:
                                                        raw_original_url = None
                                                        logger.warning(f"Could not reconstruct RAW filename from: {filename}")
                                            else:
                                                raw_original_url = None
                                        else:
                                            raw_original_url = None
                                        
                                        # Only add to gallery if it's not a RAW file in the raw folder
                                        # (we want to show processed JPEGs instead)
                                        if not (folder == 'raw' and is_raw):
                                            image_info = {
                                                'key': key,
                                                'filename': filename,
                                                'folder': folder,
                                                'is_raw': is_raw,
                                                'timestamp': timestamp,
                                                'size': obj['Size'],
                                                'last_modified': obj['LastModified'].isoformat(),
                                                'url': display_url,
                                                'thumbnail_url': thumbnail_url,
                                                'original_url': f"{base_url}/{key}" if folder == 'uploads' else None,
                                                'raw_original_url': raw_original_url
                                            }
                                            
                                            images.append(image_info)
                except Exception as e:
                    logger.warning(f"Error listing folder {folder}: {e}")
                    continue
            
            # Sort by timestamp (newest first)
            images.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return images[:limit]
            
        except Exception as e:
            logger.error(f"Error listing images: {e}")
            return []
    
    def test_connection(self) -> bool:
        """Test S3 connection and bucket access"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info("S3 connection successful")
            return True
        except Exception as e:
            logger.error(f"S3 connection failed: {e}")
            return False
