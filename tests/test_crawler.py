#!/usr/bin/env python3
"""
Tests for the web crawler functionality
"""
import unittest
import os
import shutil
import tempfile
from unittest.mock import patch, MagicMock
from vibe_scraping import WebCrawler

class TestWebCrawler(unittest.TestCase):
    """Test the WebCrawler class"""
    
    def setUp(self):
        """Set up temporary directory for crawler tests"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up after tests"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('requests.Session.get')
    def test_crawler_initialization(self, mock_get):
        """Test basic crawler initialization and properties"""
        # Configure mock response for robots.txt
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "User-agent: *\nDisallow: /private/"
        mock_get.return_value = mock_response
        
        # Create crawler instance
        crawler = WebCrawler(
            start_url="https://example.com",
            max_depth=3,
            max_pages=50,
            save_path=self.temp_dir
        )
        
        # Test basic properties
        self.assertEqual(crawler.start_url, "https://example.com")
        self.assertEqual(crawler.max_depth, 3)
        self.assertEqual(crawler.max_pages, 50)
        self.assertEqual(crawler.save_path, self.temp_dir)
        self.assertEqual(crawler.base_domain, "example.com")
        self.assertEqual(crawler.base_scheme, "https")
        self.assertEqual(crawler.crawl_method, "breadth")
    
    @patch('requests.Session.get')
    def test_url_normalization(self, mock_get):
        """Test URL normalization functionality"""
        # Configure mock response for robots.txt
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "User-agent: *\nAllow: /"
        mock_get.return_value = mock_response
        
        # Create crawler instance
        crawler = WebCrawler(
            start_url="https://example.com",
            max_depth=1,
            max_pages=10,
            save_path=self.temp_dir
        )
        
        # Test various URL normalization cases
        test_cases = [
            # [input URL, parent URL, expected output]
            ["page.html", "https://example.com", "https://example.com/page.html"],
            ["/products/item", "https://example.com", "https://example.com/products/item"],
            ["https://example.com/products/", "https://example.com", "https://example.com/products"],
            ["https://example.com/page.html#section", "https://example.com", "https://example.com/page.html"],
            ["../category/item", "https://example.com/products/", "https://example.com/category/item"]
        ]
        
        for input_url, parent_url, expected in test_cases:
            normalized = crawler._normalize_url(input_url, parent_url)
            self.assertEqual(normalized, expected)
    
    @patch('requests.Session.get')
    def test_should_follow(self, mock_get):
        """Test URL follow decision logic"""
        # Configure mock response for robots.txt
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = (
            "User-agent: *\n"
            "Disallow: /private/\n"
            "Disallow: /admin/\n"
        )
        mock_get.return_value = mock_response
        
        # Create crawler instance
        crawler = WebCrawler(
            start_url="https://example.com",
            max_depth=2,
            max_pages=20,
            save_path=self.temp_dir,
            url_pattern=r"example\.com/products/.*"  # Only follow product URLs
        )
        
        # Set up crawler state
        crawler.visited.add("https://example.com/products/visited-already")
        
        # Test cases that should NOT be followed
        should_not_follow = [
            "https://example.com/products/visited-already",  # Already visited
            "https://example.com/private/secret",  # Disallowed by robots.txt
            "https://example.com/admin/login",  # Disallowed by robots.txt
            "https://example.com/about",  # Doesn't match URL pattern
            "https://othersite.com/products/item",  # Different domain
            "https://example.com/image.jpg",  # Binary file
            "https://example.com/document.pdf"  # Document file
        ]
        
        for url in should_not_follow:
            self.assertFalse(crawler._should_follow(url), f"Should not follow: {url}")
        
        # Test cases that should be followed
        should_follow = [
            "https://example.com/products/item1",
            "https://example.com/products/category/item2"
        ]
        
        for url in should_follow:
            self.assertTrue(crawler._should_follow(url), f"Should follow: {url}")
    
    @patch('requests.Session.get')
    def test_depth_check(self, mock_get):
        """Test crawl depth limiting"""
        # Configure mock responses
        def mock_response_generator(url):
            """Generate a mock response based on the URL"""
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            
            # Robots.txt
            if url.endswith("robots.txt"):
                mock_resp.text = "User-agent: *\nAllow: /"
            # Root page
            elif url == "https://example.com":
                mock_resp.text = (
                    '<html><body>'
                    '<a href="https://example.com/page1">Page 1</a>'
                    '</body></html>'
                )
            # Page 1
            elif url == "https://example.com/page1":
                mock_resp.text = (
                    '<html><body>'
                    '<a href="https://example.com/page2">Page 2</a>'
                    '</body></html>'
                )
            # Page 2
            elif url == "https://example.com/page2":
                mock_resp.text = (
                    '<html><body>'
                    '<a href="https://example.com/page3">Page 3</a>'
                    '</body></html>'
                )
            # Default
            else:
                mock_resp.text = '<html><body>Default Page</body></html>'
                
            return mock_resp
        
        # Configure the mock to use our generator
        mock_get.side_effect = mock_response_generator
        
        # Create crawler instance with depth = 1
        crawler = WebCrawler(
            start_url="https://example.com",
            max_depth=1,  # Only crawl 1 level deep
            max_pages=10,
            save_path=self.temp_dir,
            delay=0.01  # Minimal delay for tests
        )
        
        # Mock the save_page method to avoid actual file operations
        with patch.object(crawler, '_save_page') as mock_save:
            # Start crawling
            crawler.crawl()
            
            # We should have crawled at most 2 pages (start_url and page1)
            self.assertLessEqual(crawler.page_count, 2)
            
            # page2 should not be crawled due to depth limit
            self.assertNotIn("https://example.com/page2", crawler.visited)
    
    @patch('requests.Session.get')
    def test_max_pages_limit(self, mock_get):
        """Test max pages limiting"""
        # Configure mock responses
        def mock_response_generator(url):
            """Generate a mock response with many links"""
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            
            # Robots.txt
            if url.endswith("robots.txt"):
                mock_resp.text = "User-agent: *\nAllow: /"
            # All other URLs - return a page with 10 links
            else:
                links = ''.join([
                    f'<a href="https://example.com/page{i}">Page {i}</a>'
                    for i in range(1, 11)
                ])
                mock_resp.text = f'<html><body>{links}</body></html>'
                
            return mock_resp
        
        # Configure the mock to use our generator
        mock_get.side_effect = mock_response_generator
        
        # Create crawler instance with max_pages = 5
        crawler = WebCrawler(
            start_url="https://example.com",
            max_depth=3,  # Deep enough to find many pages
            max_pages=5,  # But limit to just 5 pages
            save_path=self.temp_dir,
            delay=0.01  # Minimal delay for tests
        )
        
        # Mock the save_page method to avoid actual file operations
        with patch.object(crawler, '_save_page'):
            # Start crawling
            crawler.crawl()
            
            # Verify we only crawled 5 pages
            self.assertEqual(crawler.page_count, 5)

if __name__ == "__main__":
    unittest.main() 