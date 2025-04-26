#!/usr/bin/env python
"""
Simplest S3 crawler example with hardcoded values.
Just edit the constants below and run this script.
"""

import os
import logging
import boto3
import sys
import shutil
import hashlib
from botocore.exceptions import ClientError, NoCredentialsError
from vibe_scraping.crawler import WebCrawler
from dotenv import load_dotenv

load_dotenv()

# ===== EDIT THESE VALUES =====
URL = "https://newshub.ge"
BUCKET = "first-hapttic-bucket"
S3_PREFIX = "crawler_data/newshub"
MAX_PAGES = 10
MAX_DEPTH = 5
REMOVE_LOCAL_FILES = True  # Set to False if you want to keep local files
SKIP_EXISTING = True       # Set to True to skip files that already exist in S3
# ============================

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Crawl the website
logger.info(f"Starting crawl of {URL}")
local_dir = "./data_to_upload"
os.makedirs(local_dir, exist_ok=True)

# Create and run crawler
crawler = WebCrawler(
    start_url=URL,
    max_depth=MAX_DEPTH,
    max_pages=MAX_PAGES,
    respect_robots_txt=False,
    save_path=local_dir
)

result = crawler.crawl()
pages = result.get('pages_crawled', 0) if isinstance(result, dict) else result
logger.info(f"Crawled {pages} pages to {local_dir}")

# Get AWS credentials from environment variables
aws_access_key_id = os.environ.get('AWS_ACCESS_KEY')
aws_secret_access_key = os.environ.get('AWS_SECRET_KEY')
aws_session_token = os.environ.get('AWS_SESSION_TOKEN')  # Optional for temporary credentials
aws_region = os.environ.get('AWS_REGION', 'us-east-1')  # Default to us-east-1 if not specified

# Validate AWS credentials
if not aws_access_key_id or not aws_secret_access_key:
    logger.error("AWS credentials not found in environment variables.")
    logger.error("Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables.")
    print("\nCrawl and upload summary:")
    print(f"Crawled {pages} pages from {URL}")
    print("Upload to S3 skipped: Missing AWS credentials")
    sys.exit(1)

# Upload to S3
logger.info(f"Uploading to S3 bucket: {BUCKET}")
try:
    s3 = boto3.client(
        's3',
        region_name=aws_region,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token if aws_session_token else None
    )
    
    # Test credentials by listing buckets
    try:
        s3.head_bucket(Bucket=BUCKET)
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == '403':
            logger.error("Access denied. Your AWS credentials don't have permission to access this bucket.")
            sys.exit(1)
        elif error_code == '404':
            logger.error(f"Bucket {BUCKET} does not exist.")
            sys.exit(1)
        elif error_code == 'InvalidAccessKeyId':
            logger.error("Invalid AWS access key ID. Please check your credentials.")
            sys.exit(1)
        else:
            logger.error(f"Error accessing bucket: {e}")
            sys.exit(1)
            
except NoCredentialsError:
    logger.error("AWS credentials not found or are invalid.")
    sys.exit(1)
except Exception as e:
    logger.error(f"Error initializing S3 client: {e}")
    sys.exit(1)

# Track upload statistics
files_uploaded = 0
bytes_uploaded = 0
files_skipped = 0

# Helper function to check if a file exists in S3
def file_exists_in_s3(s3_key):
    try:
        s3.head_object(Bucket=BUCKET, Key=s3_key)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        else:
            logger.error(f"Error checking if file exists in S3: {e}")
            return False

# Helper function to calculate file MD5 hash
def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# Helper function to upload a file to S3
def upload_file(file_path, s3_key):
    global files_uploaded, bytes_uploaded, files_skipped
    
    # Check if file already exists in S3 and should be skipped
    if SKIP_EXISTING and file_exists_in_s3(s3_key):
        logger.info(f"Skipping {file_path} - already exists in S3")
        files_skipped += 1
        return True
    
    try:
        file_size = os.path.getsize(file_path)
        logger.info(f"Uploading {file_path} to s3://{BUCKET}/{s3_key}")
        s3.upload_file(file_path, BUCKET, s3_key)
        files_uploaded += 1
        bytes_uploaded += file_size
        return True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'InvalidAccessKeyId':
            logger.error("Invalid AWS access key ID. Please check your credentials.")
            return False
        logger.error(f"Error uploading {file_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error uploading {file_path}: {e}")
        return False

# Walk through the local directory and upload all files
for root, dirs, files in os.walk(local_dir):
    # Get the relative path from the root directory
    relative_path = os.path.relpath(root, local_dir)
    
    # Upload all files in this directory
    for file in files:
        local_file_path = os.path.join(root, file)
        
        # Create S3 key (path within the bucket)
        if relative_path == ".":
            s3_key = f"{S3_PREFIX}/{file}"
        else:
            s3_key = f"{S3_PREFIX}/{relative_path}/{file}"
            
        upload_file(local_file_path, s3_key)

# Clean up local files if requested
if REMOVE_LOCAL_FILES and os.path.exists(local_dir):
    logger.info(f"Removing local directory: {local_dir}")
    try:
        shutil.rmtree(local_dir)
        logger.info(f"Successfully removed {local_dir}")
    except Exception as e:
        logger.error(f"Error removing local directory {local_dir}: {e}")

# Print summary
print("\nCrawl and upload summary:")
print(f"Crawled {pages} pages from {URL}")
print(f"Uploaded {files_uploaded} files ({bytes_uploaded / (1024*1024):.2f} MB)")
print(f"Skipped {files_skipped} existing files")
print(f"Files stored in S3 bucket: {BUCKET}/{S3_PREFIX}")
if REMOVE_LOCAL_FILES:
    print(f"Local directory {local_dir} {'removed' if not os.path.exists(local_dir) else 'could not be removed'}") 