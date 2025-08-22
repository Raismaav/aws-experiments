#!/usr/bin/env python3
"""
Script to check S3 bucket configuration and region
"""

import boto3
from dotenv import load_dotenv
import os

def check_bucket_info():
    """Check bucket information and region"""
    load_dotenv()
    
    # Get credentials from environment
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    region = os.getenv('AWS_REGION')
    bucket_name = os.getenv('S3_BUCKET_NAME')
    
    print("🔍 Checking S3 bucket configuration...")
    print(f"Access Key: {access_key[:10]}..." if access_key else "❌ Not set")
    print(f"Secret Key: {'*' * 10}..." if secret_key else "❌ Not set")
    print(f"Region: {region}")
    print(f"Bucket: {bucket_name}")
    print("-" * 50)
    
    if not all([access_key, secret_key, bucket_name]):
        print("❌ Missing credentials or bucket name!")
        return
    
    try:
        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        # Get bucket location
        response = s3_client.get_bucket_location(Bucket=bucket_name)
        bucket_region = response.get('LocationConstraint')
        
        if bucket_region is None:
            bucket_region = 'us-east-1'  # Default region
        
        print(f"✅ Bucket '{bucket_name}' found!")
        print(f"📍 Actual bucket region: {bucket_region}")
        print(f"🌍 Configured region: {region}")
        
        if bucket_region != region:
            print("⚠️  WARNING: Region mismatch!")
            print(f"   Bucket is in: {bucket_region}")
            print(f"   App configured for: {region}")
            print("\n💡 Solution: Update your .env file with the correct region")
        
        # Test bucket access
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print("✅ Bucket access confirmed!")
        except Exception as e:
            print(f"❌ Cannot access bucket: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_bucket_info()
