# 🚀 FastAPI S3 Image Uploader

A modern web application that allows users to upload images directly to an AWS S3 bucket using FastAPI backend and a beautiful drag & drop frontend.

## ✨ Features

- **🖼️ Image Upload**: Drag & drop or click to browse
- **☁️ Direct S3 Integration**: Images go straight to your S3 bucket
- **🎨 Modern UI**: Beautiful, responsive design with smooth animations
- **🔒 Secure**: File validation, size limits, and type checking
- **📱 Responsive**: Works perfectly on desktop and mobile
- **⚡ Fast**: Built with FastAPI for high performance
- **📸 RAW Image Support**: Automatic processing of RAW camera files (CR2, NEF, ARW, etc.)
- **🔗 Smart File Mapping**: Intelligent linking between processed JPEGs and original RAW files
- **📁 File Organization**: Automatic folder structure (uploads/, raw/, processed/, thumbnails/)
- **🔄 Auto-Processing**: RAW files automatically converted to web-friendly JPEGs

## 🏗️ Architecture

- **Backend**: FastAPI (Python)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Storage**: AWS S3
- **File Handling**: Async file uploads with progress tracking

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- AWS Account with S3 access
- S3 bucket created and configured

### 2. File Size Limits

- **Regular images**: Up to 50MB (JPEG, PNG, GIF, etc.)
- **RAW files**: Up to 500MB (CR2, NEF, ARW, etc.)
- **Supported formats**: All common image formats + RAW camera formats

### 3. Clone & Setup

```bash
git clone <repo-url>
cd fastapi-s3-image-uploader
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure AWS

#### Option A: Automatic Setup (Recommended)
```bash
python setup.py
```

#### Option B: Manual Configuration
Create a `.env` file:
```env
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=your-region-here
S3_BUCKET_NAME=your-bucket-name-here
```

### 6. Run the Application

```bash
uvicorn main:app --reload
```

### 7. Open in Browser

Navigate to: http://localhost:8000

### 8. Access API Documentation

Once the server is running, you can access:

- **Interactive API Docs**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **Detailed Documentation**: See `API_ENDPOINTS.md` file

## 🔧 AWS S3 Configuration

### 1. Create S3 Bucket

- Go to [AWS S3 Console](https://console.aws.amazon.com/s3/)
- Click "Create bucket"
- Choose a unique name
- Select your preferred region
- **Important**: Uncheck "Block all public access" if you want public image access

### 2. Configure Bucket Policy

Apply this policy to your bucket (replace `your-bucket-name`):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": [
                "arn:aws:s3:::your-bucket-name/uploads/*",
                "arn:aws:s3:::your-bucket-name/raw/*",
                "arn:aws:s3:::your-bucket-name/processed/*",
                "arn:aws:s3:::your-bucket-name/thumbnails/*"
            ]
        }
    ]
}
```

**Note**: This policy allows public read access to all image folders. For production use, consider restricting access as needed.

### 3. Create IAM User

- Go to [IAM Console](https://console.aws.amazon.com/iam/)
- Create new user with programmatic access
- Attach `AmazonS3FullAccess` policy (or create custom policy)
- Save Access Key ID and Secret Access Key

## 📸 RAW Image Processing & File Mapping

### How It Works

The application automatically processes RAW camera files and creates a smart mapping system:

### Automatic Folder Structure

The system automatically creates and organizes files in these S3 folders:

- **`uploads/`**: Regular image files (JPEG, PNG, GIF, etc.)
- **`raw/`**: Original RAW camera files (CR2, NEF, ARW, etc.)
- **`processed/`**: JPEG versions of RAW files for web viewing
- **`thumbnails/`**: Small preview images for all files

1. **Upload**: When you upload ANY file (RAW or regular), the system:
   - **RAW files**: Stores original in `raw/`, converts to JPEG in `processed/`, creates thumbnail
   - **Regular files**: Stores original in `uploads/`, creates thumbnail
   - **All files**: Saves mapping relationship in `file_mapping.json`

2. **File Mapping**: The `file_mapping.json` file maintains the relationship between:
   - **Uploaded filename**: `20250822_001354_2d95b20a.jpg`
   - **Original filename**: `IMG_001.CR2` or `vacation_photo.jpeg`
   - **File type**: `raw` or `regular`
   - **Full URL**: Complete S3 URL with proper extension

3. **Download Links**: When viewing any image, you get:
   - **For RAW files**: JPEG (processed) + RAW (original) downloads
   - **For regular files**: Original file download
   - **All downloads**: Include proper filenames and extensions

### File Structure Example

```json
{
  "file_mappings": {
    "20250822_001354_2d95b20a.jpg": {
      "original_filename": "IMG_001.CR2",
      "file_url": "https://bucket.s3.region.amazonaws.com/raw/20250822_001354_2d95b20a.CR2",
      "file_type": "raw",
      "mapped_at": "2025-08-22T00:13:54.123456"
    },
    "20250822_004500_a1b2c3d4.png": {
      "original_filename": "screenshot.png",
      "file_url": "https://bucket.s3.region.amazonaws.com/uploads/20250822_004500_a1b2c3d4.png",
      "file_type": "regular",
      "mapped_at": "2025-08-22T00:45:00.123456"
    }
  },
  "last_updated": "2025-08-22T00:45:00.123456"
}
```

### Supported RAW Formats

- **Canon**: CR2, CR3
- **Nikon**: NEF, NRW
- **Sony**: ARW, SR2, SRW
- **Fujifilm**: RAF
- **Adobe**: DNG
- **And many more**: ORF, PEF, RW2, etc.

### How File Mapping Works

The system automatically creates a mapping database (`file_mapping.json`) that tracks:

1. **File Relationships**: Links uploaded files to their original names
2. **Type Classification**: Identifies RAW vs. regular images
3. **URL Generation**: Creates complete download links with proper extensions
4. **Metadata Tracking**: Records upload timestamps and file information

This mapping system ensures that:
- Download links always include the correct file extension
- Users can access both processed and original versions
- File relationships are maintained even after processing
- The system can handle mixed file types efficiently

## 📁 Project Structure

```
fastapi-s3-image-uploader/
├── main.py                    # FastAPI application entry point
├── requirements.txt           # Python dependencies
├── setup.py                  # Automated setup wizard
├── .env.example              # Environment variables template
├── s3_bucket_policy.json     # S3 bucket policy template
├── check_bucket.py           # S3 bucket connection test
├── file_mapping.json         # File mapping database (auto-generated)
├── static/                   # Frontend files
│   ├── index.html           # Main HTML page with drag & drop
│   ├── style.css            # Modern CSS with animations
│   └── script.js            # Frontend logic and S3 integration
└── utils/                    # Backend utilities
    ├── __init__.py          # Package initialization
    ├── s3_uploader.py       # S3 upload and file management
    └── raw_processor.py     # RAW image processing engine
```

## 🧪 Testing

### Health Check
```bash
curl http://localhost:8000/health
```

### Upload Test
```bash
curl -X POST -F "file=@test-image.jpg" http://localhost:8000/upload
```

### List Images
```bash
curl http://localhost:8000/images?limit=10
```

## 🔌 API Endpoints

- **`GET /`**: Main application page
- **`POST /upload`**: Upload image file (supports RAW and regular formats)
- **`GET /images`**: List all images with metadata
- **`GET /health`**: Health check endpoint
- **`GET /static/*`**: Static files (CSS, JS, images)

### 📚 API Documentation

The API includes comprehensive automatic documentation:

- **Interactive Swagger UI**: Visit `http://localhost:8000/docs` for live API testing
- **OpenAPI Schema**: Available at `http://localhost:8000/openapi.json`
- **Detailed Endpoint Docs**: See `API_ENDPOINTS.md` for complete documentation with examples

#### Features of Auto-Documentation:
- **Request/Response Models**: Pydantic models with detailed field descriptions
- **Example Requests**: cURL, Python, and JavaScript examples for each endpoint
- **Error Responses**: Comprehensive error handling documentation
- **Schema Validation**: Automatic request/response validation
- **Live Testing**: Try endpoints directly from the browser

## 🔍 Troubleshooting

### Common Issues

#### 1. Static Files Not Loading
- Ensure file paths in HTML use `/static/` prefix
- Check that `app.mount("/static", ...)` is configured

#### 2. S3 Upload Fails
- Verify AWS credentials in `.env` file
- Check bucket permissions and policy
- Ensure region matches bucket location

#### 3. Region Mismatch Error
- The app automatically handles region-specific URLs
- For non-standard regions (like `mx-central-1`), URLs include region
- For standard regions (like `us-east-1`), URLs are simplified

#### 4. File Mapping Issues
- Check that `file_mapping.json` exists and is writable
- Verify S3 permissions for all folder types (uploads/, raw/, processed/, thumbnails/)
- Ensure the bucket policy includes all necessary folder paths
- Check logs for mapping creation errors

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🚀 Deployment

### Production Considerations

- Use proper WSGI server (Gunicorn, uvicorn with workers)
- Set `--host 0.0.0.0` for external access
- Configure reverse proxy (Nginx, Apache)
- Use environment variables for configuration
- Enable HTTPS with SSL certificates

### Docker Support

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Styled with modern CSS3
- Powered by [AWS S3](https://aws.amazon.com/s3/)

---

**Happy coding! 🎉**