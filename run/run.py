from crawl_and_upload import crawler_func

# List of websites to crawl
websites = [
    "https://www.ambebi.ge/",
    "https://www.alia.ge/",
    "https://primetime.ge/",
    "https://www.palitravideo.ge/",
    "https://www.interpressnews.ge/ka/"
]

if __name__ == "__main__":
    # Run a single crawl for all websites
    result = crawler_func(websites=websites)
    
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