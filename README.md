A clean, standalone script that stores your profile data locally and automatically applies to LinkedIn Easy Apply jobs. No backend, no API - just a simple Python script that does the job!

## 🎯 **What This Does**

1. **Stores your data locally** (JSON files - no database needed)
2. **Searches LinkedIn** for Easy Apply jobs matching your criteria
3. **Automatically fills applications** using your saved profile data
4. **Tracks applied jobs** to avoid duplicates
5. **Works completely offline** - no external services required

## 🚀 **Quick Start**

### **Step 1: Install Dependencies**
```bash
pip install -r requirements_simple.txt
playwright install chromium
Step 2: Setup Your Profile
python linkedin_auto_apply.py --setup
This will ask for your information:

Name, email, phone
Location details
LinkedIn/portfolio URLs
Resume file path
Work authorization status
Cover letter template
Step 3: Run the Automation
python linkedin_auto_apply.py \
  --email "your.email@gmail.com" \
  --password "your_password" \
  --job-title "python developer" \
  --location "san francisco" \
  --max-apps 5
📋 Command Line Options
# Setup profile (run once)
python linkedin_auto_apply.py --setup

# Basic automation
python linkedin_auto_apply.py --email EMAIL --password PASS --job-title "software engineer"

# With location filter
python linkedin_auto_apply.py --email EMAIL --password PASS --job-title "developer" --location "remote"

# Headless mode (no browser window)
python linkedin_auto_apply.py --email EMAIL --password PASS --job-title "engineer" --headless

# Limit applications
python linkedin_auto_apply.py --email EMAIL --password PASS --job-title "python" --max-apps 10
📁 Local Files Created
The script creates these files in your directory:

linkedin_profile.json - Your profile data for autofilling
applied_jobs.json - History of jobs you've applied to
linkedin_automation.log - Detailed logs of automation runs
⚙️ Profile Configuration
Edit linkedin_profile.json to update your information:

{
  "first_name": "John",
  "last_name": "Doe", 
  "email": "john.doe@gmail.com",
  "phone": "+1-555-0123",
  "address": "123 Main St",
  "city": "San Francisco",
  "state": "CA",
  "zip_code": "94105",
  "country": "United States",
  "linkedin_url": "https://linkedin.com/in/johndoe",
  "portfolio_url": "https://johndoe.dev",
  "github_url": "https://github.com/johndoe",
  "resume_path": "/path/to/your/resume.pdf",
  "current_company": "TechCorp",
  "current_title": "Software Engineer",
  "years_experience": "5",
  "salary_expectation": "120000",
  "work_authorized": true,
  "require_sponsorship": false,
  "cover_letter": "I am excited about this opportunity and believe my skills would be a great fit for this role."
}
🎯 How It Works
1. Profile-Based Autofill
The script intelligently matches form fields to your profile data:

Name fields → first_name, last_name
Contact → email, phone
Location → address, city, state, zip_code
Experience → years_experience, current_company
Cover letter → Uses your template
2. Smart Job Filtering
Only targets Easy Apply jobs
Skips jobs you've already applied to
Focuses on recent postings
Supports location and remote filtering
3. Human-Like Behavior
Random delays between actions (2-5 seconds)
Realistic scrolling and clicking patterns
Anti-detection measures to avoid bot detection
Error handling and recovery
📊 Tracking & Analytics
Applied Jobs History
View your application history in applied_jobs.json:

[
  {
    "title": "Senior Python Developer",
    "company": "TechCorp Inc",
    "location": "Remote",
    "job_id": "3472819",
    "url": "https://linkedin.com/jobs/view/3472819",
    "applied_at": "2024-01-15T10:30:45",
    "status": "applied"
  }
]
Real-Time Logs
Monitor progress in linkedin_automation.log:

2024-01-15 10:30:15 - INFO - Searching for 'python developer' jobs...
2024-01-15 10:30:22 - INFO - Found Easy Apply job: Senior Python Developer at TechCorp Inc
2024-01-15 10:30:45 - INFO - Successfully applied to Senior Python Developer!
🛠️ Advanced Usage
Multiple Job Searches
# Search for different roles
python linkedin_auto_apply.py --email EMAIL --password PASS --job-title "frontend developer" --max-apps 3
python linkedin_auto_apply.py --email EMAIL --password PASS --job-title "backend engineer" --max-apps 3
python linkedin_auto_apply.py --email EMAIL --password PASS --job-title "full stack" --max-apps 4
Location Targeting
# Specific city
python linkedin_auto_apply.py --email EMAIL --password PASS --job-title "developer" --location "New York"

# Remote only
python linkedin_auto_apply.py --email EMAIL --password PASS --job-title "engineer" --location "remote"

# State-wide
python linkedin_auto_apply.py --email EMAIL --password PASS --job-title "python" --location "California"
Resume Upload
Make sure your resume path is correct in linkedin_profile.json:

{
  "resume_path": "/Users/john/Documents/resume.pdf"
}
The script will automatically upload your resume when forms have file upload fields.

🔧 Troubleshooting
Common Issues
1. Login Failed

Check your LinkedIn email/password
Disable 2FA on LinkedIn (or handle manually)
Try logging in manually first to clear security challenges
2. No Jobs Found

Try broader job titles ("developer" instead of "senior python developer")
Remove location filters or try "remote"
Check if you've already applied to most available jobs
3. Applications Not Submitting

Some jobs have custom forms not covered by the script
LinkedIn may have updated their form structure
Run in non-headless mode (--headless off) to see what's happening
4. Profile Not Loading

Run --setup again to recreate your profile
Check that linkedin_profile.json has valid JSON syntax
Ensure all required fields are filled
Debug Mode
Run without headless to see the browser:

python linkedin_auto_apply.py --email EMAIL --password PASS --job-title "developer"
# (removes --headless flag so you can see what's happening)
🔒 Security & Privacy
Local Storage: All data stored locally on your computer
No External APIs: Script doesn't send data to any external services
LinkedIn Compliance: Uses human-like delays and behavior
Resume Security: Your resume file stays on your computer
Login Security: Credentials only used to login to LinkedIn
📝 Best Practices
1. Start Small
Begin with --max-apps 3-5 to test
Use specific job titles first
Monitor the first few runs
2. Optimize Profile
Complete all profile fields for better matching
Use a professional email address
Keep cover letter concise but engaging
3. Smart Scheduling
Run 2-3 times per day maximum
Space out runs by several hours
Avoid peak LinkedIn usage hours
4. Job Search Strategy
Use varied job titles ("developer", "engineer", "programmer")
Try different locations and remote options
Focus on recently posted jobs (script does this automatically)
📊 Success Tips
Complete Profile: Fill out all fields for maximum form compatibility
Quality Resume: Ensure your resume file is up-to-date and professional
Compelling Cover Letter: Write a strong template that can apply to multiple jobs
Regular Updates: Update your profile as your experience grows
Monitor Results: Check your email for responses and follow up appropriately
⚠️ Important Notes
LinkedIn ToS: Use responsibly and in compliance with LinkedIn's Terms of Service
Rate Limiting: Built-in delays prevent overwhelming LinkedIn's servers
Manual Review: Always be prepared to manually complete applications that fail
Follow-up: Monitor your applications and respond to employer communications
🆘 Support Files
Main Script: linkedin_auto_apply.py
Profile Data: linkedin_profile.json
Job History: applied_jobs.json
Logs: linkedin_automation.log