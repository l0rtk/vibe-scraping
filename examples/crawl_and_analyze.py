#!/usr/bin/env python3
"""
Complete pipeline for crawling a website and processing the HTML content.
This script combines functionality from basic_crawler.py and html_processor.py.
"""

import os
from vibe_scraping.crawler import WebCrawler
from vibe_scraping.html_processor import HTMLProcessor

def crawl_website():
    # Configuration parameters
    url = "https://newshub.ge"
    max_depth = 2
    max_pages = 20
    respect_robots = False
    crawl_data_path = "./crawl_data"
    
    print(f"Starting to crawl {url}...")
    crawler = WebCrawler(
        start_url=url,
        max_depth=max_depth,
        max_pages=max_pages,
        respect_robots_txt=respect_robots,
        save_path=crawl_data_path
    )
    
    result = crawler.crawl()
    pages = result.get('pages_crawled', 0) if isinstance(result, dict) else result
    print(f"Crawled {pages} pages to {crawl_data_path}")
    return crawl_data_path

def custom_processor(url, html_content, soup, metadata):
    """
    Custom HTML processor that extracts specific information.
    This is an example that can be replaced with any custom processing logic.
    
    Args:
        url: The URL of the page
        html_content: Raw HTML content
        soup: BeautifulSoup object of the page
        metadata: Page metadata
        
    Returns:
        Dictionary with processing results
    """
    # Get page title
    title = soup.title.text if soup.title else "No title"
    
    # Extract text from paragraphs using soup
    paragraphs_text = ' '.join([p.get_text() for p in soup.find_all('p')])
    
    # Also measure the total HTML content length
    html_length = len(html_content)
    
    # Count words in paragraph text
    word_count = len(paragraphs_text.split())
    
    # Count links
    links = [a['href'] for a in soup.find_all('a', href=True)]
    
    # Get headings
    headings = []
    for tag in ['h1', 'h2', 'h3']:
        for heading in soup.find_all(tag):
            headings.append({
                'level': tag,
                'text': heading.get_text().strip()
            })
    
    return {
        "url": url,
        "title": title,
        "html_size_bytes": html_length,
        "word_count": word_count,
        "link_count": len(links),
        "headings_count": len(headings),
        "headings": headings[:5],  # Just show first 5 headings
        "crawl_depth": metadata.get("depth", 0)
    }

def process_content(crawl_dir):
    # Save processing results inside the crawl_data directory
    process_output = os.path.join(crawl_dir, "process_results.json")
    
    print("\nProcessing crawled HTML content...")
    processor = HTMLProcessor(crawl_dir)
    
    # Load metadata
    processor.load_metadata()
    
    # Apply custom processor to all pages
    processor.apply_custom_processor(custom_processor)
    
    # Get statistics
    stats = processor.get_statistics()
    
    # Save results
    processor.save_results(process_output)
    
    stats['output_file'] = process_output
    return stats

def main():
    # Ensure output directory exists
    crawl_data_path = "./crawl_data"
    os.makedirs(crawl_data_path, exist_ok=True)
    
    # Step 1: Crawl the website
    crawl_dir = crawl_website()
    
    # Step 2: Process the content
    stats = process_content(crawl_dir)
    
    # Step 3: Print summary
    if stats:
        print("\nProcessing completed:")
        print(f"Total pages processed: {stats['total_pages_processed']}")
        if 'total_words' in stats:
            print(f"Total words extracted: {stats['total_words']}")
            print(f"Average words per page: {stats['average_words_per_page']:.2f}")
        print(f"\nDetailed results saved to: {stats['output_file']}")

if __name__ == "__main__":
    main()
