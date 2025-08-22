#!/usr/bin/env python3
"""
Setup script for FastAPI S3 Image Uploader project
This script helps configure the project and test AWS connectivity
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file from user input"""
    print("🔧 Setting up FastAPI S3 Image Uploader project")
    print("=" * 50)
    
    # Check if .env already exists
    if Path('.env').exists():
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it? (y/N): ").lower()
        if response != 'y':
            print("Setup cancelled.")
            return
    
    print("\n📝 Please provide your AWS credentials:")
    
    # Get AWS credentials
    access_key = input("AWS Access Key ID: ").strip()
    secret_key = input("AWS Secret Access Key: ").strip()
    region = input("AWS Region (default: us-east-1): ").strip() or "us-east-1"
    bucket_name = input("S3 Bucket Name: ").strip()
    
    if not all([access_key, secret_key, bucket_name]):
        print("❌ All fields are required!")
        return
    
    # Create .env file
    env_content = f"""# AWS Credentials
AWS_ACCESS_KEY_ID={access_key}
AWS_SECRET_ACCESS_KEY={secret_key}
AWS_REGION={region}

# S3 Configuration
S3_BUCKET_NAME={bucket_name}
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ .env file created successfully!")
    print(f"📁 Bucket: {bucket_name}")
    print(f"🌍 Region: {region}")

def test_aws_connection():
    """Test AWS connection and bucket access"""
    print("\n🧪 Testing AWS connection...")
    
    try:
        from dotenv import load_dotenv
        from utils.s3_uploader import S3Uploader
        
        load_dotenv()
        s3_uploader = S3Uploader()
        
        if s3_uploader.test_connection():
            print("✅ AWS connection successful!")
            print("✅ S3 bucket access confirmed!")
            return True
        else:
            print("❌ AWS connection failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error testing connection: {e}")
        return False

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    
    try:
        import subprocess
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Dependencies installed successfully!")
        return True
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 FastAPI S3 Image Uploader - Setup Wizard")
    print("=" * 50)
    
    # Check if requirements.txt exists
    if not Path('requirements.txt').exists():
        print("❌ requirements.txt not found!")
        print("Please run this script from the project root directory.")
        return
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies. Please check your Python environment.")
        return
    
    # Create .env file
    create_env_file()
    
    # Test connection
    if test_aws_connection():
        print("\n🎉 Setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Run: uvicorn main:app --reload")
        print("2. Open: http://localhost:8000")
        print("3. Start uploading images!")
    else:
        print("\n⚠️  Setup completed but AWS connection failed.")
        print("Please check your credentials and try again.")

if __name__ == "__main__":
    main()
