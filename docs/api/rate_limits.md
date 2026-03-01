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