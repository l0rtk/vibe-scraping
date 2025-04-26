#!/usr/bin/env python
"""
Simplest S3 crawler example with hardcoded values.
Just edit the constants below and run this script.
"""

import os
import logging
import boto3
from vibe_scraping.crawler import WebCrawler
from dotenv import load_dotenv

load_dotenv()

# ===== EDIT THESE VALUES =====
URL = "https://newshub.ge"
BUCKET = "first-hapttic-bucket"
S3_PREFIX = "crawler_data/newshub"
MAX_PAGES = 10
MAX_DEPTH = 5
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

# Upload to S3
logger.info(f"Uploading to S3 bucket: {BUCKET}")
s3 = boto3.client(
    's3',
    region_name=aws_region,
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    aws_session_token=aws_session_token if aws_session_token else None
)

# Track upload statistics
files_uploaded = 0
bytes_uploaded = 0

# Helper function to upload a file to S3
def upload_file(file_path, s3_key):
    global files_uploaded, bytes_uploaded
    try:
        file_size = os.path.getsize(file_path)
        logger.info(f"Uploading {file_path} to s3://{BUCKET}/{s3_key}")
        s3.upload_file(file_path, BUCKET, s3_key)
        files_uploaded += 1
        bytes_uploaded += file_size
        return True
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

# Print summary
print("\nCrawl and upload summary:")
print(f"Crawled {pages} pages from {URL}")
print(f"Uploaded {files_uploaded} files ({bytes_uploaded / (1024*1024):.2f} MB)")
print(f"Files stored in S3 bucket: {BUCKET}/{S3_PREFIX}") 