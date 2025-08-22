from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
from utils.s3_uploader import S3Uploader
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="FastAPI S3 Image Uploader", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize S3 uploader
s3_uploader = S3Uploader()

@app.get("/")
async def read_root():
    """Serve the main HTML page"""
    return FileResponse("static/index.html")

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
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

@app.get("/images")
async def list_images(limit: int = 50):
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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
