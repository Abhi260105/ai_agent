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
2. Monitor Rate Limit Headers
Check remaining requests before making calls:
pythonclass RateLimitAwareClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.remaining = None
        self.reset_at = None
    
    def request(self, endpoint, **kwargs):
        # Check if we should wait
        if self.remaining is not None and self.remaining < 10:
            if self.reset_at:
                wait_time = self.reset_at - time.time()
                if wait_time > 0:
                    print(f"Approaching rate limit. Waiting {wait_time:.0f}s")
                    time.sleep(wait_time)
        
        # Make request
        response = requests.get(endpoint, **kwargs)
        
        # Update rate limit state
        self.remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
        self.reset_at = int(response.headers.get('X-RateLimit-Reset', 0))
        
        return response

        3. Use Caching
Cache responses to reduce API calls:
pythonfrom functools import lru_cache
import time

@lru_cache(maxsize=128)
def get_user_cached(user_id, cache_key):
    """Cached user lookup. Cache key changes every 5 minutes."""
    return client.users.get(user_id)

# Use cache key that changes every 5 minutes
cache_key = int(time.time()) // 300
user = get_user_cached('usr_123', cache_key)
4. Batch Operations
Use batch endpoints to reduce request count:
python# ❌ Don't: Multiple individual requests
for user_data in users_to_create:
    client.users.create(user_data)  # 100 requests

# ✅ Do: Single batch request
client.batch.execute([
    {'method': 'POST', 'path': '/users', 'body': user_data}
    for user_data in users_to_create
])  # 1 request
5. Implement Request Queuing
Queue requests to stay within limits:
pythonimport queue
import threading
import time

class RateLimitedQueue:
    def __init__(self, requests_per_minute=60):
        self.queue = queue.Queue()
        self.requests_per_minute = requests_per_minute
        self.min_interval = 60 / requests_per_minute
        self.last_request_time = 0
        self.running = False
    
    def start(self):
        """Start processing queue."""
        self.running = True
        thread = threading.Thread(target=self._process_queue)
        thread.daemon = True
        thread.start()
    
    def _process_queue(self):
        """Process queued requests."""
        while self.running:
            try:
                func, args, kwargs = self.queue.get(timeout=1)
                
                # Wait if needed to respect rate limit
                elapsed = time.time() - self.last_request_time
                if elapsed < self.min_interval:
                    time.sleep(self.min_interval - elapsed)
                
                # Execute request
                func(*args, **kwargs)
                self.last_request_time = time.time()
                
                self.queue.task_done()
            except queue.Empty:
                continue
    
    def add(self, func, *args, **kwargs):
        """Add request to queue."""
        self.queue.put((func, args, kwargs))
    
    def wait_completion(self):
        """Wait for all queued requests to complete."""
        self.queue.join()

# Usage
queue = RateLimitedQueue(requests_per_minute=60)
queue.start()

# Add requests to queue
for user_id in user_ids:
    queue.add(client.users.get, user_id)

# Wait for completion
queue.wait_completion()