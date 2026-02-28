API Examples
Overview
This document provides practical, real-world examples of using the API in various programming languages and scenarios.

Getting Started
Quick Start Example
bash# Get your API key from the dashboard
export API_KEY="sk_live_abc123xyz789"

# Make your first request
curl https://api.example.com/v1/auth/me \
  -H "Authorization: Bearer $API_KEY"

User Management Examples
Create and Manage Users
Python
pythonimport requests
import os

API_KEY = os.environ.get('API_KEY')
BASE_URL = 'https://api.example.com/v1'

headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

# Create a new user
def create_user(email, name, password):
    response = requests.post(
        f'{BASE_URL}/users',
        headers=headers,
        json={
            'email': email,
            'name': name,
            'password': password,
            'role': 'user'
        }
    )
    return response.json()

# Get user by ID
def get_user(user_id):
    response = requests.get(
        f'{BASE_URL}/users/{user_id}',
        headers=headers
    )
    return response.json()

# Update user
def update_user(user_id, **updates):
    response = requests.patch(
        f'{BASE_URL}/users/{user_id}',
        headers=headers,
        json=updates
    )
    return response.json()

# List users with filters
def list_users(status='active', limit=50):
    response = requests.get(
        f'{BASE_URL}/users',
        headers=headers,
        params={
            'status': status,
            'limit': limit
        }
    )
    return response.json()

# Example usage
if __name__ == '__main__':
    # Create user
    new_user = create_user(
        email='john@example.com',
        name='John Doe',
        password='SecureP@ss123'
    )
    print(f"Created user: {new_user['data']['id']}")
    
    # Get user
    user = get_user(new_user['data']['id'])
    print(f"User details: {user['data']}")
    
    # Update user
    updated = update_user(
        new_user['data']['id'],
        name='John Smith'
    )
    print(f"Updated name: {updated['data']['name']}")
    
    # List users
    users = list_users(status='active')
    print(f"Found {len(users['data'])} active users")
JavaScript/Node.js
javascriptconst axios = require('axios');

const API_KEY = process.env.API_KEY;
const BASE_URL = 'https://api.example.com/v1';

const client = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json'
  }
});

// Create user
async function createUser(email, name, password) {
  const response = await client.post('/users', {
    email,
    name,
    password,
    role: 'user'
  });
  return response.data;
}

// Get user
async function getUser(userId) {
  const response = await client.get(`/users/${userId}`);
  return response.data;
}

// Update user
async function updateUser(userId, updates) {
  const response = await client.patch(`/users/${userId}`, updates);
  return response.data;
}

// List users with pagination
async function listAllUsers() {
  let allUsers = [];
  let cursor = null;
  
  do {
    const response = await client.get('/users', {
      params: {
        limit: 100,
        cursor: cursor
      }
    });
    
    allUsers = allUsers.concat(response.data.data);
    cursor = response.data.pagination.has_more 
      ? response.data.pagination.next_cursor 
      : null;
  } while (cursor);
  
  return allUsers;
}

// Example usage
(async () => {
  try {
    // Create user
    const newUser = await createUser(
      'jane@example.com',
      'Jane Doe',
      'SecureP@ss456'
    );
    console.log('Created user:', newUser.data.id);
    
    // Get all users
    const users = await listAllUsers();
    console.log(`Total users: ${users.length}`);
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
})();

cURL
bash#!/bin/bash

API_KEY="sk_live_abc123xyz789"
BASE_URL="https://api.example.com/v1"

# Create user
curl -X POST "$BASE_URL/users" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "bob@example.com",
    "name": "Bob Wilson",
    "password": "SecureP@ss789",
    "role": "user"
  }'

# Get user
USER_ID="usr_abc123"
curl "$BASE_URL/users/$USER_ID" \
  -H "Authorization: Bearer $API_KEY"

# Update user
curl -X PATCH "$BASE_URL/users/$USER_ID" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Robert Wilson"
  }'

# List users
curl "$BASE_URL/users?status=active&limit=50" \
  -H "Authorization: Bearer $API_KEY"

# Delete user
curl -X DELETE "$BASE_URL/users/$USER_ID" \
  -H "Authorization: Bearer $API_KEY"

OAuth 2.0 Authentication
Complete OAuth Flow
Python (Flask)
pythonfrom flask import Flask, redirect, request, session, url_for
import requests
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

CLIENT_ID = 'your_client_id'
CLIENT_SECRET = 'your_client_secret'
REDIRECT_URI = 'http://localhost:5000/callback'
AUTH_URL = 'https://api.example.com/oauth/authorize'
TOKEN_URL = 'https://api.example.com/oauth/token'
API_URL = 'https://api.example.com/v1'

@app.route('/')
def index():
    if 'access_token' in session:
        return f'Logged in! <a href="/profile">View Profile</a> | <a href="/logout">Logout</a>'
    return '<a href="/login">Login with OAuth</a>'

@app.route('/login')
def login():
    # Generate random state for CSRF protection
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    
    # Build authorization URL
    auth_url = (
        f"{AUTH_URL}?"
        f"response_type=code&"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"scope=users:read users:write&"
        f"state={state}"
    )
    
    return redirect(auth_url)

@app.route('/callback')
def callback():
    # Verify state to prevent CSRF
    state = request.args.get('state')
    if state != session.get('oauth_state'):
        return 'Invalid state parameter', 400
    
    # Get authorization code
    code = request.args.get('code')
    if not code:
        return 'No code provided', 400
    
    # Exchange code for access token
    token_response = requests.post(TOKEN_URL, data={
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI
    })
    
    if token_response.status_code != 200:
        return 'Failed to obtain token', 400
    
    token_data = token_response.json()
    session['access_token'] = token_data['access_token']
    session['refresh_token'] = token_data.get('refresh_token')
    
    return redirect(url_for('profile'))

@app.route('/profile')
def profile():
    if 'access_token' not in session:
        return redirect(url_for('login'))
    
    # Get user profile
    headers = {'Authorization': f"Bearer {session['access_token']}"}
    response = requests.get(f'{API_URL}/auth/me', headers=headers)
    
    if response.status_code == 401:
        # Token expired, try refresh
        if 'refresh_token' in session:
            return redirect(url_for('refresh'))
        return redirect(url_for('login'))
    
    user = response.json()['data']
    return f"<h1>Welcome, {user['name']}</h1><p>Email: {user['email']}</p>"

@app.route('/refresh')
def refresh():
    if 'refresh_token' not in session:
        return redirect(url_for('login'))
    
    # Refresh access token
    token_response = requests.post(TOKEN_URL, data={
        'grant_type': 'refresh_token',
        'refresh_token': session['refresh_token'],
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    })
    
    if token_response.status_code != 200:
        return redirect(url_for('login'))
    
    token_data = token_response.json()
    session['access_token'] = token_data['access_token']
    session['refresh_token'] = token_data.get('refresh_token')
    
    return redirect(url_for('profile'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
JavaScript (Express)
javascriptconst express = require('express');
const session = require('express-session');
const axios = require('axios');
const crypto = require('crypto');

const app = express();

app.use(session({
  secret: crypto.randomBytes(32).toString('hex'),
  resave: false,
  saveUninitialized: false
}));

const CLIENT_ID = 'your_client_id';
const CLIENT_SECRET = 'your_client_secret';
const REDIRECT_URI = 'http://localhost:3000/callback';
const AUTH_URL = 'https://api.example.com/oauth/authorize';
const TOKEN_URL = 'https://api.example.com/oauth/token';
const API_URL = 'https://api.example.com/v1';

app.get('/', (req, res) => {
  if (req.session.accessToken) {
    res.send('Logged in! <a href="/profile">View Profile</a> | <a href="/logout">Logout</a>');
  } else {
    res.send('<a href="/login">Login with OAuth</a>');
  }
});

app.get('/login', (req, res) => {
  const state = crypto.randomBytes(32).toString('hex');
  req.session.oauthState = state;
  
  const authUrl = `${AUTH_URL}?` +
    `response_type=code&` +
    `client_id=${CLIENT_ID}&` +
    `redirect_uri=${encodeURIComponent(REDIRECT_URI)}&` +
    `scope=users:read users:write&` +
    `state=${state}`;
  
  res.redirect(authUrl);
});

app.get('/callback', async (req, res) => {
  const { code, state } = req.query;
  
  // Verify state
  if (state !== req.session.oauthState) {
    return res.status(400).send('Invalid state');
  }
  
  try {
    // Exchange code for token
    const tokenResponse = await axios.post(TOKEN_URL, {
      grant_type: 'authorization_code',
      code,
      client_id: CLIENT_ID,
      client_secret: CLIENT_SECRET,
      redirect_uri: REDIRECT_URI
    });
    
    req.session.accessToken = tokenResponse.data.access_token;
    req.session.refreshToken = tokenResponse.data.refresh_token;
    
    res.redirect('/profile');
  } catch (error) {
    res.status(400).send('Authentication failed');
  }
});

app.get('/profile', async (req, res) => {
  if (!req.session.accessToken) {
    return res.redirect('/login');
  }
  
  try {
    const response = await axios.get(`${API_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${req.session.accessToken}` }
    });
    
    const user = response.data.data;
    res.send(`<h1>Welcome, ${user.name}</h1><p>Email: ${user.email}</p>`);
  } catch (error) {
    if (error.response?.status === 401) {
      return res.redirect('/refresh');
    }
    res.status(500).send('Error fetching profile');
  }
});

app.get('/logout', (req, res) => {
  req.session.destroy();
  res.redirect('/');
});

app.listen(3000, () => {
  console.log('Server running on http://localhost:3000');
});

Project and Task Management
Complete Workflow Example
Python
pythonimport requests
from typing import List, Dict
from datetime import datetime, timedelta

class ProjectManager:
    def __init__(self, api_key: str, org_id: str):
        self.api_key = api_key
        self.org_id = org_id
        self.base_url = 'https://api.example.com/v1'
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def create_project(self, name: str, description: str) -> Dict:
        """Create a new project."""
        response = requests.post(
            f'{self.base_url}/organizations/{self.org_id}/projects',
            headers=self.headers,
            json={
                'name': name,
                'description': description,
                'settings': {
                    'visibility': 'private',
                    'enable_notifications': True
                }
            }
        )
        response.raise_for_status()
        return response.json()['data']
    
    def create_tasks(self, project_id: str, tasks: List[Dict]) -> List[Dict]:
        """Create multiple tasks in a project."""
        created_tasks = []
        
        for task in tasks:
            response = requests.post(
                f'{self.base_url}/projects/{project_id}/tasks',
                headers=self.headers,
                json=task
            )
            response.raise_for_status()
            created_tasks.append(response.json()['data'])
        
        return created_tasks
    
    def assign_tasks(self, tasks: List[Dict], assignees: List[str]) -> None:
        """Assign tasks to team members."""
        for i, task in enumerate(tasks):
            assignee = assignees[i % len(assignees)]
            
            requests.patch(
                f'{self.base_url}/tasks/{task["id"]}',
                headers=self.headers,
                json={'assignee_id': assignee}
            )
    
    def get_project_status(self, project_id: str) -> Dict:
        """Get project analytics and status."""
        response = requests.get(
            f'{self.base_url}/projects/{project_id}/analytics',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()['data']
    
    def complete_task(self, task_id: str) -> Dict:
        """Mark a task as complete."""
        response = requests.patch(
            f'{self.base_url}/tasks/{task_id}',
            headers=self.headers,
            json={
                'status': 'done',
                'completed_at': datetime.utcnow().isoformat() + 'Z'
            }
        )
        response.raise_for_status()
        return response.json()['data']

# Example: Set up a new project
if __name__ == '__main__':
    manager = ProjectManager(
        api_key='sk_live_abc123xyz789',
        org_id='org_abc123'
    )
    
    # Create project
    project = manager.create_project(
        name='Q2 2026 Product Launch',
        description='Launch new product features for Q2'
    )
    print(f"Created project: {project['id']}")
    
    # Define tasks
    tasks = [
        {
            'title': 'Design UI mockups',
            'description': 'Create mockups for new features',
            'priority': 'high',
            'due_date': (datetime.now() + timedelta(days=7)).date().isoformat(),
            'tags': ['design', 'frontend']
        },
        {
            'title': 'Implement backend API',
            'description': 'Build REST API endpoints',
            'priority': 'high',
            'due_date': (datetime.now() + timedelta(days=14)).date().isoformat(),
            'tags': ['backend', 'api']
        },
        {
            'title': 'Write documentation',
            'description': 'API documentation and user guides',
            'priority': 'medium',
            'due_date': (datetime.now() + timedelta(days=21)).date().isoformat(),
            'tags': ['documentation']
        }
    ]
    
    # Create tasks
    created_tasks = manager.create_tasks(project['id'], tasks)
    print(f"Created {len(created_tasks)} tasks")
    
    # Assign tasks to team
    team_members = ['usr_alice123', 'usr_bob456', 'usr_charlie789']
    manager.assign_tasks(created_tasks, team_members)
    print("Tasks assigned to team members")
    
    # Check project status
    status = manager.get_project_status(project['id'])
    print(f"Project status: {status['tasks']}")

File Upload and Management
Upload Files with Progress
Python
pythonimport requests
from pathlib import Path
from tqdm import tqdm

class FileUploader:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = 'https://api.example.com/v1'
        self.headers = {'Authorization': f'Bearer {api_key}'}
    
    def upload_file(self, project_id: str, file_path: str, folder: str = None):
        """Upload a file with progress bar."""
        file_path = Path(file_path)
        file_size = file_path.stat().st_size
        
        with open(file_path, 'rb') as f:
            # Wrap file in tqdm for progress
            with tqdm(total=file_size, unit='B', unit_scale=True, desc=file_path.name) as pbar:
                def read_with_progress(chunk_size=8192):
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        pbar.update(len(chunk))
                        yield chunk
                
                files = {'file': (file_path.name, read_with_progress())}
                data = {}
                if folder:
                    data['folder'] = folder
                
                response = requests.post(
                    f'{self.base_url}/projects/{project_id}/files',
                    headers=self.headers,
                    files=files,
                    data=data
                )
        
        response.raise_for_status()
        return response.json()['data']
    
    def upload_directory(self, project_id: str, directory: str, folder: str = None):
        """Upload all files in a directory."""
        directory = Path(directory)
        uploaded_files = []
        
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                relative_path = file_path.relative_to(directory)
                target_folder = f"{folder}/{relative_path.parent}" if folder else str(relative_path.parent)
                
                print(f"\nUploading {file_path.name}...")
                result = self.upload_file(project_id, str(file_path), target_folder)
                uploaded_files.append(result)
        
        return uploaded_files
    
    def download_file(self, file_id: str, output_path: str):
        """Download a file."""
        response = requests.get(
            f'{self.base_url}/files/{file_id}/download',
            headers=self.headers,
            stream=True
        )
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(output_path, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=output_path) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    pbar.update(len(chunk))

# Example usage
if __name__ == '__main__':
    uploader = FileUploader('sk_live_abc123xyz789')
    
    # Upload single file
    result = uploader.upload_file(
        project_id='prj_abc123',
        file_path='./designs/mockup.png',
        folder='designs/v2'
    )
    print(f"\nUploaded: {result['url']}")
    
    # Upload directory
    results = uploader.upload_directory(
        project_id='prj_abc123',
        directory='./assets',
        folder='project-assets'
    )
    print(f"\nUploaded {len(results)} files")

    Webhook Handler
Receive and Verify Webhooks
Python (Flask)
pythonfrom flask import Flask, request, jsonify
import hmac
import hashlib
import json

app = Flask(__name__)

WEBHOOK_SECRET = 'your_webhook_secret'

def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify webhook signature."""
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

@app.route('/webhooks', methods=['POST'])
def handle_webhook():
    # Get signature from header
    signature = request.headers.get('X-Webhook-Signature')
    if not signature:
        return jsonify({'error': 'No signature provided'}), 401
    
    # Verify signature
    if not verify_signature(request.data, signature):
        return jsonify({'error': 'Invalid signature'}), 401
    
    # Parse event
    event = request.json
    event_type = event.get('type')
    event_data = event.get('data')
    
    print(f"Received webhook: {event_type}")
    
    # Handle different event types
    if event_type == 'user.created':
        handle_user_created(event_data)
    elif event_type == 'task.completed':
        handle_task_completed(event_data)
    elif event_type == 'file.uploaded':
        handle_file_uploaded(event_data)
    else:
        print(f"Unhandled event type: {event_type}")
    
    return jsonify({'status': 'received'}), 200

def handle_user_created(data):
    """Handle user creation event."""
    print(f"New user created: {data['email']}")
    # Send welcome email, create onboarding tasks, etc.

def handle_task_completed(data):
    """Handle task completion event."""
    print(f"Task completed: {data['title']}")
    # Update metrics, notify team, etc.

def handle_file_uploaded(data):
    """Handle file upload event."""
    print(f"File uploaded: {data['name']}")
    # Process file, generate thumbnail, etc.

if __name__ == '__main__':
    app.run(port=5000)

Node.js (Express)
javascriptconst express = require('express');
const crypto = require('crypto');

const app = express();
app.use(express.json());

const WEBHOOK_SECRET = 'your_webhook_secret';

function verifySignature(payload, signature) {
  const expected = crypto
    .createHmac('sha256', WEBHOOK_SECRET)
    .update(payload)
    .digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(expected),
    Buffer.from(signature)
  );
}

app.post('/webhooks', (req, res) => {
  const signature = req.headers['x-webhook-signature'];
  
  if (!signature) {
    return res.status(401).json({ error: 'No signature' });
  }
  
  const payload = JSON.stringify(req.body);
  if (!verifySignature(payload, signature)) {
    return res.status(401).json({ error: 'Invalid signature' });
  }
  
  const { type, data } = req.body;
  console.log(`Received webhook: ${type}`);
  
  switch (type) {
    case 'user.created':
      handleUserCreated(data);
      break;
    case 'task.completed':
      handleTaskCompleted(data);
      break;
    case 'file.uploaded':
      handleFileUploaded(data);
      break;
    default:
      console.log(`Unhandled event: ${type}`);
  }
  
  res.json({ status: 'received' });
});

function handleUserCreated(data) {
  console.log(`New user: ${data.email}`);
}

function handleTaskCompleted(data) {
  console.log(`Task completed: ${data.title}`);
}

function handleFileUploaded(data) {
  console.log(`File uploaded: ${data.name}`);
}

app.listen(3000, () => {
  console.log('Webhook server running on port 3000');
});
Error Handling and Retry Logic
Robust API Client
Python
pythonimport requests
import time
from typing import Optional, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self, api_key: str, max_retries: int = 3):
        self.api_key = api_key
        self.base_url = 'https://api.example.com/v1'
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make API request with retry logic."""
        url = f'{self.base_url}/{endpoint.lstrip("/")}'
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method, url, **kwargs)
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited. Retrying after {retry_after}s")
                    time.sleep(retry_after)
                    continue
                
                # Handle server errors with exponential backoff
                if response.status_code >= 500:
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning(f"Server error. Retrying in {wait_time}s")
                        time.sleep(wait_time)
                        continue
                
                # Raise for other HTTP errors
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Request failed after {self.max_retries} attempts")
                    raise
                
                wait_time = 2 ** attempt
                logger.warning(f"Request failed: {e}. Retrying in {wait_time}s")
                time.sleep(wait_time)
    
    def get(self, endpoint: str, **kwargs) -> Dict:
        return self.request('GET', endpoint, **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> Dict:
        return self.request('POST', endpoint, **kwargs)
    
    def patch(self, endpoint: str, **kwargs) -> Dict:
        return self.request('PATCH', endpoint, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> Dict:
        return self.request('DELETE', endpoint, **kwargs)

# Example usage
if __name__ == '__main__':
    client = APIClient('sk_live_abc123xyz789')
    
    try:
        # This will automatically retry on failures
        users = client.get('/users', params={'limit': 50})
        print(f"Retrieved {len(users['data'])} users")
    except Exception as e:
        logger.error(f"Failed to fetch users: {e}")