from crawl_and_upload import crawler_func


websites = [
    "https://www.ambebi.ge/",
    "https://www.alia.ge/",
    "https://primetime.ge/",
    "https://www.palitravideo.ge/",
    "https://www.interpressnews.ge/ka/"
]

if __name__ == "__main__":
    for website in websites:
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