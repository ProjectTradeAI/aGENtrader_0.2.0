"""
Test script for API error handling in CoinAPIFetcher

This script tests the enhanced error handling capabilities of the CoinAPIFetcher
class for various HTTP status codes and error conditions.
"""

import os
import time
import json
import random
import logging
import unittest
import requests
from unittest.mock import patch, MagicMock, PropertyMock

# Import modules to test - using absolute imports to avoid path manipulation
from aGENtrader_v2.data.feed.coinapi_fetcher import CoinAPIFetcher
from aGENtrader_v2.utils.error_handler import DataFetchingError, ValidationError

class MockResponse:
    """Mock HTTP response for testing"""
    
    def __init__(self, status_code, json_data=None, text="", headers=None):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text
        self.headers = headers or {}
        self.reason = self._get_reason_for_status(status_code)
        
    def json(self):
        return self._json_data
        
    def _get_reason_for_status(self, status_code):
        reasons = {
            200: "OK",
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            429: "Too Many Requests",
            500: "Internal Server Error",
            502: "Bad Gateway",
            503: "Service Unavailable",
            504: "Gateway Timeout"
        }
        return reasons.get(status_code, "Unknown")

class TestAPIErrorHandling(unittest.TestCase):
    """Test the enhanced error handling in API components"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Suppress logging during tests
        logging.disable(logging.CRITICAL)
        
        # Create a CoinAPIFetcher instance
        self.fetcher = CoinAPIFetcher()
        
        # Mock the API key to avoid actual API calls
        self.fetcher.api_key = "test_api_key"
        
        # Mock time to avoid rate limit sleeping
        self.fetcher.last_request_time = 0
        
    def tearDown(self):
        """Tear down test fixtures"""
        # Re-enable logging
        logging.disable(logging.NOTSET)
    
    @patch('requests.get')
    def test_400_bad_request(self, mock_get):
        """Test handling of 400 Bad Request errors"""
        # Mock response
        mock_response = MockResponse(
            status_code=400,
            text="Invalid symbol",
            json_data={"error": "Symbol 'invalid-symbol' is not supported"}
        )
        mock_get.return_value = mock_response
        
        # Test the error handling
        with self.assertRaises(DataFetchingError) as context:
            self.fetcher._make_request("https://rest.coinapi.io/v1/test")
            
        # Check that the error message contains the expected information
        error_msg = str(context.exception)
        self.assertIn("API Error 400", error_msg)
        self.assertIn("Bad Request", error_msg)
        self.assertIn("Error details", error_msg)
        self.assertIn("Symbol 'invalid-symbol' is not supported", error_msg)
        self.assertIn("Recommended action", error_msg)
    
    @patch('requests.get')    
    def test_401_unauthorized(self, mock_get):
        """Test handling of 401 Unauthorized errors"""
        # Mock response
        mock_response = MockResponse(
            status_code=401,
            text="Unauthorized",
            json_data={"error": "Invalid API key"}
        )
        mock_get.return_value = mock_response
        
        # Test the error handling
        with self.assertRaises(DataFetchingError) as context:
            self.fetcher._make_request("https://rest.coinapi.io/v1/test")
            
        # Check that the error message contains the expected information
        error_msg = str(context.exception)
        self.assertIn("API Error 401", error_msg)
        self.assertIn("Unauthorized", error_msg)
        self.assertIn("Authentication failed", error_msg)
        self.assertIn("Recommended action", error_msg)
        self.assertIn("Check that your API key is valid", error_msg)
    
    @patch('requests.get')
    def test_403_forbidden(self, mock_get):
        """Test handling of 403 Forbidden errors"""
        # Mock response
        mock_response = MockResponse(
            status_code=403,
            text="Forbidden",
            json_data={"error": "Your subscription plan does not support this endpoint"}
        )
        mock_get.return_value = mock_response
        
        # Test the error handling
        with self.assertRaises(DataFetchingError) as context:
            self.fetcher._make_request("https://rest.coinapi.io/v1/test")
            
        # Check that the error message contains the expected information
        error_msg = str(context.exception)
        self.assertIn("API Error 403", error_msg)
        self.assertIn("Forbidden", error_msg)
        self.assertIn("does not have permission", error_msg)
        self.assertIn("Recommended action", error_msg)
        self.assertIn("Verify your API subscription level", error_msg)
    
    @patch('requests.get')
    def test_404_not_found(self, mock_get):
        """Test handling of 404 Not Found errors"""
        # Mock response
        mock_response = MockResponse(
            status_code=404,
            text="Not Found",
            json_data={"error": "Endpoint not found"}
        )
        mock_get.return_value = mock_response
        
        # Test the error handling
        with self.assertRaises(DataFetchingError) as context:
            self.fetcher._make_request("https://rest.coinapi.io/v1/test")
            
        # Check that the error message contains the expected information
        error_msg = str(context.exception)
        self.assertIn("API Error 404", error_msg)
        self.assertIn("Not Found", error_msg)
        self.assertIn("does not exist", error_msg)
        self.assertIn("Recommended action", error_msg)
        self.assertIn("Check the API documentation", error_msg)
    
    @patch('requests.get')
    def test_429_too_many_requests(self, mock_get):
        """Test handling of 429 Too Many Requests errors"""
        # Mock response
        mock_response = MockResponse(
            status_code=429,
            text="Too Many Requests",
            json_data={"error": "Rate limit exceeded"},
            headers={"Retry-After": "30"}
        )
        mock_get.return_value = mock_response
        
        # Test the error handling
        with self.assertRaises(DataFetchingError) as context:
            self.fetcher._make_request("https://rest.coinapi.io/v1/test")
            
        # Check that the error message contains the expected information
        error_msg = str(context.exception)
        self.assertIn("API Error 429", error_msg)
        self.assertIn("Too Many Requests", error_msg)
        self.assertIn("Rate limit exceeded", error_msg)
        self.assertIn("Recommended action", error_msg)
        self.assertIn("Retry after 30 seconds", error_msg)
        
        # Check that the rate limiting was adjusted
        self.assertGreaterEqual(self.fetcher.min_request_interval, 30)
    
    @patch('requests.get')
    def test_500_internal_server_error(self, mock_get):
        """Test handling of 500 Internal Server Error"""
        # Mock response
        mock_response = MockResponse(
            status_code=500,
            text="Internal Server Error",
            json_data={"error": "Unexpected server error"}
        )
        mock_get.return_value = mock_response
        
        # Test the error handling
        with self.assertRaises(DataFetchingError) as context:
            self.fetcher._make_request("https://rest.coinapi.io/v1/test")
            
        # Check that the error message contains the expected information
        error_msg = str(context.exception)
        self.assertIn("API Error 500", error_msg)
        self.assertIn("Internal Server Error", error_msg)
        self.assertIn("unexpected error", error_msg)
        self.assertIn("Recommended action", error_msg)
        self.assertIn("Retry automatically", error_msg)
    
    @patch('requests.get')
    def test_503_service_unavailable(self, mock_get):
        """Test handling of 503 Service Unavailable with maintenance info"""
        # Mock response
        mock_response = MockResponse(
            status_code=503,
            text="Service Unavailable",
            json_data={"error": "Scheduled maintenance", "maintenance": "Maintenance until 2025-04-21T00:00:00Z"}
        )
        mock_get.return_value = mock_response
        
        # Test the error handling
        with self.assertRaises(DataFetchingError) as context:
            self.fetcher._make_request("https://rest.coinapi.io/v1/test")
            
        # Check that the error message contains the expected information
        error_msg = str(context.exception)
        self.assertIn("API Error 503", error_msg)
        self.assertIn("Service Unavailable", error_msg)
        self.assertIn("temporarily unavailable", error_msg)
        self.assertIn("Recommended action", error_msg)
        self.assertIn("Retry automatically", error_msg)
    
    @patch('requests.get')
    def test_connection_error(self, mock_get):
        """Test handling of connection errors"""
        # Mock raising a connection error
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        # Test the error handling (this will be caught by retry_with_backoff)
        with self.assertRaises(requests.exceptions.ConnectionError):
            self.fetcher._make_request("https://rest.coinapi.io/v1/test")
    
    @patch('requests.get')
    def test_timeout_error(self, mock_get):
        """Test handling of timeout errors"""
        # Mock raising a timeout error
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        # Test the error handling (this will be caught by retry_with_backoff)
        with self.assertRaises(requests.exceptions.Timeout):
            self.fetcher._make_request("https://rest.coinapi.io/v1/test")

def run_tests():
    """Run the API error handling tests"""
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

if __name__ == "__main__":
    run_tests()