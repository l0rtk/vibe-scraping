from vibe_scraping.crawler import WebCrawler

# Create and run crawler
crawler = WebCrawler(
    start_url="https://newshub.ge",
    save_path="./newshub_data_69",
    max_depth=10,
    max_pages=10000,
    respect_robots_txt=False,
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

result = crawler.crawl()
pages = result.get('pages_crawled', 0) if isinstance(result, dict) else result
print(f"Crawled {pages} pages to ./newshub_data")

"""
This will deeply crawl the website using Scrapy and save the content to the specified directory.
"""