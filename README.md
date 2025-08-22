# 🚀 AWS S3 Image Upload Experiment

A modern web application that allows users to upload images directly to an AWS S3 bucket using FastAPI backend and a beautiful drag & drop frontend.

## ✨ Features

- **🖼️ Image Upload**: Drag & drop or click to browse
- **☁️ Direct S3 Integration**: Images go straight to your S3 bucket
- **🎨 Modern UI**: Beautiful, responsive design with smooth animations
- **🔒 Secure**: File validation, size limits, and type checking
- **📱 Responsive**: Works perfectly on desktop and mobile
- **⚡ Fast**: Built with FastAPI for high performance

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

### 2. Clone & Setup

```bash
git clone <your-repo-url>
cd aws-experiments
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure AWS

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

### 5. Run the Application

```bash
uvicorn main:app --reload
```

### 6. Open in Browser

Navigate to: http://localhost:8000

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
            "Resource": "arn:aws:s3:::your-bucket-name/uploads/*"
        }
    ]
}
```

### 3. Create IAM User

- Go to [IAM Console](https://console.aws.amazon.com/iam/)
- Create new user with programmatic access
- Attach `AmazonS3FullAccess` policy (or create custom policy)
- Save Access Key ID and Secret Access Key

## 📁 Project Structure

```
aws-experiments/
├── main.py                 # FastAPI application
├── requirements.txt        # Python dependencies
├── setup.py               # Automated setup script
├── .env.example           # Environment variables template
├── s3_bucket_policy.json  # S3 bucket policy template
├── static/                # Frontend files
│   ├── index.html        # Main HTML page
│   ├── style.css         # Modern CSS styles
│   └── script.js         # Frontend logic
└── utils/                 # Backend utilities
    ├── __init__.py       # Package initialization
    └── s3_uploader.py    # S3 upload handling
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