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