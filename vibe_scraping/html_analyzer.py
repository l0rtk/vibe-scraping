"""
HTML content analyzer for vibe-scraping.
Parses the metadata.json file and extracts text from crawled HTML.
"""

import os
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
from collections import Counter
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HTMLAnalyzer:
    """Analyzer for extracting and processing text from crawled HTML files."""
    
    def __init__(self, crawl_data_path="./crawl_data"):
        """
        Initialize the analyzer.
        
        Args:
            crawl_data_path: Path to the directory containing crawled data and metadata.json
        """
        self.crawl_data_path = Path(crawl_data_path)
        self.metadata_path = self.crawl_data_path / "metadata.json"
        self.metadata = None
        self.results = {}
        
    def load_metadata(self):
        """Load the metadata.json file."""
        if not self.metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found at {self.metadata_path}")
        
        logger.info(f"Loading metadata from {self.metadata_path}")
        with open(self.metadata_path, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
        
        return self.metadata
    
    def extract_text_from_html(self, html_content):
        """
        Extract readable text from HTML content.
        
        Args:
            html_content: Raw HTML content as string
            
        Returns:
            Extracted text string with extra whitespace removed
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "noscript", "iframe", "svg"]):
            script.extract()
        
        # Extract text
        text = soup.get_text(separator=' ')
        
        # Clean up text: remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def analyze_page(self, url, hash_value):
        """
        Analyze a single page from the crawl data.
        
        Args:
            url: The URL of the page
            hash_value: The hash directory name containing the page data
            
        Returns:
            Dictionary with analysis results for the page
        """
        page_dir = self.crawl_data_path / hash_value
        html_path = page_dir / "page.html"
        page_metadata_path = page_dir / "metadata.json"
        
        if not html_path.exists():
            logger.warning(f"HTML file not found for {url} at {html_path}")
            return None
        
        # Load page metadata
        with open(page_metadata_path, 'r', encoding='utf-8') as f:
            page_metadata = json.load(f)
        
        # Load and parse HTML
        with open(html_path, 'r', encoding='utf-8', errors='replace') as f:
            html_content = f.read()
        
        # Extract text
        text = self.extract_text_from_html(html_content)
        
        # Basic analysis
        word_count = len(text.split())
        char_count = len(text)
        
        # Create simple result
        result = {
            "url": url,
            "text_length": len(text),
            "word_count": word_count,
            "char_count": char_count,
            "crawl_depth": page_metadata.get("depth", 0),
            "extracted_text": text[:1000] + "..." if len(text) > 1000 else text  # Truncate for preview
        }
        
        return result
    
    def analyze_all(self):
        """
        Analyze all pages in the crawl data.
        
        Returns:
            Dictionary with analysis results for all pages
        """
        if not self.metadata:
            self.load_metadata()
        
        results = {}
        crawled_urls = self.metadata.get("crawled_urls", {})
        total_urls = len(crawled_urls)
        
        logger.info(f"Starting analysis of {total_urls} URLs")
        
        for i, (url, data) in enumerate(crawled_urls.items()):
            if i % 10 == 0:
                logger.info(f"Processing URL {i+1}/{total_urls}")
            
            hash_value = data.get("hash")
            if not hash_value:
                logger.warning(f"No hash found for URL: {url}")
                continue
            
            result = self.analyze_page(url, hash_value)
            if result:
                results[url] = result
        
        self.results = results
        return results
    
    def get_statistics(self):
        """
        Generate overall statistics from the analysis results.
        
        Returns:
            Dictionary with overall statistics
        """
        if not self.results:
            logger.warning("No analysis results available. Run analyze_all() first.")
            return {}
        
        total_pages = len(self.results)
        total_words = sum(result["word_count"] for result in self.results.values())
        total_chars = sum(result["char_count"] for result in self.results.values())
        avg_words_per_page = total_words / total_pages if total_pages > 0 else 0
        
        # Get depth distribution
        depths = [result["crawl_depth"] for result in self.results.values()]
        depth_counter = Counter(depths)
        
        stats = {
            "total_pages_analyzed": total_pages,
            "total_words": total_words,
            "total_characters": total_chars,
            "average_words_per_page": avg_words_per_page,
            "depth_distribution": depth_counter,
            "crawl_date": self.metadata.get("last_crawl", "Unknown")
        }
        
        return stats
    
    def save_results(self, output_path="./analysis_results.json"):
        """
        Save analysis results to a JSON file.
        
        Args:
            output_path: Path to save the results
        """
        if not self.results:
            logger.warning("No analysis results available. Run analyze_all() first.")
            return
        
        output = {
            "statistics": self.get_statistics(),
            "page_results": self.results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Analysis results saved to {output_path}")

def analyze_html_content(crawl_data_path="./crawl_data", output_path="./analysis_results.json"):
    """
    Convenience function to analyze crawled data.
    
    Args:
        crawl_data_path: Path to the crawled data directory
        output_path: Path to save the analysis results
        
    Returns:
        Dictionary with analysis statistics
    """
    analyzer = HTMLAnalyzer(crawl_data_path)
    analyzer.load_metadata()
    analyzer.analyze_all()
    stats = analyzer.get_statistics()
    analyzer.save_results(output_path)
    
    return stats

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze crawled HTML content")
    parser.add_argument("--input", default="./crawl_data", help="Path to crawled data directory")
    parser.add_argument("--output", default="./analysis_results.json", help="Path to save analysis results")
    
    args = parser.parse_args()
    
    stats = analyze_html_content(args.input, args.output)
    
    # Print some basic stats
    print("\nAnalysis completed:")
    print(f"Total pages analyzed: {stats['total_pages_analyzed']}")
    print(f"Total words extracted: {stats['total_words']}")
    print(f"Average words per page: {stats['average_words_per_page']:.2f}")
    print(f"Results saved to: {args.output}") 