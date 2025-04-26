from crawl_and_upload import crawler_func
import argparse
import sys

# Default list of websites to crawl
default_websites = [
    "https://www.ambebi.ge/",
    "https://www.alia.ge/",
    "https://primetime.ge/",
    "https://www.palitravideo.ge/",
    "https://www.interpressnews.ge/ka/"
]

def parse_args():
    parser = argparse.ArgumentParser(description='Web crawler with S3 upload')
    parser.add_argument('--websites', '-w', nargs='+', help='List of websites to crawl', default=None)
    parser.add_argument('--max-pages', '-p', type=int, default=5000, help='Maximum number of pages to crawl')
    parser.add_argument('--max-depth', '-d', type=int, default=5, help='Maximum crawl depth')
    parser.add_argument('--no-remove-local', action='store_false', dest='remove_local', 
                        help='Do not remove local files after upload')
    parser.add_argument('--bucket', '-b', type=str, default="second-hapttic-bucket", 
                        help='S3 bucket name')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    # Use provided websites or fall back to defaults
    websites = args.websites if args.websites else default_websites
    
    print(f"Starting crawl for {len(websites)} websites:")
    for website in websites:
        print(f"  - {website}")
    
    # Run a single crawl for all websites
    result = crawler_func(
        websites=websites,
        max_pages=args.max_pages,
        max_depth=args.max_depth,
        remove_local_files=args.remove_local,
        bucket=args.bucket
    )
    
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