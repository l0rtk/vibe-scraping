#!/usr/bin/env python3
"""
Simple pipeline for crawling a website and processing the HTML content.
"""

from vibe_scraping.crawler import WebCrawler
from vibe_scraping.html_processor import process_html_content

# Define a custom processor function - must include all four parameters
def extract_key_info(url, html_content, soup, metadata):
    """Extract just the essential information from a page"""
    return {
        "url": url,
        "title": soup.title.text if soup.title else "No title",
        "word_count": len(html_content.split()),
        "link_count": len(soup.find_all('a', href=True))
    }

# Step 1: Set up and run crawler
crawler = WebCrawler(
    start_url="https://newshub.ge",
    max_depth=2,
    max_pages=20,
    respect_robots_txt=False,
    save_path="./crawl_data"
)
result = crawler.crawl()
print(f"Crawled {result.get('pages_crawled', 0)} pages to ./crawl_data")

# Step 2: Process the content with custom processor
stats = process_html_content(
    crawl_data_path="./crawl_data",
    output_path="./crawl_data/process_results.json",
    processor_func=extract_key_info
)

# Step 3: Display results
print("\nProcessing complete!")
if stats and 'total_pages_processed' in stats:
    print(f"Processed {stats['total_pages_processed']} pages")
else:
    print("No pages were processed")
print(f"Results saved to: ./crawl_data/process_results.json")
