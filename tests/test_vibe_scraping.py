#!/usr/bin/env python3
"""
Basic tests for the vibe-scraping package
"""
import unittest
from unittest.mock import patch, MagicMock
from vibe_scraping import scrape_webpage, calculate_cost, MODEL_PRICING

class TestScrapingFunctions(unittest.TestCase):
    """Test basic functionality of the scraping package"""
    
    def test_model_pricing_structure(self):
        """Test that the MODEL_PRICING dictionary has the expected structure"""
        # Check if MODEL_PRICING is a dict
        self.assertIsInstance(MODEL_PRICING, dict)
        
        # Check at least one model exists
        self.assertGreater(len(MODEL_PRICING), 0)
        
        # Check model pricing structure
        for model, pricing in MODEL_PRICING.items():
            self.assertIsInstance(model, str)
            self.assertIsInstance(pricing, dict)
            self.assertIn('input', pricing)
            self.assertIn('output', pricing)
            self.assertIsInstance(pricing['input'], (int, float))
            self.assertIsInstance(pricing['output'], (int, float))
    
    @patch('requests.get')
    def test_scrape_webpage_basic(self, mock_get):
        """Test the basic functionality of scrape_webpage with mocked requests"""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><h1>Test Product</h1><p>Test Description</p></body></html>"
        mock_get.return_value = mock_response
        
        # Call the function
        result = scrape_webpage("https://example.com/test", use_selenium_fallback=False)
        
        # Verify results
        self.assertIsNotNone(result)
        self.assertIn("Test Product", result)
        self.assertIn("Test Description", result)
        
        # Verify the function called requests.get with expected parameters
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], "https://example.com/test")
        self.assertIn("headers", kwargs)
    
    def test_calculate_cost(self):
        """Test that calculate_cost returns the correct cost values"""
        # Test usage data
        usage = {
            "input_tokens": 1000,
            "output_tokens": 500,
            "total_tokens": 1500
        }
        
        # Test with a model that exists
        for model in MODEL_PRICING:
            result = calculate_cost(usage, model)
            
            # Check result structure
            self.assertIsInstance(result, dict)
            self.assertIn("has_pricing", result)
            self.assertTrue(result["has_pricing"])
            self.assertIn("input_cost", result)
            self.assertIn("output_cost", result)
            self.assertIn("total_cost", result)
            
            # Check cost calculation
            input_cost = (usage["input_tokens"] / 1_000_000) * MODEL_PRICING[model]["input"]
            output_cost = (usage["output_tokens"] / 1_000_000) * MODEL_PRICING[model]["output"]
            total_cost = input_cost + output_cost
            
            self.assertAlmostEqual(result["input_cost"], input_cost)
            self.assertAlmostEqual(result["output_cost"], output_cost)
            self.assertAlmostEqual(result["total_cost"], total_cost)
        
        # Test with a model that doesn't exist
        result = calculate_cost(usage, "nonexistent-model")
        self.assertIsInstance(result, dict)
        self.assertIn("has_pricing", result)
        self.assertFalse(result["has_pricing"])

if __name__ == "__main__":
    unittest.main() 