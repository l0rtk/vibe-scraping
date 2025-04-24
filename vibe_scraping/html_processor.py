"""
HTML content processor for vibe-scraping.
Parses the metadata.json file and extracts text from crawled HTML.
"""

import os
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
from collections import Counter
import logging
from typing import Callable, Dict, List, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HTMLProcessor:
    """Processor for extracting and processing text from crawled HTML files."""
    
    def __init__(self, crawl_data_path="./data/crawl_data"):
        """
        Initialize the processor.
        
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
    
    def get_page_content(self, url, hash_value):
        """
        Get raw HTML content and metadata for a page.
        
        Args:
            url: The URL of the page
            hash_value: The hash directory name containing the page data
            
        Returns:
            Dictionary with page content and metadata
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
        
        # Load HTML
        with open(html_path, 'r', encoding='utf-8', errors='replace') as f:
            html_content = f.read()
        
        return {
            "url": url,
            "html_content": html_content,
            "metadata": page_metadata,
            "soup": BeautifulSoup(html_content, 'html.parser')
        }
    
    def process_page(self, url, hash_value):
        """
        Process a single page from the crawl data using the default processor.
        
        Args:
            url: The URL of the page
            hash_value: The hash directory name containing the page data
            
        Returns:
            Dictionary with processing results for the page
        """
        page_data = self.get_page_content(url, hash_value)
        if not page_data:
            return None
        
        # Extract text
        text = self.extract_text_from_html(page_data["html_content"])
        
        # Basic processing
        word_count = len(text.split())
        char_count = len(text)
        
        # Create simple result
        result = {
            "url": url,
            "text_length": len(text),
            "word_count": word_count,
            "char_count": char_count,
            "crawl_depth": page_data["metadata"].get("depth", 0),
            "extracted_text": text
        }
        
        return result
    
    def apply_custom_processor(self, processor_func: Callable, urls: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Apply a custom processor function to selected URLs or all URLs.
        
        Args:
            processor_func: A function that takes (url, html_content, soup, metadata) and returns a result
            urls: List of URLs to process (if None, processes all URLs)
            
        Returns:
            Dictionary mapping URLs to their processing results
        """
        if not self.metadata:
            self.load_metadata()
        
        crawled_urls = self.metadata.get("crawled_urls", {})
        if urls is None:
            urls_to_process = list(crawled_urls.keys())
        else:
            # Filter to only include URLs that exist in our crawled data
            urls_to_process = [url for url in urls if url in crawled_urls]
        
        total_urls = len(urls_to_process)
        logger.info(f"Starting custom processing of {total_urls} URLs")
        
        results = {}
        for i, url in enumerate(urls_to_process):
            if i % 10 == 0:
                logger.info(f"Processing URL {i+1}/{total_urls}")
            
            hash_value = crawled_urls[url].get("hash")
            if not hash_value:
                logger.warning(f"No hash found for URL: {url}")
                continue
            
            page_data = self.get_page_content(url, hash_value)
            if not page_data:
                continue
            
            try:
                # Apply the custom processor function
                result = processor_func(
                    url=url,
                    html_content=page_data["html_content"],
                    soup=page_data["soup"],
                    metadata=page_data["metadata"]
                )
                results[url] = result
            except Exception as e:
                logger.error(f"Error processing URL {url}: {str(e)}")
                continue
        
        self.results = results
        return results
    
    def get_statistics(self):
        """
        Generate overall statistics from the processing results.
        
        Returns:
            Dictionary with overall statistics
        """
        if not self.results:
            logger.warning("No processing results available. Run custom processing first.")
            return {}
        
        # Default statistics if results have standard fields
        stats = {
            "total_pages_processed": len(self.results),
            "crawl_date": self.metadata.get("last_crawl", "Unknown") if self.metadata else "Unknown"
        }
        
        # Try to extract common fields if they exist in results
        if all("word_count" in result for result in self.results.values()):
            total_words = sum(result["word_count"] for result in self.results.values())
            stats["total_words"] = total_words
            stats["average_words_per_page"] = total_words / len(self.results) if self.results else 0
            
        if all("char_count" in result for result in self.results.values()):
            stats["total_characters"] = sum(result["char_count"] for result in self.results.values())
            
        if all("crawl_depth" in result for result in self.results.values()):
            depths = [result["crawl_depth"] for result in self.results.values()]
            stats["depth_distribution"] = Counter(depths)
        
        return stats
    
    def save_results(self, output_path="./process_results.json"):
        """
        Save processing results to a JSON file.
        
        Args:
            output_path: Path to save the results
        """
        if not self.results:
            logger.warning("No processing results available. Apply custom processing first.")
            return
        
        output = {
            "statistics": self.get_statistics(),
            "page_results": self.results
        }
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Processing results saved to {output_path}")

def process_html_content(crawl_data_path="./data/crawl_data", 
                         output_path="./data/process/process_results.json",
                         processor_func=None):
    """
    Convenience function to process crawled data.
    
    Args:
        crawl_data_path: Path to the crawled data directory
        output_path: Path to save the processing results
        processor_func: Custom processor function (if None, uses default processor)
        
    Returns:
        Dictionary with processing statistics
    """
    processor = HTMLProcessor(crawl_data_path)
    processor.load_metadata()
    
    if processor_func:
        # Apply custom processor
        processor.apply_custom_processor(processor_func)
    else:
        # Use default processor
        metadata = processor.metadata
        crawled_urls = metadata.get("crawled_urls", {})
        
        results = {}
        for url, data in crawled_urls.items():
            hash_value = data.get("hash")
            if not hash_value:
                continue
                
            result = processor.process_page(url, hash_value)
            if result:
                results[url] = result
        
        processor.results = results
    
    stats = processor.get_statistics()
    processor.save_results(output_path)
    
    return stats

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Process crawled HTML content")
    parser.add_argument("--input", default="./data/crawl_data", help="Path to crawled data directory")
    parser.add_argument("--output", default="./data/process/process_results.json", help="Path to save processing results")
    
    args = parser.parse_args()
    
    # Example of using the default processor
    stats = process_html_content(args.input, args.output)
    
    # Print some basic stats
    print("\nProcessing completed:")
    print(f"Total pages processed: {stats['total_pages_processed']}")
    if 'total_words' in stats:
        print(f"Total words extracted: {stats['total_words']}")
        print(f"Average words per page: {stats['average_words_per_page']:.2f}")
    print(f"Results saved to: {args.output}") 