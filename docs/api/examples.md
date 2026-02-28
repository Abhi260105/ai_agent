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