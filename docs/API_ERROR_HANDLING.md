# API Error Handling in aGENtrader v2

This document outlines the standardized approach to handling API errors in the aGENtrader v2 system, specifically focusing on HTTP response codes and their appropriate handling strategies.

## HTTP Response Code Handling

### 400 - Bad Request

**Description:**  
The server could not understand the request due to invalid syntax or parameters.

**Handling Strategy:**
- Log error with specific request details
- Do not retry (client error that needs to be fixed)
- Include specifically which parameters were invalid when available
- Provide clear recommendations for fixing the request

**Example Error Message:**
```
API Error 400: Bad Request. The provided symbol 'BTC-USD' is invalid. 
Recommended action: Check your symbol format. Supported formats include 'BTC/USD' or 'BTC_USD'.
```

### 401 - Unauthorized

**Description:**  
Authentication credentials are missing or invalid.

**Handling Strategy:**
- Log error with authentication details (not the actual API key)
- Do not retry (authentication needs to be fixed)
- Check if API key is present, valid, and not expired
- Provide instructions for obtaining/updating the key

**Example Error Message:**
```
API Error 401: Unauthorized. Authentication failed with the provided API key. 
Recommended action: Check that your API key is valid and not expired. You may need to regenerate your key.
```

### 403 - Forbidden

**Description:**  
The server understood the request but refuses to authorize it due to permissions issues.

**Handling Strategy:**
- Log error with endpoint and request type
- Do not retry (permissions need to be updated)
- Identify if the issue is related to rate limits, subscription tier, or specific endpoint restrictions
- Suggest appropriate subscription tier upgrades if relevant

**Example Error Message:**
```
API Error 403: Forbidden. Your current plan does not allow access to historical OHLCV data. 
Recommended action: Upgrade your API subscription to a plan that includes historical data access.
```

### 404 - Not Found

**Description:**  
The requested resource could not be found.

**Handling Strategy:**
- Log error with the specific resource that was requested
- Do not retry (resource needs to be corrected)
- Suggest checking the endpoint URL and parameters
- Verify if the resource might be available at a different location

**Example Error Message:**
```
API Error 404: Not Found. The requested endpoint '/v1/historical-data' does not exist. 
Recommended action: Check the API documentation for the correct endpoint URL.
```

### 429 - Too Many Requests

**Description:**  
The user has sent too many requests in a given amount of time ("rate limiting").

**Handling Strategy:**
- Log warning with rate limit details and retry information
- Automatically retry after appropriate wait time
- Extract Retry-After header if available to determine wait time
- Implement exponential backoff for repeated rate limiting
- Adjust request rate dynamically based on rate limit responses

**Example Error Message:**
```
API Error 429: Too Many Requests. Rate limit exceeded. 
Recommended action: Retry after 60 seconds. Consider reducing request frequency.
```

### 500 - Internal Server Error

**Description:**  
The server encountered an unexpected condition that prevented it from fulfilling the request.

**Handling Strategy:**
- Log error with request details
- Retry with backoff strategy (server errors are often temporary)
- After multiple retries, suggest trying again later
- Document as an external issue beyond client control

**Example Error Message:**
```
API Error 500: Internal Server Error. The server encountered an unexpected error. 
Recommended action: Retry the request after a brief delay. If the error persists, the API service may be experiencing issues.
```

### 502 - Bad Gateway

**Description:**  
The server received an invalid response from an upstream server.

**Handling Strategy:**
- Log error with request details
- Retry with backoff strategy
- After multiple retries, suggest checking API status page for outages

**Example Error Message:**
```
API Error 502: Bad Gateway. The API server is currently experiencing issues with its upstream systems. 
Recommended action: Retry automatically in 30 seconds. Check the CoinAPI status page for system outages.
```

### 503 - Service Unavailable

**Description:**  
The server is not ready to handle the request, often due to maintenance or overloading.

**Handling Strategy:**
- Log error with request details and any maintenance information
- Retry with backoff strategy (potentially with longer delays)
- Check for maintenance schedules in error response
- After multiple retries, suggest checking API status

**Example Error Message:**
```
API Error 503: Service Unavailable. The API is currently undergoing scheduled maintenance. 
Recommended action: Retry automatically in 5 minutes. Maintenance is scheduled to complete at 2025-04-20T18:00:00Z.
```

### 504 - Gateway Timeout

**Description:**  
The server did not receive a timely response from an upstream server.

**Handling Strategy:**
- Log error with request details
- Retry with backoff strategy
- After multiple retries, suggest using endpoints with less processing requirements

**Example Error Message:**
```
API Error 504: Gateway Timeout. The API request timed out waiting for a response. 
Recommended action: Retry with a simpler request. Consider requesting less data in a single call.
```

## Network Error Handling

### ConnectionError

**Description:**  
Failed to establish a connection to the API server.

**Handling Strategy:**
- Log warning with connection details
- Retry with backoff strategy
- Check network connectivity
- After multiple retries, suggest checking if API is accessible from current network

**Example Error Message:**
```
Network Error: Connection refused. Could not connect to api.coinapi.io. 
Recommended action: Checking network connectivity and DNS resolution.
```

### Timeout

**Description:**  
The request took too long to complete.

**Handling Strategy:**
- Log warning with request details and timeout duration
- Retry with backoff strategy
- Consider increasing timeout for future requests
- After multiple retries, suggest simplifying request

**Example Error Message:**
```
Network Error: Request timed out after 30 seconds. 
Recommended action: Consider simplifying the request by requesting less data.
```

## Implementation Details

### Retry Strategy

The system uses an exponential backoff strategy for retrying recoverable errors:

1. Initial retry after `backoff_seconds` (default: 2 seconds)
2. Second retry after `backoff_seconds * 2^1` (4 seconds)
3. Third retry after `backoff_seconds * 2^2` (8 seconds)
4. And so on, up to the maximum retry count

For rate limiting (429 errors), the system will use the Retry-After header value if provided.

### Error Logging

All API errors are logged with:
- Timestamp
- HTTP status code
- Error message from API
- Request details (URL, parameters)
- Recommended action

For security reasons, API keys and authentication tokens are never logged in full.

### Error Recovery

The system can be configured to use different recovery strategies:
- Stop processing on critical errors (default for authentication errors)
- Retry with backoff (default for network and server errors)
- Fall back to alternative data sources (when configured)

### API Key Management

The system checks for API keys in multiple locations:
1. Environment variables (e.g., `COINAPI_KEY`)
2. Configuration files
3. Secrets file (config/secrets.yaml)

When a key is missing or invalid, the system provides clear instructions for obtaining and configuring the correct API key.