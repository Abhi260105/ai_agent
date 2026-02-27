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

Response: 201 Created
json{
  "status": "success",
  "data": {
    "id": "usr_def456",
    "email": "jane.smith@example.com",
    "name": "Jane Smith",
    "role": "user",
    "status": "pending",
    "created_at": "2026-02-11T12:00:00Z"
  }
}
Error Responses:

400 Bad Request - Invalid input
409 Conflict - Email already exists
422 Unprocessable Entity - Validation errors

Update User
Update an existing user.
httpPATCH /v1/users/{user_id}
Request Body:
json{
  "name": "Jane Doe",
  "profile": {
    "bio": "Senior Product Manager"
  }
}
Response: 200 OK
json{
  "status": "success",
  "data": {
    "id": "usr_def456",
    "email": "jane.smith@example.com",
    "name": "Jane Doe",
    "role": "user",
    "status": "active",
    "updated_at": "2026-02-11T12:30:00Z"
  }
}
Delete User
Delete a user permanently.
httpDELETE /v1/users/{user_id}
Response: 204 No Content

Authentication
Get Current User
Get the authenticated user's information.
httpGET /v1/auth/me
Response: 200 OK
json{
  "status": "success",
  "data": {
    "id": "usr_abc123",
    "email": "john.doe@example.com",
    "name": "John Doe",
    "permissions": ["users:read", "users:write"]
  }
}
Change Password
Change the current user's password.
httpPOST /v1/auth/password/change
Request Body:
json{
  "current_password": "OldP@ssw0rd",
  "new_password": "NewP@ssw0rd123"
}
Response: 200 OK
json{
  "status": "success",
  "message": "Password changed successfully"
}
Request Password Reset
Request a password reset email.
httpPOST /v1/auth/password/reset
Request Body:
json{
  "email": "john.doe@example.com"
}
Response: 202 Accepted
json{
  "status": "success",
  "message": "Password reset email sent"
}

Organizations
List Organizations
Retrieve organizations the user has access to.
httpGET /v1/organizations
Response: 200 OK
json{
  "status": "success",
  "data": [
    {
      "id": "org_abc123",
      "name": "Acme Corporation",
      "slug": "acme-corp",
      "plan": "enterprise",
      "member_count": 150,
      "created_at": "2025-06-01T00:00:00Z"
    }
  ]
}
Get Organization
Retrieve a specific organization.
httpGET /v1/organizations/{org_id}
Response: 200 OK
json{
  "status": "success",
  "data": {
    "id": "org_abc123",
    "name": "Acme Corporation",
    "slug": "acme-corp",
    "plan": "enterprise",
    "settings": {
      "allow_signup": true,
      "require_2fa": true
    },
    "billing": {
      "plan": "enterprise",
      "seats": 150,
      "billing_email": "billing@acme.com"
    },
    "created_at": "2025-06-01T00:00:00Z"
  }
}
Create Organization
Create a new organization.
httpPOST /v1/organizations
Request Body:
json{
  "name": "Startup Inc",
  "slug": "startup-inc",
  "plan": "pro"
}
Response: 201 Created
List Organization Members
List members of an organization.
httpGET /v1/organizations/{org_id}/members
Response: 200 OK
json{
  "status": "success",
  "data": [
    {
      "user_id": "usr_abc123",
      "email": "john@acme.com",
      "name": "John Doe",
      "role": "admin",
      "joined_at": "2025-06-01T00:00:00Z"
    }
  ]
}

Projects
List Projects
Retrieve projects within an organization.
httpGET /v1/organizations/{org_id}/projects
Query Parameters:
ParameterTypeDescriptionstatusstringFilter: active, archivedsortstringSort: created_at:desc, name:asc
Response: 200 OK
json{
  "status": "success",
  "data": [
    {
      "id": "prj_abc123",
      "name": "Website Redesign",
      "description": "Q2 2026 website refresh",
      "status": "active",
      "owner_id": "usr_def456",
      "team_size": 8,
      "created_at": "2026-01-10T00:00:00Z"
    }
  ]
}
Create Project
Create a new project.
httpPOST /v1/organizations/{org_id}/projects
Request Body:
json{
  "name": "Mobile App v2",
  "description": "Next generation mobile application",
  "settings": {
    "visibility": "private",
    "enable_notifications": true
  }
}
Response: 201 Created
Get Project
Retrieve project details.
httpGET /v1/projects/{project_id}
Response: 200 OK
json{
  "status": "success",
  "data": {
    "id": "prj_abc123",
    "name": "Website Redesign",
    "description": "Q2 2026 website refresh",
    "status": "active",
    "organization_id": "org_abc123",
    "owner": {
      "id": "usr_def456",
      "name": "Jane Doe"
    },
    "stats": {
      "tasks": 45,
      "completed": 32,
      "in_progress": 10,
      "blocked": 3
    },
    "created_at": "2026-01-10T00:00:00Z",
    "updated_at": "2026-02-11T10:00:00Z"
  }
}

Tasks
List Tasks
Retrieve tasks within a project.
httpGET /v1/projects/{project_id}/tasks
Query Parameters:
ParameterTypeDescriptionstatusstringtodo, in_progress, doneassignee_idstringFilter by assigneeprioritystringlow, medium, high, urgentdue_beforestringISO 8601 date
Response: 200 OK
json{
  "status": "success",
  "data": [
    {
      "id": "tsk_abc123",
      "title": "Design homepage mockup",
      "description": "Create high-fidelity mockup for homepage",
      "status": "in_progress",
      "priority": "high",
      "assignee": {
        "id": "usr_ghi789",
        "name": "Alice Johnson"
      },
      "due_date": "2026-02-15",
      "created_at": "2026-02-05T09:00:00Z"
    }
  ]
}
Create Task
Create a new task.
httpPOST /v1/projects/{project_id}/tasks
Request Body:
json{
  "title": "Implement user authentication",
  "description": "Add OAuth 2.0 authentication flow",
  "priority": "high",
  "assignee_id": "usr_ghi789",
  "due_date": "2026-02-20",
  "tags": ["backend", "security"]
}
Response: 201 Created
Update Task
Update task details or status.
httpPATCH /v1/tasks/{task_id}
Request Body:
json{
  "status": "done",
  "completed_at": "2026-02-11T15:00:00Z"
}
Response: 200 OK

Files
Upload File
Upload a file to a project.
httpPOST /v1/projects/{project_id}/files
Content-Type: multipart/form-data
Form Data:
FieldTypeRequiredDescriptionfilefileYesFile to uploadnamestringNoCustom filenamefolderstringNoFolder path
Response: 201 Created
json{
  "status": "success",
  "data": {
    "id": "fil_abc123",
    "name": "design-mockup.png",
    "size": 2048576,
    "mime_type": "image/png",
    "url": "https://cdn.example.com/files/design-mockup.png",
    "thumbnail_url": "https://cdn.example.com/thumbnails/design-mockup.png",
    "uploaded_by": "usr_def456",
    "created_at": "2026-02-11T12:00:00Z"
  }
}
List Files
List files in a project.
httpGET /v1/projects/{project_id}/files
Query Parameters:
ParameterTypeDescriptionfolderstringFilter by folder pathmime_typestringFilter by MIME typeuploaded_afterstringISO 8601 date filter
Response: 200 OK
Download File
Download a file.
httpGET /v1/files/{file_id}/download
Response: 200 OK
Returns the file content with appropriate Content-Type and Content-Disposition headers.
Delete File
Delete a file.
httpDELETE /v1/files/{file_id}
Response: 204 No Content

Webhooks
List Webhooks
List configured webhooks.
httpGET /v1/webhooks
Response: 200 OK
json{
  "status": "success",
  "data": [
    {
      "id": "whk_abc123",
      "url": "https://yourapp.com/webhooks",
      "events": ["user.created", "task.completed"],
      "status": "active",
      "created_at": "2026-01-15T00:00:00Z"
    }
  ]
}
Create Webhook
Create a new webhook subscription.
httpPOST /v1/webhooks
Request Body:
json{
  "url": "https://yourapp.com/webhooks",
  "events": ["user.created", "user.updated", "task.completed"],
  "secret": "your_webhook_secret"
}
Available Events:

user.created, user.updated, user.deleted
organization.created, organization.updated
project.created, project.updated, project.deleted
task.created, task.updated, task.completed, task.deleted
file.uploaded, file.deleted

Response: 201 Created
Test Webhook
Send a test webhook event.
httpPOST /v1/webhooks/{webhook_id}/test
Response: 200 OK
json{
  "status": "success",
  "message": "Test webhook sent successfully",
  "response": {
    "status_code": 200,
    "latency_ms": 145
  }
}
Delete Webhook
Delete a webhook subscription.
httpDELETE /v1/webhooks/{webhook_id}
Response: 204 No Content

Analytics
Get Usage Statistics
Retrieve API usage statistics.
httpGET /v1/analytics/usage
Query Parameters:
ParameterTypeDescriptionstart_datestringISO 8601 dateend_datestringISO 8601 dategranularitystringhour, day, week, month
Response: 200 OK
json{
  "status": "success",
  "data": {
    "period": {
      "start": "2026-02-01T00:00:00Z",
      "end": "2026-02-11T23:59:59Z"
    },
    "total_requests": 125000,
    "successful_requests": 123500,
    "failed_requests": 1500,
    "average_response_time_ms": 245,
    "by_endpoint": [
      {
        "endpoint": "/v1/users",
        "method": "GET",
        "count": 45000,
        "avg_response_time_ms": 180
      }
    ],
    "by_status_code": {
      "200": 100000,
      "201": 20000,
      "400": 1000,
      "404": 500,
      "500": 100
    }
  }
}
Get Project Analytics
Retrieve project-specific analytics.
httpGET /v1/projects/{project_id}/analytics
Response: 200 OK
json{
  "status": "success",
  "data": {
    "tasks": {
      "total": 150,
      "completed": 100,
      "in_progress": 35,
      "todo": 15
    },
    "velocity": {
      "tasks_per_week": 12.5,
      "completion_rate": 0.87
    },
    "team": {
      "active_members": 8,
      "total_contributions": 450
    }
  }
}

Batch Operations
Execute Batch Request
Execute multiple operations in a single request.
httpPOST /v1/batch
Request Body:
json{
  "operations": [
    {
      "method": "POST",
      "path": "/users",
      "body": {
        "email": "user1@example.com",
        "name": "User 1"
      }
    },
    {
      "method": "GET",
      "path": "/users/usr_abc123"
    },
    {
      "method": "PATCH",
      "path": "/tasks/tsk_def456",
      "body": {
        "status": "done"
      }
    }
  ]
}
Response: 200 OK
json{
  "status": "success",
  "results": [
    {
      "status": 201,
      "body": {
        "id": "usr_new123",
        "email": "user1@example.com"
      }
    },
    {
      "status": 200,
      "body": {
        "id": "usr_abc123",
        "name": "John Doe"
      }
    },
    {
      "status": 200,
      "body": {
        "id": "tsk_def456",
        "status": "done"
      }
    }
  ]
}