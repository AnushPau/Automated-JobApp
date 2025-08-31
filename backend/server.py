from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
import logging
import uuid
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, auth
import json

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Initialize Firebase Admin
try:
    # Try to load from environment variable first
    firebase_credentials = os.environ.get('FIREBASE_CREDENTIALS')
    if firebase_credentials:
        firebase_cred_dict = json.loads(firebase_credentials)
        cred = credentials.Certificate(firebase_cred_dict)
    else:
        # Fallback to service account file
        firebase_key_path = ROOT_DIR / 'firebase-admin.json'
        if firebase_key_path.exists():
            cred = credentials.Certificate(str(firebase_key_path))
        else:
            # Initialize without credentials for now (will need to be provided)
            cred = None
    
    if cred and not firebase_admin._apps:
        firebase_app = firebase_admin.initialize_app(cred)
        FIREBASE_ENABLED = True
    else:
        FIREBASE_ENABLED = False
        print("Firebase Admin not initialized - authentication will be disabled")
except Exception as e:
    FIREBASE_ENABLED = False
    print(f"Firebase initialization failed: {e}")

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
security = HTTPBearer(auto_error=False)

# Create FastAPI app
app = FastAPI(
    title="Job Application Automation API",
    description="API for automating job applications with user profiles, templates, and field mapping",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# API Router with versioning
api_router = APIRouter(prefix="/api/v1")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000", 
        "chrome-extension://*",
        "*"  # For development - restrict in production
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============== MODELS ==============

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    firebase_uid: str
    email: EmailStr
    display_name: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    # Personal Information
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    
    # Professional Information
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    github_url: Optional[str] = None
    resume_url: Optional[str] = None
    cover_letter_template: Optional[str] = None
    
    # Work Authorization
    work_authorization: Optional[str] = None  # "US Citizen", "Green Card", "Visa Required", etc.
    visa_status: Optional[str] = None
    
    # Preferences
    preferred_locations: List[str] = []
    salary_expectation: Optional[int] = None
    remote_work_preference: Optional[str] = None  # "Remote", "Hybrid", "On-site", "No Preference"
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class JobTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    description: Optional[str] = None
    
    # Template fields that can be auto-filled
    fields: Dict[str, Any] = {}  # Key-value pairs for form fields
    
    # Metadata
    is_default: bool = False
    usage_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FieldMapping(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    site_domain: str  # e.g., "linkedin.com", "indeed.com"
    site_name: str    # e.g., "LinkedIn", "Indeed"
    
    # Field mappings: CSS selector or field identifier -> profile field name
    field_mappings: Dict[str, str] = {}
    
    # Site-specific settings
    requires_manual_review: bool = True
    auto_submit_enabled: bool = False
    notes: Optional[str] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class JobApplication(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    
    # Job Information
    job_title: str
    company_name: str
    job_url: str
    site_domain: str
    
    # Application Details
    template_id: Optional[str] = None
    mapping_id: Optional[str] = None
    status: str = "applied"  # "applied", "reviewed", "interview", "rejected", "offer"
    
    # Metadata
    applied_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: Optional[str] = None
    
    # Auto-fill success metrics
    fields_filled: int = 0
    total_fields: int = 0
    manual_review_required: bool = True

# Request/Response Models
class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    github_url: Optional[str] = None
    resume_url: Optional[str] = None
    cover_letter_template: Optional[str] = None
    work_authorization: Optional[str] = None
    visa_status: Optional[str] = None
    preferred_locations: Optional[List[str]] = None
    salary_expectation: Optional[int] = None
    remote_work_preference: Optional[str] = None

class JobTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Template name cannot be empty")
    description: Optional[str] = Field(None, max_length=1000)
    fields: Dict[str, Any] = {}
    is_default: bool = False

class JobTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    fields: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None

class FieldMappingCreate(BaseModel):
    site_domain: str = Field(..., min_length=1, max_length=200, description="Site domain cannot be empty")
    site_name: str = Field(..., min_length=1, max_length=100, description="Site name cannot be empty")
    field_mappings: Dict[str, str] = {}
    requires_manual_review: bool = True
    auto_submit_enabled: bool = False
    notes: Optional[str] = Field(None, max_length=1000)

class FieldMappingUpdate(BaseModel):
    site_name: Optional[str] = None
    field_mappings: Optional[Dict[str, str]] = None
    requires_manual_review: Optional[bool] = None
    auto_submit_enabled: Optional[bool] = None
    notes: Optional[str] = None

class JobApplicationCreate(BaseModel):
    job_title: str = Field(..., min_length=1, max_length=200, description="Job title cannot be empty")
    company_name: str = Field(..., min_length=1, max_length=200, description="Company name cannot be empty")
    job_url: str = Field(..., min_length=1, description="Job URL cannot be empty")
    site_domain: str = Field(..., min_length=1, max_length=200, description="Site domain cannot be empty")
    template_id: Optional[str] = Field(None, description="Template ID to use for this application")
    mapping_id: Optional[str] = Field(None, description="Field mapping ID for this site")
    status: str = Field("applied", pattern="^(applied|reviewed|interview|rejected|offer)$")
    notes: Optional[str] = Field(None, max_length=2000)
    fields_filled: int = Field(0, ge=0, description="Number of fields successfully filled")
    total_fields: int = Field(0, ge=0, description="Total number of fields in the form")
    manual_review_required: bool = True

# ============== DEPENDENCIES ==============

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verify Firebase ID token and return user info"""
    if not FIREBASE_ENABLED:
        # For development/testing without Firebase
        return {"uid": "test-user", "email": "test@example.com"}
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    try:
        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(credentials.credentials)
        return decoded_token
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

async def get_user_from_db(current_user: dict = Depends(get_current_user)) -> User:
    """Get or create user in database"""
    user_doc = await db.users.find_one({"firebase_uid": current_user["uid"]})
    
    if not user_doc:
        # Create new user
        user = User(
            firebase_uid=current_user["uid"],
            email=current_user.get("email", ""),
            display_name=current_user.get("name")
        )
        await db.users.insert_one(user.model_dump())
        return user
    
    return User(**user_doc)

# ============== ROUTES ==============

@api_router.get("/")
async def root():
    return {"message": "Job Application Automation API", "version": "1.0.0"}

# ============== AUTHENTICATION ==============

@api_router.post("/auth/login")
async def login_user(current_user: dict = Depends(get_current_user)):
    """Verify token and return user info"""
    user = await get_user_from_db(current_user)
    return {
        "message": "Login successful",
        "user": user.model_dump()
    }

# ============== PROFILE MANAGEMENT ==============

@api_router.get("/profiles/me", response_model=UserProfile)
async def get_my_profile(user: User = Depends(get_user_from_db)):
    """Get current user's profile"""
    profile_doc = await db.profiles.find_one({"user_id": user.id})
    
    if not profile_doc:
        # Create default profile
        profile = UserProfile(
            user_id=user.id,
            full_name=user.display_name or "",
            email=user.email
        )
        await db.profiles.insert_one(profile.model_dump())
        return profile
    
    return UserProfile(**profile_doc)

@api_router.put("/profiles/me", response_model=UserProfile)
async def update_my_profile(
    profile_update: UserProfileUpdate,
    user: User = Depends(get_user_from_db)
):
    """Update current user's profile"""
    # Get existing profile
    existing_profile = await db.profiles.find_one({"user_id": user.id})
    
    if not existing_profile:
        # Create new profile with update data
        profile_data = profile_update.model_dump(exclude_unset=True)
        profile_data.update({
            "user_id": user.id,
            "full_name": profile_data.get("full_name", user.display_name or ""),
            "email": profile_data.get("email", user.email)
        })
        profile = UserProfile(**profile_data)
        await db.profiles.insert_one(profile.model_dump())
        return profile
    
    # Update existing profile
    update_data = profile_update.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    await db.profiles.update_one(
        {"user_id": user.id},
        {"$set": update_data}
    )
    
    updated_profile = await db.profiles.find_one({"user_id": user.id})
    return UserProfile(**updated_profile)

# ============== TEMPLATE MANAGEMENT ==============

@api_router.post("/templates", response_model=JobTemplate)
async def create_template(
    template_data: JobTemplateCreate,
    user: User = Depends(get_user_from_db)
):
    """Create a new job application template"""
    template = JobTemplate(
        user_id=user.id,
        **template_data.model_dump()
    )
    
    await db.templates.insert_one(template.model_dump())
    return template

@api_router.get("/templates", response_model=List[JobTemplate])
async def get_templates(user: User = Depends(get_user_from_db)):
    """Get all templates for current user"""
    templates = await db.templates.find({"user_id": user.id}).to_list(length=None)
    return [JobTemplate(**template) for template in templates]

@api_router.get("/templates/{template_id}", response_model=JobTemplate)
async def get_template(
    template_id: str,
    user: User = Depends(get_user_from_db)
):
    """Get specific template"""
    template_doc = await db.templates.find_one({
        "id": template_id,
        "user_id": user.id
    })
    
    if not template_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    return JobTemplate(**template_doc)

@api_router.put("/templates/{template_id}", response_model=JobTemplate)
async def update_template(
    template_id: str,
    template_update: JobTemplateUpdate,
    user: User = Depends(get_user_from_db)
):
    """Update a template"""
    existing_template = await db.templates.find_one({
        "id": template_id,
        "user_id": user.id
    })
    
    if not existing_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    update_data = template_update.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    await db.templates.update_one(
        {"id": template_id, "user_id": user.id},
        {"$set": update_data}
    )
    
    updated_template = await db.templates.find_one({
        "id": template_id,
        "user_id": user.id
    })
    return JobTemplate(**updated_template)

@api_router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str,
    user: User = Depends(get_user_from_db)
):
    """Delete a template"""
    result = await db.templates.delete_one({
        "id": template_id,
        "user_id": user.id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    return {"message": "Template deleted successfully"}

# ============== FIELD MAPPING ==============

@api_router.post("/mappings", response_model=FieldMapping)
async def create_mapping(
    mapping_data: FieldMappingCreate,
    user: User = Depends(get_user_from_db)
):
    """Create a new field mapping for a job site"""
    mapping = FieldMapping(
        user_id=user.id,
        **mapping_data.model_dump()
    )
    
    await db.mappings.insert_one(mapping.model_dump())
    return mapping

@api_router.get("/mappings", response_model=List[FieldMapping])
async def get_mappings(
    site: Optional[str] = Query(None, description="Filter by site domain"),
    user: User = Depends(get_user_from_db)
):
    """Get field mappings for current user, optionally filtered by site"""
    query = {"user_id": user.id}
    if site:
        query["site_domain"] = site
    
    mappings = await db.mappings.find(query).to_list(length=None)
    return [FieldMapping(**mapping) for mapping in mappings]

@api_router.get("/mappings/{mapping_id}", response_model=FieldMapping)
async def get_mapping(
    mapping_id: str,
    user: User = Depends(get_user_from_db)
):
    """Get specific field mapping"""
    mapping_doc = await db.mappings.find_one({
        "id": mapping_id,
        "user_id": user.id
    })
    
    if not mapping_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field mapping not found"
        )
    
    return FieldMapping(**mapping_doc)

@api_router.put("/mappings/{mapping_id}", response_model=FieldMapping)
async def update_mapping(
    mapping_id: str,
    mapping_update: FieldMappingUpdate,
    user: User = Depends(get_user_from_db)
):
    """Update a field mapping"""
    existing_mapping = await db.mappings.find_one({
        "id": mapping_id,
        "user_id": user.id
    })
    
    if not existing_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field mapping not found"
        )
    
    update_data = mapping_update.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    await db.mappings.update_one(
        {"id": mapping_id, "user_id": user.id},
        {"$set": update_data}
    )
    
    updated_mapping = await db.mappings.find_one({
        "id": mapping_id,
        "user_id": user.id
    })
    return FieldMapping(**updated_mapping)

@api_router.delete("/mappings/{mapping_id}")
async def delete_mapping(
    mapping_id: str,
    user: User = Depends(get_user_from_db)
):
    """Delete a field mapping"""
    result = await db.mappings.delete_one({
        "id": mapping_id,
        "user_id": user.id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field mapping not found"
        )
    
    return {"message": "Field mapping deleted successfully"}

# ============== APPLICATION TRACKING ==============

@api_router.post("/applications", response_model=JobApplication)
async def create_application(
    application_data: JobApplicationCreate,
    user: User = Depends(get_user_from_db)
):
    """Log a new job application"""
    application = JobApplication(
        user_id=user.id,
        **application_data.model_dump()
    )
    
    # Update template usage count if template was used
    if application.template_id:
        await db.templates.update_one(
            {"id": application.template_id, "user_id": user.id},
            {"$inc": {"usage_count": 1}}
        )
    
    await db.applications.insert_one(application.model_dump())
    return application

@api_router.get("/applications", response_model=List[JobApplication])
async def get_applications(
    status: Optional[str] = Query(None, description="Filter by application status"),
    limit: int = Query(50, description="Maximum number of applications to return"),
    user: User = Depends(get_user_from_db)
):
    """Get job applications for current user"""
    query = {"user_id": user.id}
    if status:
        query["status"] = status
    
    applications = await db.applications.find(query).sort("applied_at", -1).limit(limit).to_list(length=None)
    return [JobApplication(**app) for app in applications]

@api_router.get("/applications/{application_id}", response_model=JobApplication)
async def get_application(
    application_id: str,
    user: User = Depends(get_user_from_db)
):
    """Get specific job application"""
    app_doc = await db.applications.find_one({
        "id": application_id,
        "user_id": user.id
    })
    
    if not app_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    return JobApplication(**app_doc)

@api_router.put("/applications/{application_id}", response_model=JobApplication)
async def update_application_status(
    application_id: str,
    status: str,
    notes: Optional[str] = None,
    user: User = Depends(get_user_from_db)
):
    """Update application status"""
    existing_app = await db.applications.find_one({
        "id": application_id,
        "user_id": user.id
    })
    
    if not existing_app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    update_data = {"status": status}
    if notes:
        update_data["notes"] = notes
    
    await db.applications.update_one(
        {"id": application_id, "user_id": user.id},
        {"$set": update_data}
    )
    
    updated_app = await db.applications.find_one({
        "id": application_id,
        "user_id": user.id
    })
    return JobApplication(**updated_app)

# ============== ANALYTICS ==============

@api_router.get("/analytics/summary")
async def get_analytics_summary(user: User = Depends(get_user_from_db)):
    """Get basic analytics summary"""
    pipeline = [
        {"$match": {"user_id": user.id}},
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1}
        }}
    ]
    
    status_counts = {}
    async for doc in db.applications.aggregate(pipeline):
        status_counts[doc["_id"]] = doc["count"]
    
    total_applications = await db.applications.count_documents({"user_id": user.id})
    total_templates = await db.templates.count_documents({"user_id": user.id})
    total_mappings = await db.mappings.count_documents({"user_id": user.id})
    
    # Get most recent application without ObjectId issues
    recent_app_doc = await db.applications.find_one(
        {"user_id": user.id},
        sort=[("applied_at", -1)]
    )
    
    recent_app = None
    if recent_app_doc:
        recent_app = JobApplication(**recent_app_doc).model_dump()
    
    return {
        "total_applications": total_applications,
        "total_templates": total_templates,
        "total_mappings": total_mappings,
        "status_breakdown": status_counts,
        "most_recent_application": recent_app
    }

# Include the router
app.include_router(api_router)

# Health check endpoint (outside API versioning)
@app.get("/health")
async def health_check():
    return {"status": "healthy", "firebase_enabled": FIREBASE_ENABLED}

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)