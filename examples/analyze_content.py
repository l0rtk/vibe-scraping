#!/usr/bin/env python
"""
Example of how to use the vibe-scraping content analyzer.
This script extracts text from crawled HTML files.
"""

from vibe_scraping.analyzer import ContentAnalyzer, analyze_crawl_data

# Option 1: Simple approach using the convenience function
print("Running basic analysis...")
stats = analyze_crawl_data(
    crawl_data_path="./crawl_data",
    output_path="./analysis_results.json"
)

print(f"\nBasic analysis completed:")
print(f"Total pages analyzed: {stats['total_pages_analyzed']}")
print(f"Total words extracted: {stats['total_words']}")
print(f"Average words per page: {stats['average_words_per_page']:.2f}")

# Option 2: More advanced usage with the ContentAnalyzer class
print("\nRunning detailed analysis...")
analyzer = ContentAnalyzer("./crawl_data")
analyzer.load_metadata()

# Analyze all pages
results = analyzer.analyze_all()

# Get overall statistics
statistics = analyzer.get_statistics()
print(f"Pages analyzed: {statistics['total_pages_analyzed']}")
print(f"Content crawled on: {statistics['crawl_date']}")

# Print depth distribution
print("\nPages by crawl depth:")
for depth, count in sorted(statistics['depth_distribution'].items()):
    print(f"  Depth {depth}: {count} pages")

# Print some sample text from the first few results (if available)
print("\nSample extracted text from first page:")
if results:
    first_url = list(results.keys())[0]
    first_result = results[first_url]
    preview_text = first_result["extracted_text"]
    
    # Keep the preview reasonably short
    if len(preview_text) > 300:
        preview_text = preview_text[:300] + "..."
    
    print(f"URL: {first_url}")
    print(f"Word count: {first_result['word_count']}")
    print(f"Text preview: {preview_text}")

# Save detailed results to a different file
analyzer.save_results("./detailed_analysis.json")
print("\nDetailed analysis saved to ./detailed_analysis.json")

"""
This example demonstrates two ways to use the content analyzer:
1. Simple approach with the convenience function
2. More advanced usage with direct access to the ContentAnalyzer class

The analyzer extracts text from HTML files, computes basic statistics,
and saves the results to a JSON file.
""" 