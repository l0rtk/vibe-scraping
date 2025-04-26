#!/usr/bin/env python
"""
Crawler module that provides a function to crawl a website and upload data to S3.
"""

import os
import logging
import boto3
import shutil
from urllib.parse import urlparse
import tldextract
from botocore.exceptions import ClientError, NoCredentialsError
from vibe_scraping.crawler import WebCrawler
from dotenv import load_dotenv
from boto3.s3.transfer import TransferConfig
import json

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_domain(url):
    """
    Extract clean domain from URL using tldextract.
    Returns format like 'example.com' without subdomain or 'www.'
    """
    extracted = tldextract.extract(url)
    # Return the registered domain (domain + suffix, e.g., example.com)
    return f"{extracted.domain}.{extracted.suffix}"

def crawler_func(websites, 
                bucket="first-hapttic-bucket", 
                max_pages=5000, 
                max_depth=5, 
                remove_local_files=True, 
                skip_existing=True,
                force_fresh_crawl=True):
    """
    Crawls websites and uploads the data to an S3 bucket.
    
    Args:
        websites (str or list): URL or list of URLs to crawl
        bucket (str): S3 bucket name
        max_pages (int): Maximum number of pages to crawl
        max_depth (int): Maximum depth to crawl
        remove_local_files (bool): Whether to remove local files after upload
        skip_existing (bool): Whether to skip existing files in S3
        force_fresh_crawl (bool): Whether to force a fresh crawl by disabling HTTP cache
        
    Returns:
        dict: Summary of the crawl and upload operation
    """
    # Ensure websites is a list
    if isinstance(websites, str):
        websites = [websites]
        
    # Create a map of URLs to their extracted domains and S3 prefixes
    url_to_domain = {url: extract_domain(url) for url in websites}
    url_to_raw_domain = {url: urlparse(url).netloc for url in websites}
    
    # Get unique clean domains
    domains = list(set(url_to_domain.values()))
    
    # Create mapping from raw domain to extracted domain
    raw_to_extracted = {
        url_to_raw_domain[url]: url_to_domain[url] 
        for url in websites
    }
    
    # Create mapping from domain to S3 prefix
    domain_to_prefix = {domain: f"crawler_data/{domain}" for domain in domains}
    
    # Crawl the websites
    logger.info(f"Starting crawl of {len(websites)} websites: {', '.join(websites)}")
    local_dir = "./data_to_upload"
    os.makedirs(local_dir, exist_ok=True)

    # Create and run crawler with force_fresh_crawl option
    crawler = WebCrawler(
        start_urls=websites,
        max_depth=max_depth,
        max_pages=max_pages,
        respect_robots_txt=False,
        save_path=local_dir,
        force_fresh_crawl=force_fresh_crawl
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
            'websites': websites,
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
                    'websites': websites,
                    'error': 'Access denied to S3 bucket'
                }
            elif error_code == '404':
                logger.error(f"Bucket {bucket} does not exist.")
                return {
                    'success': False,
                    'pages_crawled': pages,
                    'websites': websites,
                    'error': f"Bucket {bucket} does not exist"
                }
            elif error_code == 'InvalidAccessKeyId':
                logger.error("Invalid AWS access key ID. Please check your credentials.")
                return {
                    'success': False,
                    'pages_crawled': pages,
                    'websites': websites,
                    'error': 'Invalid AWS access key ID'
                }
            else:
                logger.error(f"Error accessing bucket: {e}")
                return {
                    'success': False,
                    'pages_crawled': pages,
                    'websites': websites,
                    'error': f"Error accessing bucket: {str(e)}"
                }
                
    except NoCredentialsError:
        logger.error("AWS credentials not found or are invalid.")
        return {
            'success': False,
            'pages_crawled': pages,
            'websites': websites,
            'error': 'AWS credentials not found or are invalid'
        }
    except Exception as e:
        logger.error(f"Error initializing S3 client: {e}")
        return {
            'success': False,
            'pages_crawled': pages,
            'websites': websites,
            'error': f"Error initializing S3 client: {str(e)}"
        }

    # Track upload statistics
    files_uploaded = 0
    bytes_uploaded = 0
    files_skipped = 0
    
    # Get all existing objects in each S3 prefix for efficient checking
    existing_s3_objects_by_prefix = {}
    if skip_existing:
        for domain, prefix in domain_to_prefix.items():
            logger.info(f"Fetching existing objects in s3://{bucket}/{prefix}")
            try:
                existing_objects = set()
                paginator = s3.get_paginator('list_objects_v2')
                page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)
                for page in page_iterator:
                    if 'Contents' in page:
                        for obj in page['Contents']:
                            existing_objects.add(obj['Key'])
                existing_s3_objects_by_prefix[prefix] = existing_objects
                logger.info(f"Found {len(existing_objects)} existing objects in s3://{bucket}/{prefix}")
            except Exception as e:
                logger.warning(f"Error fetching existing S3 objects for {prefix}: {e}")
                existing_s3_objects_by_prefix[prefix] = set()

    # Create a URL to domain/prefix mapping for all pages crawled
    url_to_domain_map = {}
    
    # First, try to get the mapping from metadata files
    for root, dirs, files in os.walk(local_dir):
        for file in files:
            if file == "metadata.json":
                try:
                    metadata_path = os.path.join(root, file)
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    
                    if "url" in metadata:
                        url = metadata["url"]
                        # Extract clean domain using tldextract
                        clean_domain = extract_domain(url)
                        if clean_domain in domain_to_prefix:
                            url_to_domain_map[os.path.dirname(metadata_path)] = clean_domain
                except Exception as e:
                    logger.warning(f"Error reading metadata file {metadata_path}: {e}")
    
    # Helper function to determine the S3 prefix for a file
    def get_s3_prefix_for_file(file_path):
        # First check if this file's directory has a mapping
        directory = os.path.dirname(file_path)
        if directory in url_to_domain_map:
            domain = url_to_domain_map[directory]
            return domain_to_prefix[domain]
        
        # For files without a mapping, try to determine from metadata.json in their directory
        metadata_path = os.path.join(os.path.dirname(file_path), "metadata.json")
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                if "url" in metadata:
                    url = metadata["url"]
                    clean_domain = extract_domain(url)
                    if clean_domain in domain_to_prefix:
                        # Add to our mapping for future lookups
                        url_to_domain_map[os.path.dirname(file_path)] = clean_domain
                        return domain_to_prefix[clean_domain]
            except Exception as e:
                logger.warning(f"Error determining domain for {file_path}: {e}")
        
        # If no mapping available, use the first domain as fallback
        return domain_to_prefix[domains[0]]

    # Helper function to upload a file to S3
    def upload_file(file_path, relative_path):
        nonlocal files_uploaded, bytes_uploaded, files_skipped
        
        # Determine which S3 prefix to use based on the file's URL domain
        s3_prefix = get_s3_prefix_for_file(file_path)
        
        # Create S3 key (path within the bucket)
        if relative_path == ".":
            s3_key = f"{s3_prefix}/{os.path.basename(file_path)}"
        else:
            # Preserve directory structure by using the full relative path
            # This will include the hash directory and maintain structure
            if relative_path != os.path.basename(relative_path):
                s3_key = f"{s3_prefix}/{relative_path}"
            else:
                s3_key = f"{s3_prefix}/{relative_path}/{os.path.basename(file_path)}"
        
        # Check if file already exists in S3 and should be skipped
        if skip_existing and s3_prefix in existing_s3_objects_by_prefix and s3_key in existing_s3_objects_by_prefix[s3_prefix]:
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
            upload_file(local_file_path, relative_path if relative_path != "." else file)

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
        'websites': websites,
        'files_uploaded': files_uploaded,
        'files_skipped': files_skipped,
        'bytes_uploaded': bytes_uploaded,
        'bucket': bucket,
        's3_prefixes': list(domain_to_prefix.values()),
        'domains': domains,
        'local_files_removed': not os.path.exists(local_dir) if remove_local_files else False
    }
    
    return summary

# Example usage
if __name__ == "__main__":
    websites = ["https://newshub.ge", "https://www.ambebi.ge"]
    result = crawler_func(websites)
    
    # Print summary
    print("\nCrawl and upload summary:")
    print(f"Crawled {result['pages_crawled']} pages from {len(result['websites'])} websites")
    
    if result['success']:
        print(f"Uploaded {result['files_uploaded']} files ({result['bytes_uploaded'] / (1024*1024):.2f} MB)")
        print(f"Skipped {result['files_skipped']} existing files")
        print(f"Files stored in S3 bucket: {result['bucket']} with prefixes:")
        for prefix in result['s3_prefixes']:
            print(f"  - {prefix}")
        if result.get('local_files_removed', False):
            print("Local files have been removed.")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}") 