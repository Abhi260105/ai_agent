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