#!/usr/bin/env python3
"""
Example script showing how to use the HTMLAnalyzer to extract text from crawled pages.
"""

from vibe_scraping.html_analyzer import HTMLAnalyzer, analyze_html_content

def main():
    print("Running HTML analysis with the convenience function...")
    # Method 1: Use the convenience function
    stats = analyze_html_content(
        crawl_data_path="./crawl_data",
        output_path="./html_analysis_results.json"
    )
    
    print(f"\nAnalysis completed:")
    print(f"Total pages analyzed: {stats['total_pages_analyzed']}")
    print(f"Total words extracted: {stats['total_words']}")
    print(f"Average words per page: {stats['average_words_per_page']:.2f}")
    
    # Method 2: Use the HTMLAnalyzer class directly for more control
    print("\nRunning HTML analysis with the HTMLAnalyzer class...")
    analyzer = HTMLAnalyzer("./crawl_data")
    
    # Load metadata
    metadata = analyzer.load_metadata()
    print(f"Loaded metadata with {len(metadata.get('crawled_urls', {}))} URLs")
    
    # Get just the first 3 URLs to demonstrate focused analysis
    urls = list(metadata.get('crawled_urls', {}).keys())[:3]
    
    # Process each URL individually
    for url in urls:
        hash_value = metadata['crawled_urls'][url]['hash']
        result = analyzer.analyze_page(url, hash_value)
        
        if result:
            print(f"\nURL: {url}")
            print(f"Word count: {result['word_count']}")
            
            # Print a short preview
            text = result['extracted_text']
            preview = text[:150] + "..." if len(text) > 150 else text
            print(f"Text preview: {preview}")

if __name__ == "__main__":
    main() 