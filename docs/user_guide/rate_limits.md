Rate Limits
Overview
Rate limiting protects our API infrastructure and ensures fair usage for all users. This document explains rate limits, how to work within them, and best practices for handling rate limit errors.
Rate Limit Tiers
By Plan
PlanRequests/MinuteRequests/HourRequests/DayBurst AllowanceFree601,00010,000100Starter30010,000100,000500Pro1,00050,000500,0002,000Enterprise5,000250,0002,500,00010,000CustomNegotiableNegotiableNegotiableNegotiable
Burst Allowance: Maximum requests in a 10-second window.
By Authentication Type
AuthenticationRate LimitNotesAPI Key (sk_*)Plan-basedFull API accessOAuth TokenPlan-basedUser-specific limitsPublic Key (pk_*)100/minuteLimited scope onlyNo Authentication10/minutePublic endpoints only
Rate Limit Headers
Every API response includes rate limit information in headers:
httpHTTP/1.1 200 OK
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1707660000
X-RateLimit-Window: 60
Headers Explained:
HeaderDescriptionExampleX-RateLimit-LimitMaximum requests per window1000X-RateLimit-RemainingRequests remaining in window995X-RateLimit-ResetUnix timestamp when limit resets1707660000X-RateLimit-WindowWindow duration in seconds60
Calculating Time Until Reset
pythonimport time

def time_until_reset(reset_timestamp):
    """Calculate seconds until rate limit resets."""
    return max(0, reset_timestamp - time.time())

# Example from response headers
reset_timestamp = 1707660000
wait_time = time_until_reset(reset_timestamp)
print(f"Rate limit resets in {wait_time:.0f} seconds")

Rate Limit Exceeded Response
When you exceed the rate limit, you'll receive a 429 Too Many Requests response:
json{
  "status": "error",
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please retry after 45 seconds.",
    "details": {
      "limit": 1000,
      "window": "minute",
      "reset_at": "2026-02-11T12:30:00Z"
    }
  }
}
Response Headers:
httpHTTP/1.1 429 Too Many Requests
Retry-After: 45
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1707660000
Endpoint-Specific Limits
Some endpoints have additional limits to prevent abuse:
Search and Query Endpoints
EndpointLimitWindowReason/v1/search1001 minuteResource-intensive/v1/analytics/usage501 minuteComplex queries/v1/batch101 minuteMultiple operations
Write Operations
EndpointLimitWindowReasonPOST /v1/users101 minutePrevent spamPOST /v1/files201 minuteUpload bandwidthDELETE /*501 minutePrevent accidental mass deletion
Webhook Management
EndpointLimitWindowReasonPOST /v1/webhooks51 hourPrevent webhook spamPOST /v1/webhooks/{id}/test101 minuteTest endpoint abuse
Best Practices
1. Implement Exponential Backoff
When you hit rate limits, retry with exponential backoff:
pythonimport time
import random

def make_request_with_backoff(func, max_retries=5):
    """Execute request with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            
            # Calculate wait time with jitter
            wait_time = min(300, (2 ** attempt) + random.uniform(0, 1))
            print(f"Rate limited. Waiting {wait_time:.1f}s before retry {attempt + 1}/{max_retries}")
            time.sleep(wait_time)

# Usage
result = make_request_with_backoff(lambda: client.users.list())
2. Monitor Rate Lim