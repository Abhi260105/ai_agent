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