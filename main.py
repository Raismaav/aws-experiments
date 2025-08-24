from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn
from utils.s3_uploader import S3Uploader
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Response models
class ImageInfo(BaseModel):
    key: str = Field(..., description="S3 object key")
    filename: str = Field(..., description="File name")
    folder: str = Field(..., description="S3 folder location")
    is_raw: bool = Field(..., description="Whether the file is a RAW format")
    timestamp: str = Field(..., description="Upload timestamp")
    size: int = Field(..., description="File size in bytes")
    last_modified: str = Field(..., description="Last modification date")
    url: str = Field(..., description="Display URL for the image")
    thumbnail_url: str = Field(..., description="Thumbnail URL")
    original_url: Optional[str] = Field(None, description="Original file URL")
    raw_original_url: Optional[str] = Field(None, description="Original RAW file URL if applicable")

class UploadResponse(BaseModel):
    message: str = Field(..., description="Success message")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    is_raw: bool = Field(..., description="Whether the file is RAW format")
    upload_time: str = Field(..., description="Upload timestamp")
    unique_id: str = Field(..., description="Unique identifier")
    urls: dict = Field(..., description="Dictionary containing file URLs")
    metadata: Optional[dict] = Field(None, description="RAW file metadata if applicable")
    processing_info: dict = Field(..., description="Processing information")

class ImagesListResponse(BaseModel):
    images: List[ImageInfo] = Field(..., description="List of image information")
    total: int = Field(..., description="Total number of images")
    limit: int = Field(..., description="Requested limit")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Health status")

class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error description")

app = FastAPI(
    title="AWS S3 Image Uploader API",
    description="""
    A comprehensive API for uploading, processing, and managing images with AWS S3.
    
    ## Features
    
    * **Image Upload**: Support for regular images (JPG, PNG, GIF, WebP) and RAW formats
    * **RAW Processing**: Automatic conversion of RAW files to web-friendly JPEG format
    * **Thumbnail Generation**: Automatic creation of thumbnails for all uploaded images
    * **S3 Integration**: Direct upload to AWS S3 with proper file organization
    * **Metadata Extraction**: Rich metadata extraction from RAW files
    
    ## Supported RAW Formats
    
    * Canon: CR2, CR3
    * Nikon: NEF, NRW
    * Sony: ARW, SR2
    * Fujifilm: RAF
    * Panasonic: RW2
    * Olympus: ORF
    * Pentax: PEF
    * Adobe: DNG
    * And many more...
    
    ## File Size Limits
    
    * Regular images: Standard FastAPI limits
    * RAW files: Up to 500MB
    
    ## Authentication
    
    Requires AWS credentials configured via environment variables:
    * AWS_ACCESS_KEY_ID
    * AWS_SECRET_ACCESS_KEY
    * AWS_REGION
    * S3_BUCKET_NAME
    """,
    version="1.0.0",
    contact={
        "name": "API Support",
        "email": "support@example.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize S3 uploader
s3_uploader = S3Uploader()

@app.get("/", response_class=FileResponse)
async def read_root():
    """
    Serve the main HTML page
    
    Returns the main application interface for image upload and management.
    """
    return FileResponse("static/index.html")

@app.post("/upload", 
          response_model=UploadResponse,
          responses={
              200: {"description": "File uploaded successfully", "model": UploadResponse},
              400: {"description": "Invalid file or file too large", "model": ErrorResponse},
              500: {"description": "Upload failed", "model": ErrorResponse}
          },
          summary="Upload Image to S3",
          description="""
          Upload an image file to AWS S3 with automatic processing.
          
          **Features:**
          * Supports both regular images and RAW formats
          * Automatic RAW to JPEG conversion
          * Thumbnail generation
          * Metadata extraction for RAW files
          * File validation and size checking
          
          **File Requirements:**
          * Must be a valid image format
          * Regular images: Standard size limits
          * RAW files: Up to 500MB
          
          **Response includes:**
          * File URLs (original, processed, thumbnail)
          * Metadata for RAW files
          * Processing information
          * Unique identifiers
          """)
async def upload_image(file: UploadFile = File(..., description="Image file to upload")):
    """Upload image to S3 bucket with RAW processing support"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Check file size (increased limit for RAW files)
        max_size = 500 * 1024 * 1024  # 500MB for RAW files
        if file.size > max_size:
            raise HTTPException(status_code=400, detail=f"File size must be less than {max_size / (1024*1024):.0f}MB")
        
        # Upload to S3 (now returns dict instead of string)
        result = await s3_uploader.upload_file(file)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/images", 
         response_model=ImagesListResponse,
         responses={
             200: {"description": "Images retrieved successfully", "model": ImagesListResponse},
             500: {"description": "Failed to list images", "model": ErrorResponse}
         },
         summary="List Images",
         description="""
         Retrieve a list of all images stored in the S3 bucket.
         
         **Features:**
         * Pagination support with limit parameter
         * Comprehensive image metadata
         * Support for both regular and RAW images
         * Thumbnail and display URLs
         * File organization information
         
         **Response includes:**
         * Image list with metadata
         * Total count
         * Applied limit
         * URLs for display and thumbnails
         """)
async def list_images(limit: int = Query(50, ge=1, le=1000, description="Maximum number of images to return (1-1000)")):
    """List all images in the S3 bucket"""
    try:
        images = await s3_uploader.list_images(limit=limit)
        return {
            "images": images,
            "total": len(images),
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list images: {str(e)}")

@app.get("/health", 
         response_model=HealthResponse,
         responses={
             200: {"description": "Service is healthy", "model": HealthResponse}
         },
         summary="Health Check",
         description="""
         Check the health status of the service.
         
         **Use cases:**
         * Load balancer health checks
         * Monitoring and alerting
         * Service availability verification
         
         **Response:**
         * Simple status indicator
         """)
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add custom examples
    openapi_schema["paths"]["/upload"]["post"]["requestBody"]["content"]["multipart/form-data"]["schema"]["example"] = {
        "file": "(binary)"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
