#!/usr/bin/env python3
"""
Complete pipeline for crawling a website and analyzing the HTML content.
This script combines functionality from basic_crawler.py and analyze_crawled_html.py.
"""

import os
from vibe_scraping.crawler import WebCrawler
from vibe_scraping.html_analyzer import HTMLAnalyzer

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

def analyze_content(crawl_dir):
    # Save analysis results inside the crawl_data directory
    analysis_output = os.path.join(crawl_dir, "analysis_results.json")
    
    print("\nAnalyzing crawled HTML content...")
    analyzer = HTMLAnalyzer(crawl_dir)
    
    # Load metadata
    analyzer.load_metadata()
    
    # Analyze all pages
    analyzer.analyze_all()
    
    # Get statistics
    stats = analyzer.get_statistics()
    
    # Save results
    analyzer.save_results(analysis_output)
    
    stats['output_file'] = analysis_output
    return stats

def main():
    # Ensure output directory exists
    crawl_data_path = "./crawl_data"
    os.makedirs(crawl_data_path, exist_ok=True)
    
    # Step 1: Crawl the website
    crawl_dir = crawl_website()
    
    # Step 2: Analyze the content
    stats = analyze_content(crawl_dir)
    
    # Step 3: Print summary
    if stats:
        print("\nAnalysis completed:")
        print(f"Total pages analyzed: {stats['total_pages_analyzed']}")
        print(f"Total words extracted: {stats['total_words']}")
        print(f"Average words per page: {stats['average_words_per_page']:.2f}")
        print(f"\nDetailed results saved to: {stats['output_file']}")

if __name__ == "__main__":
    main()
