#!/usr/bin/env python
"""
Crawler module that provides a function to crawl a website and upload data to S3.
"""

import os
import logging
import boto3
import sys
import shutil
import hashlib
from urllib.parse import urlparse
from botocore.exceptions import ClientError, NoCredentialsError
from vibe_scraping.crawler import WebCrawler
from dotenv import load_dotenv
from boto3.s3.transfer import TransferConfig

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def crawler_func(website, 
                bucket="first-hapttic-bucket", 
                max_pages=300, 
                max_depth=5, 
                remove_local_files=True, 
                skip_existing=True):
    """
    Crawls a website and uploads the data to an S3 bucket.
    
    Args:
        website (str): URL of the website to crawl
        bucket (str): S3 bucket name
        max_pages (int): Maximum number of pages to crawl
        max_depth (int): Maximum depth to crawl
        remove_local_files (bool): Whether to remove local files after upload
        skip_existing (bool): Whether to skip existing files in S3
        
    Returns:
        dict: Summary of the crawl and upload operation
    """
    # Extract domain for S3 prefix
    domain = urlparse(website).netloc
    s3_prefix = f"crawler_data/{domain}"
    
    # Crawl the website
    logger.info(f"Starting crawl of {website}")
    local_dir = "./data_to_upload"
    os.makedirs(local_dir, exist_ok=True)

    # Create and run crawler
    crawler = WebCrawler(
        start_url=website,
        max_depth=max_depth,
        max_pages=max_pages,

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
        return {
            'success': False,
            'pages_crawled': pages,
            'website': website,
            'error': 'Missing AWS credentials'
        }

    # Upload to S3
    logger.info(f"Uploading to S3 bucket: {bucket}")
    try:
        s3 = boto3.client(
            's3',
            region_name=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token if aws_session_token else None
        )
        
        # Configure transfer configuration for parallel uploads
        transfer_config = TransferConfig(
            multipart_threshold=8 * 1024 * 1024,  # 8MB
            max_concurrency=10,                   # 10 threads
            multipart_chunksize=8 * 1024 * 1024,  # 8MB
            use_threads=True
        )
        
        # Test credentials by listing buckets
        try:
            s3.head_bucket(Bucket=bucket)
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == '403':
                logger.error("Access denied. Your AWS credentials don't have permission to access this bucket.")
                return {
                    'success': False,
                    'pages_crawled': pages,
                    'website': website,
                    'error': 'Access denied to S3 bucket'
                }
            elif error_code == '404':
                logger.error(f"Bucket {bucket} does not exist.")
                return {
                    'success': False,
                    'pages_crawled': pages,
                    'website': website,
                    'error': f"Bucket {bucket} does not exist"
                }
            elif error_code == 'InvalidAccessKeyId':
                logger.error("Invalid AWS access key ID. Please check your credentials.")
                return {
                    'success': False,
                    'pages_crawled': pages,
                    'website': website,
                    'error': 'Invalid AWS access key ID'
                }
            else:
                logger.error(f"Error accessing bucket: {e}")
                return {
                    'success': False,
                    'pages_crawled': pages,
                    'website': website,
                    'error': f"Error accessing bucket: {str(e)}"
                }
                
    except NoCredentialsError:
        logger.error("AWS credentials not found or are invalid.")
        return {
            'success': False,
            'pages_crawled': pages,
            'website': website,
            'error': 'AWS credentials not found or are invalid'
        }
    except Exception as e:
        logger.error(f"Error initializing S3 client: {e}")
        return {
            'success': False,
            'pages_crawled': pages,
            'website': website,
            'error': f"Error initializing S3 client: {str(e)}"
        }

    # Track upload statistics
    files_uploaded = 0
    bytes_uploaded = 0
    files_skipped = 0
    
    # Get all existing objects in the S3 prefix for efficient checking
    existing_s3_objects = set()
    if skip_existing:
        logger.info(f"Fetching existing objects in s3://{bucket}/{s3_prefix}")
        try:
            paginator = s3.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(Bucket=bucket, Prefix=s3_prefix)
            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        existing_s3_objects.add(obj['Key'])
            logger.info(f"Found {len(existing_s3_objects)} existing objects in S3")
        except Exception as e:
            logger.warning(f"Error fetching existing S3 objects: {e}. Will check files individually.")

    # Helper function to upload a file to S3
    def upload_file(file_path, s3_key):
        nonlocal files_uploaded, bytes_uploaded, files_skipped
        
        # Check if file already exists in S3 and should be skipped
        if skip_existing and s3_key in existing_s3_objects:
            logger.info(f"Skipping {file_path} - already exists in S3")
            files_skipped += 1
            return True
        
        try:
            file_size = os.path.getsize(file_path)
            logger.info(f"Uploading {file_path} to s3://{bucket}/{s3_key}")
            s3.upload_file(
                file_path, 
                bucket, 
                s3_key,
                Config=transfer_config
            )
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
                s3_key = f"{s3_prefix}/{file}"
            else:
                s3_key = f"{s3_prefix}/{relative_path}/{file}"
                
            upload_file(local_file_path, s3_key)

    # Clean up local files if requested
    if remove_local_files and os.path.exists(local_dir):
        logger.info(f"Removing local directory: {local_dir}")
        try:
            shutil.rmtree(local_dir)
            logger.info(f"Successfully removed {local_dir}")
        except Exception as e:
            logger.error(f"Error removing local directory {local_dir}: {e}")

    # Create a summary
    summary = {
        'success': True,
        'pages_crawled': pages,
        'website': website,
        'files_uploaded': files_uploaded,
        'files_skipped': files_skipped,
        'bytes_uploaded': bytes_uploaded,
        'bucket': bucket,
        's3_prefix': s3_prefix,
        'local_files_removed': not os.path.exists(local_dir) if remove_local_files else False
    }
    
    return summary

# Example usage
if __name__ == "__main__":
    website = "https://newshub.ge"
    result = crawler_func(website)
    
    # Print summary
    print("\nCrawl and upload summary:")
    print(f"Crawled {result['pages_crawled']} pages from {result['website']}")
    
    if result['success']:
        print(f"Uploaded {result['files_uploaded']} files ({result['bytes_uploaded'] / (1024*1024):.2f} MB)")
        print(f"Skipped {result['files_skipped']} existing files")
        print(f"Files stored in S3 bucket: {result['bucket']}/{result['s3_prefix']}")
        if result.get('local_files_removed', False):
            print("Local files have been removed.")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}") 