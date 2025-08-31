# Job Application Automation API

A comprehensive backend API system for automating job applications with user profiles, templates, field mapping, and application tracking. Designed to integrate seamlessly with Chrome extensions and other frontend applications.

## 🚀 Features

- **User Authentication**: Firebase Authentication with JWT token verification
- **Profile Management**: Comprehensive user profiles with personal and professional information
- **Template System**: Create and manage reusable job application templates
- **Field Mapping**: Site-specific field mappings for different job boards
- **Application Tracking**: Log and track job application submissions
- **Analytics**: Basic analytics and reporting on application activity
- **CORS Support**: Configured for Chrome extensions and web applications

## 📋 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Verify Firebase token and login

### User Profiles
- `GET /api/v1/profiles/me` - Get current user's profile
- `PUT /api/v1/profiles/me` - Update current user's profile

### Templates (Core Autofill Feature)
- `POST /api/v1/templates` - Create new template
- `GET /api/v1/templates` - Get all user templates
- `GET /api/v1/templates/{id}` - Get specific template
- `PUT /api/v1/templates/{id}` - Update template
- `DELETE /api/v1/templates/{id}` - Delete template

### Field Mappings
- `POST /api/v1/mappings` - Create field mapping for a job site
- `GET /api/v1/mappings` - Get all mappings (optional `?site=domain` filter)
- `GET /api/v1/mappings/{id}` - Get specific mapping
- `PUT /api/v1/mappings/{id}` - Update mapping
- `DELETE /api/v1/mappings/{id}` - Delete mapping

### Application Tracking
- `POST /api/v1/applications` - Log new job application
- `GET /api/v1/applications` - Get applications (optional `?status=` filter)
- `GET /api/v1/applications/{id}` - Get specific application
- `PUT /api/v1/applications/{id}` - Update application status

### Analytics
- `GET /api/v1/analytics/summary` - Get analytics summary

### Health Check
- `GET /health` - Health check endpoint

## 🛠 Setup Instructions

### Prerequisites
- Python 3.11+
- MongoDB
- Firebase project (optional for development)

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd /app/backend
Install dependencies:

pip install -r requirements.txt
Environment Setup:

