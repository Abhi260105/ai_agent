API Endpoints
Overview
This document provides detailed information about all available API endpoints, including request/response formats, parameters, and examples.
Base URL
https://api.example.com/v1

Users
List Users
Retrieve a paginated list of users.
httpGET /v1/users
Query Parameters:
ParameterTypeRequiredDescriptionlimitintegerNoNumber of items (1-100, default: 50)cursorstringNoPagination cursorstatusstringNoFilter by status: active, inactive, pendingrolestringNoFilter by role: admin, user, guestcreated_afterstringNoISO 8601 date filtercreated_beforestringNoISO 8601 date filterqstringNoSearch by name or emailsortstringNoSort order: created_at:desc, name:asc
Response: 200 OK
json{
  "status": "success",
  "data": [
    {
      "id": "usr_abc123",
      "email": "john.doe@example.com",
      "name": "John Doe",
      "role": "user",
      "status": "active",
      "created_at": "2026-01-15T10:30:00Z",
      "updated_at": "2026-02-10T14:20:00Z",
      "metadata": {
        "last_login": "2026-02-11T08:15:00Z",
        "login_count": 42
      }
    }
  ],
  "pagination": {
    "limit": 50,
    "has_more": true,
    "next_cursor": "eyJpZCI6InVzcl94eXo3ODkifQ==",
    "total": 1250
  }
}
Get User
Retrieve a specific user by ID.
httpGET /v1/users/{user_id}
Path Parameters:
ParameterTypeRequiredDescriptionuser_idstringYesUser ID (e.g., usr_abc123)
Response: 200 OK
json{
  "status": "success",
  "data": {
    "id": "usr_abc123",
    "email": "john.doe@example.com",
    "name": "John Doe",
    "role": "user",
    "status": "active",
    "profile": {
      "avatar": "https://cdn.example.com/avatars/john.jpg",
      "bio": "Software developer",
      "location": "San Francisco, CA"
    },
    "created_at": "2026-01-15T10:30:00Z",
    "updated_at": "2026-02-10T14:20:00Z"
  }
}
Error Responses:

404 Not Found - User doesn't exist

Create User
Create a new user.
httpPOST /v1/users
Request Body:
json{
  "email": "jane.smith@example.com",
  "name": "Jane Smith",
  "password": "SecureP@ssw0rd",
  "role": "user",
  "profile": {
    "bio": "Product manager",
    "location": "New York, NY"
  }
}
Required Fields:

email (string, valid email)
name (string, 2-100 characters)
password (string, min 8 characters)

Optional Fields:

role (string, default: user)
profile (object)