from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
from utils.s3_uploader import S3Uploader
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="AWS S3 Image Upload", version="1.0.0")

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
    """Upload image to S3 bucket"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Validate file size (max 10MB)
        if file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size must be less than 10MB")
        
        # Upload to S3
        s3_url = await s3_uploader.upload_file(file)
        
        return {
            "message": "Image uploaded successfully",
            "s3_url": s3_url,
            "filename": file.filename
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
