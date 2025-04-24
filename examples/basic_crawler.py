from vibe_scraping.crawler import WebCrawler

# Create and run crawler
crawler = WebCrawler(
    start_url="https://newshub.ge",
    max_depth=10,
    max_pages=10,
    respect_robots_txt=False,
)

result = crawler.crawl()
pages = result.get('pages_crawled', 0) if isinstance(result, dict) else result
print(f"Crawled {pages} pages to ./newshub_data")

"""
This will deeply crawl the website using Scrapy and save the content to the specified directory.
"""