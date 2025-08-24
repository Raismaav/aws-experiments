# API Endpoints Documentation

## Overview

This document provides comprehensive documentation for all API endpoints in the AWS S3 Image Uploader service. The API supports both regular image formats and RAW camera formats with automatic processing and conversion.

## Base URL

```
http://localhost:8000
```

## Authentication

The API requires AWS credentials configured via environment variables:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `S3_BUCKET_NAME`

## Endpoints

### 1. Root Endpoint

**GET** `/`

Serves the main HTML interface for image upload and management.

**Response:**
- **Content-Type:** `text/html`
- **Body:** HTML page with upload interface

**Example:**
```bash
curl http://localhost:8000/
```

---

### 2. Upload Image

**POST** `/upload`

Upload an image file to AWS S3 with automatic processing and RAW format support.

**Request:**
- **Content-Type:** `multipart/form-data`
- **Body:** Form data with file field

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | Image file to upload (supports regular and RAW formats) |

**File Requirements:**
- Must be a valid image format
- Regular images: Standard size limits
- RAW files: Up to 500MB
- Supported RAW formats: CR2, CR3, NEF, ARW, RAF, DNG, and many more

**Response Models:**

#### Success Response (200)
```json
{
  "message": "RAW file processed and uploaded successfully",
  "filename": "IMG_001.CR2",
  "file_size": 45678912,
  "is_raw": true,
  "upload_time": "20241201_143022",
  "unique_id": "a1b2c3d4",
  "urls": {
    "raw": "https://bucket-name.s3.amazonaws.com/raw/20241201_143022_a1b2c3d4.CR2",
    "processed": "https://bucket-name.s3.amazonaws.com/processed/20241201_143022_a1b2c3d4.jpg",
    "thumbnail": "https://bucket-name.s3.amazonaws.com/thumbnails/20241201_143022_a1b2c3d4.jpg"
  },
  "metadata": {
    "width": 6000,
    "height": 4000,
    "colors": 3,
    "raw_type": "FoveonX3",
    "color_desc": "RGB",
    "black_level": 0,
    "white_level": 16383,
    "camera_whitebalance": [1.0, 1.0, 1.0],
    "daylight_whitebalance": [1.0, 1.0, 1.0]
  },
  "processing_info": {
    "original_format": "CR2",
    "converted_to": "JPEG",
    "thumbnail_created": true
  }
}
```

#### Regular Image Response (200)
```json
{
  "message": "Image uploaded successfully",
  "filename": "photo.jpg",
  "file_size": 2048576,
  "is_raw": false,
  "upload_time": "20241201_143022",
  "unique_id": "a1b2c3d4",
  "urls": {
    "image": "https://bucket-name.s3.amazonaws.com/uploads/20241201_143022_a1b2c3d4.jpg",
    "thumbnail": "https://bucket-name.s3.amazonaws.com/thumbnails/20241201_143022_a1b2c3d4.jpg"
  },
  "processing_info": {
    "format": "jpg",
    "thumbnail_created": true
  }
}
```

#### Error Responses

**400 Bad Request - Invalid File Type**
```json
{
  "detail": "File must be an image"
}
```

**400 Bad Request - File Too Large**
```json
{
  "detail": "File size must be less than 500MB"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Upload failed: [specific error message]"
}
```

**Example Requests:**

**Using cURL:**
```bash
# Upload a regular image
curl -X POST "http://localhost:8000/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@photo.jpg"

# Upload a RAW file
curl -X POST "http://localhost:8000/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@IMG_001.CR2"
```

**Using Python requests:**
```python
import requests

# Upload image
with open('photo.jpg', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/upload', files=files)
    print(response.json())
```

**Using JavaScript/Fetch:**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('/upload', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

---

### 3. List Images

**GET** `/images`

Retrieve a list of all images stored in the S3 bucket with comprehensive metadata.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | Integer | No | 50 | Maximum number of images to return (1-1000) |

**Response Model:**

#### Success Response (200)
```json
{
  "images": [
    {
      "key": "processed/20241201_143022_a1b2c3d4.jpg",
      "filename": "20241201_143022_a1b2c3d4.jpg",
      "folder": "processed",
      "is_raw": true,
      "timestamp": "20241201_143022",
      "size": 2048576,
      "last_modified": "2024-12-01T14:30:22.123Z",
      "url": "https://bucket-name.s3.amazonaws.com/processed/20241201_143022_a1b2c3d4.jpg",
      "thumbnail_url": "https://bucket-name.s3.amazonaws.com/thumbnails/20241201_143022_a1b2c3d4.jpg",
      "original_url": null,
      "raw_original_url": "https://bucket-name.s3.amazonaws.com/raw/20241201_143022_a1b2c3d4.CR2"
    },
    {
      "key": "uploads/20241201_143000_e5f6g7h8.jpg",
      "filename": "20241201_143000_e5f6g7h8.jpg",
      "folder": "uploads",
      "is_raw": false,
      "timestamp": "20241201_143000",
      "size": 1024000,
      "last_modified": "2024-12-01T14:30:00.456Z",
      "url": "https://bucket-name.s3.amazonaws.com/uploads/20241201_143000_e5f6g7h8.jpg",
      "thumbnail_url": "https://bucket-name.s3.amazonaws.com/thumbnails/20241201_143000_e5f6g7h8.jpg",
      "original_url": "https://bucket-name.s3.amazonaws.com/uploads/20241201_143000_e5f6g7h8.jpg",
      "raw_original_url": null
    }
  ],
  "total": 2,
  "limit": 50
}
```

#### Error Response (500)
```json
{
  "detail": "Failed to list images: [specific error message]"
}
```

**Example Requests:**

**Using cURL:**
```bash
# Get default limit (50 images)
curl "http://localhost:8000/images"

# Get specific limit
curl "http://localhost:8000/images?limit=10"
```

**Using Python requests:**
```python
import requests

# List images with limit
response = requests.get('http://localhost:8000/images', params={'limit': 25})
images = response.json()
print(f"Total images: {images['total']}")
```

**Using JavaScript/Fetch:**
```javascript
fetch('/images?limit=20')
  .then(response => response.json())
  .then(data => {
    console.log(`Total images: ${data.total}`);
    data.images.forEach(img => console.log(img.filename));
  });
```

---

### 4. Health Check

**GET** `/health`

Check the health status of the service.

**Response Model:**

#### Success Response (200)
```json
{
  "status": "healthy"
}
```

**Example Requests:**

**Using cURL:**
```bash
curl "http://localhost:8000/health"
```

**Using Python requests:**
```python
import requests

response = requests.get('http://localhost:8000/health')
print(response.json()['status'])  # Output: healthy
```

**Using JavaScript/Fetch:**
```javascript
fetch('/health')
  .then(response => response.json())
  .then(data => console.log(data.status));  // Output: healthy
```

---

## File Organization

The API organizes uploaded files in the following S3 structure:

```
bucket-name/
├── uploads/           # Regular image files
├── raw/              # Original RAW files
├── processed/         # Converted JPEG files from RAW
└── thumbnails/       # Thumbnails for all images
```

## RAW File Processing

When a RAW file is uploaded:

1. **Validation**: File format and size are validated
2. **Processing**: RAW file is converted to JPEG using rawpy
3. **Thumbnail**: A thumbnail is created for web display
4. **Storage**: 
   - Original RAW file stored in `raw/` folder
   - Converted JPEG stored in `processed/` folder
   - Thumbnail stored in `thumbnails/` folder
5. **Metadata**: Camera and image information is extracted
6. **Mapping**: File relationships are tracked for easy access

## Error Handling

All endpoints return appropriate HTTP status codes:

- **200**: Success
- **400**: Bad Request (invalid input)
- **500**: Internal Server Error

Error responses include a `detail` field with a descriptive message.

## Rate Limiting

Currently, no rate limiting is implemented. Consider implementing rate limiting for production use.

## CORS

CORS is not configured by default. For web applications, configure CORS headers as needed.

## Monitoring

The API includes comprehensive logging for:
- File uploads and processing
- S3 operations
- Error conditions
- Performance metrics

## Development

To run the API locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-east-1
export S3_BUCKET_NAME=your_bucket

# Run the server
python main.py
```

## Interactive Documentation

Once running, visit `http://localhost:8000/docs` for interactive Swagger UI documentation with:
- Live API testing
- Request/response examples
- Schema validation
- Try-it-out functionality

## Support

For API support or questions, contact the development team or refer to the project documentation.
