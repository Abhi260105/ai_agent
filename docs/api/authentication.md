Authentication
Overview
Our API uses multiple authentication methods to ensure secure access to resources. Choose the method that best fits your use case.
Authentication Methods
1. API Keys (Recommended for Server-to-Server)
API keys provide simple authentication for server-side applications.
Obtaining API Keys

Log in to your dashboard
Navigate to Settings > API Keys
Click "Create API Key"
Name your key and set permissions
Copy and securely store the key (shown only once)

Using API Keys
Include the API key in the Authorization header:
httpGET /v1/users HTTP/1.1
Host: api.example.com
Authorization: Bearer sk_live_abc123xyz789
Example (cURL):
bashcurl https://api.example.com/v1/users \
  -H "Authorization: Bearer sk_live_abc123xyz789"
Example (Python):
pythonimport requests

headers = {
    'Authorization': 'Bearer sk_live_abc123xyz789'
}

response = requests.get(
    'https://api.example.com/v1/users',
    headers=headers
)
Example (JavaScript):
javascriptconst response = await fetch('https://api.example.com/v1/users', {
  headers: {
    'Authorization': 'Bearer sk_live_abc123xyz789'
  }
});
API Key Types
PrefixEnvironmentUse Casesk_live_ProductionLive data and transactionssk_test_SandboxTesting and developmentpk_live_ProductionClient-side (limited scope)pk_test_SandboxClient-side testing
Important:

sk_ keys are secret keys - never expose in client-side code
pk_ keys are publishable - safe for browser/mobile apps (limited permissions)

2. OAuth 2.0 (Recommended for User Applications)
OAuth 2.0 enables users to grant your application access to their data without sharing passwords.
Supported Flows
Authorization Code Flow (Web Applications)
Step 1: Authorization Request
Redirect users to:
https://api.example.com/oauth/authorize?
  response_type=code&
  client_id=YOUR_CLIENT_ID&
  redirect_uri=https://yourapp.com/callback&
  scope=users:read users:write&
  state=random_string
Parameters:

response_type: Must be code
client_id: Your OAuth application ID
redirect_uri: URL to redirect after authorization
scope: Space-separated list of permissions
state: Random string for CSRF protection
Step 2: User Authorization
User logs in and approves your application's access request.
Step 3: Authorization Code
User is redirected to your redirect_uri:
https://yourapp.com/callback?code=AUTH_CODE&state=random_string
Step 4: Exchange Code for Token
httpPOST /oauth/token HTTP/1.1
Host: api.example.com
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=AUTH_CODE&
client_id=YOUR_CLIENT_ID&
client_secret=YOUR_CLIENT_SECRET&
redirect_uri=https://yourapp.com/callback
Response:
json{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "scope": "users:read users:write"
}
Step 5: Use Access Token
httpGET /v1/users/me HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Client Credentials Flow (Machine-to-Machine)
For server-side applications without user interaction:
httpPOST /oauth/token HTTP/1.1
Host: api.example.com
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&
client_id=YOUR_CLIENT_ID&
client_secret=YOUR_CLIENT_SECRET&
scope=api:access
Response:
json{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600
}
Refresh Token Flow
When access token expires, use refresh token:
httpPOST /oauth/token HTTP/1.1
Host: api.example.com
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token&
refresh_token=REFRESH_TOKEN&
client_id=YOUR_CLIENT_ID&
client_secret=YOUR_CLIENT_SECRET
Response:
json{
  "access_token": "NEW_ACCESS_TOKEN",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "NEW_REFRESH_TOKEN"
}
OAuth Scopes
ScopeDescriptionusers:readRead user informationusers:writeCreate and update usersusers:deleteDelete userspayments:readRead payment informationpayments:writeProcess paymentsadmin:readRead admin dataadmin:writePerform admin actions
Requesting Multiple Scopes:
scope=users:read users:write payments:read
3. JWT (JSON Web Tokens)
For custom authentication systems, use JWT tokens.
Token Structure
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
Components:

Header: Algorithm and token type
Payload: Claims (user data)
Signature: Verification signature

Creating JWT Tokens
Python Example:
pythonimport jwt
import datetime

payload = {
    'sub': 'user_123',  # Subject (user ID)
    'name': 'John Doe',
    'iat': datetime.datetime.utcnow(),  # Issued at
    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Expires
}

token = jwt.encode(payload, 'your-secret-key', algorithm='HS256')
Node.js Example:
javascriptconst jwt = require('jsonwebtoken');

const payload = {
  sub: 'user_123',
  name: 'John Doe',
  iat: Math.floor(Date.now() / 1000),
  exp: Math.floor(Date.now() / 1000) + (60 * 60)
};

const token = jwt.sign(payload, 'your-secret-key');
Using JWT Tokens
httpGET /v1/users/me HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
4. Basic Authentication (Legacy)
Not recommended for production. Use for testing only.
httpGET /v1/users HTTP/1.1
Host: api.example.com
Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=
The value after Basic is base64-encoded username:password.
Example (cURL):
bashcurl https://api.example.com/v1/users \
  -u username:password
Token Management
Token Expiration
Token TypeLifetimeRenewableAPI KeyNo expirationNoOAuth Access Token1 hourYes (via refresh)OAuth Refresh Token30 daysYesJWTConfigurableNo (issue new)
Revoking Tokens
Revoke API Key
httpDELETE /v1/api-keys/{key_id} HTTP/1.1
Host: api.example.com
Authorization: Bearer ADMIN_API_KEY
Revoke OAuth Token
httpPOST /oauth/revoke HTTP/1.1
Host: api.example.com
Content-Type: application/x-www-form-urlencoded

token=ACCESS_TOKEN&
token_type_hint=access_token&
client_id=YOUR_CLIENT_ID&
client_secret=YOUR_CLIENT_SECRET
Rotating API Keys
Best practice: Rotate keys every 90 days
python# 1. Create new API key
new_key = client.api_keys.create(name="Production Key v2")

# 2. Update your application to use new key
update_env_variable('API_KEY', new_key.key)

# 3. Monitor for 24 hours

# 4. Delete old key
client.api_keys.delete(old_key_id)
Security Best Practices
1. Store Credentials Securely
❌ Don't:
python# Hard-coded credentials
api_key = "sk_live_abc123xyz789"
✅ Do:
python# Use environment variables
import os
api_key = os.environ.get('API_KEY')
✅ Do (using secrets manager):
python# AWS Secrets Manager
import boto3

client = boto3.client('secretsmanager')
response = client.get_secret_value(SecretId='api-key')
api_key = response['SecretString']
2. Use HTTPS Only
Always use HTTPS in production:
python# Enforce HTTPS
if not request.is_secure():
    return redirect(request.url.replace('http://', 'https://'))
3. Implement Rate Limiting
Protect your application from abuse:
pythonfrom flask_limiter import Limiter

limiter = Limiter(
    key_func=lambda: request.headers.get('Authorization'),
    default_limits=["1000 per hour"]
)
4. Validate Tokens
Always validate tokens on the server:
pythonimport jwt

def validate_token(token):
    try:
        payload = jwt.decode(
            token,
            'your-secret-key',
            algorithms=['HS256']
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Token expired
    except jwt.InvalidTokenError:
        return None  # Invalid token
5. Use Scoped Permissions
Request only necessary scopes:
python# ❌ Don't request all permissions
scopes = "users:read users:write users:delete admin:write"

# ✅ Request minimum required
scopes = "users:read"
6. Monitor Authentication Events
Log all authentication attempts:
pythonimport logging

logger.info(f"Authentication attempt: user={user_id}, ip={ip_address}, status={status}")
7. Implement Token Refresh
Refresh tokens before expiration:
pythondef get_valid_token():
    if token_expires_in < 300:  # Less than 5 minutes
        token = refresh_access_token()
    return token
Error Responses
Authentication Errors
401 Unauthorized
Missing Token:
json{
  "status": "error",
  "error": {
    "code": "MISSING_AUTH",
    "message": "No authentication token provided"
  }
}
Invalid Token:
json{
  "status": "error",
  "error": {
    "code": "INVALID_TOKEN",
    "message": "The provided token is invalid or expired"
  }
}
Expired Token:
json{
  "status": "error",
  "error": {
    "code": "TOKEN_EXPIRED",
    "message": "Token has expired",
    "details": {
      "expired_at": "2026-02-11T12:00:00Z"
    }
  }
}