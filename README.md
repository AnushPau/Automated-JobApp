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

Create/update .env file with:

MONGO_URL=mongodb://localhost:27017
DB_NAME=job_automation
CORS_ORIGINS=http://localhost:3000,chrome-extension://*
Firebase Setup (Optional):

For production with Firebase Authentication:

Create Firebase project at https://console.firebase.google.com
Download service account JSON
Either:
Save as firebase-admin.json in backend directory, OR
Set FIREBASE_CREDENTIALS environment variable with JSON content
Run the server:

# Development mode (uses test authentication)
python server.py

# Or with supervisor (recommended)
sudo supervisorctl restart backend
Access API Documentation:

OpenAPI docs: http://localhost:8001/api/docs
ReDoc: http://localhost:8001/api/redoc
📖 Usage Examples
Authentication
# Login (returns user info)
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN"
Create a Template
curl -X POST http://localhost:8001/api/v1/templates \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Software Engineer Template",
    "description": "Template for software engineering positions",
    "fields": {
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@example.com",
      "phone": "+1234567890",
      "years_experience": "5",
      "programming_languages": "Python, JavaScript, Java"
    },
    "is_default": true
  }'
Create Field Mapping
curl -X POST http://localhost:8001/api/v1/mappings \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "site_domain": "linkedin.com",
    "site_name": "LinkedIn",
    "field_mappings": {
      "#firstName": "first_name",
      "#lastName": "last_name",
      "#email": "email",
      "#phoneNumber": "phone"
    },
    "requires_manual_review": true
  }'
Log Job Application
curl -X POST http://localhost:8001/api/v1/applications \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job_title": "Senior Software Engineer",
    "company_name": "TechCorp Inc.",
    "job_url": "https://linkedin.com/jobs/12345",
    "site_domain": "linkedin.com",
    "template_id": "your-template-id",
    "mapping_id": "your-mapping-id",
    "status": "applied",
    "fields_filled": 6,
    "total_fields": 8
  }'
Get Analytics
curl -X GET http://localhost:8001/api/v1/analytics/summary \
  -H "Authorization: Bearer YOUR_TOKEN"
🏗 Database Schema
Collections
users: User account information
profiles: Detailed user profiles
templates: Job application templates
mappings: Site-specific field mappings
applications: Job application logs
Key Fields
User Profile:

Personal: name, email, phone, address
Professional: LinkedIn, portfolio, resume URLs
Work authorization and visa status
Location and salary preferences
Template Fields:

Flexible key-value structure for any form fields
Usage tracking and default template settings
Field Mappings:

CSS selectors or field identifiers mapped to profile fields
Site-specific settings and review requirements
🔧 Development Features
Test Mode
When Firebase is not configured, the API runs in test mode with:

Mock authentication (uses "test-user" ID)
All endpoints functional for development
No Firebase dependency required
CORS Configuration
Pre-configured for:

Chrome extensions (chrome-extension://*)
Local development (localhost:3000)
Customizable via CORS_ORIGINS environment variable
Error Handling
Proper HTTP status codes
Detailed error messages
Authentication error handling
Database connection error handling
🚀 Chrome Extension Integration
This API is designed for Chrome extension integration:

Authentication: Send Firebase ID token in Authorization header
Templates: Fetch user templates for autofill
Mappings: Get site-specific field mappings
Logging: Track successful applications
CORS: Pre-configured for extension origins
Extension Usage Flow:
User logs in → Extension gets Firebase token
Extension detects job site → Fetches mappings for site
Extension loads template → Fills form fields automatically
User reviews → Submits application
Extension logs → Records application in database
📊 API Response Examples
Template Response:
{
  "id": "uuid-here",
  "user_id": "user-uuid",
  "name": "Software Engineer Template",
  "fields": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com"
  },
  "usage_count": 5,
  "is_default": true
}
Analytics Response:
{
  "total_applications": 25,
  "total_templates": 3,
  "total_mappings": 8,
  "status_breakdown": {
    "applied": 15,
    "interview": 5,
    "rejected": 3,
    "offer": 2
  }
}
🔐 Security Features
Firebase JWT token verification
User-specific data isolation
CORS protection
Input validation with Pydantic
No hardcoded credentials
🚨 Production Considerations
Firebase Setup: Configure proper Firebase credentials
CORS: Restrict origins in production
Database: Use MongoDB Atlas or dedicated instance
Rate Limiting: Implement rate limiting for production
Logging: Configure proper application logging
SSL: Use HTTPS in production
📈 Future Enhancements
Rate limiting middleware
Advanced analytics and reporting
Webhook integrations
Bulk template import/export
Template sharing between users
Advanced field mapping with AI assistance