import asyncio
import json
import logging
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import argparse
import sys

from playwright.async_api import async_playwright, Page, Browser, BrowserContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('linkedin_automation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class UserProfile:
    """User profile data for autofilling applications"""
    # Basic Info
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    
    # Location
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    country: str = "United States"
    
    # Professional
    linkedin_url: str = ""
    portfolio_url: str = ""
    github_url: str = ""
    resume_path: str = ""  # Local path to resume file
    
    # Work Details
    current_company: str = ""
    current_title: str = ""
    years_experience: str = "5"
    salary_expectation: str = ""
    
    # Work Authorization
    work_authorized: bool = True
    require_sponsorship: bool = False
    
    # Cover Letter Template
    cover_letter: str = "I am excited about this opportunity and believe my skills would be a great fit for this role."

@dataclass 
class JobApplication:
    """Job application data"""
    title: str
    company: str
    location: str
    job_id: str
    url: str
    applied_at: str
    status: str = "applied"

class LinkedInAutomator:
    """Main automation class for LinkedIn Easy Apply"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Load or create user profile
        self.profile = self.load_profile()
        
        # Load applied jobs history
        self.applied_jobs = self.load_applied_jobs()
        
        # Configuration
        self.delay_min = 2
        self.delay_max = 5
        self.max_applications = 10
        
    def load_profile(self) -> UserProfile:
        """Load user profile from JSON file"""
        profile_file = Path("linkedin_profile.json")
        
        if profile_file.exists():
            try:
                with open(profile_file, 'r') as f:
                    data = json.load(f)
                return UserProfile(**data)
            except Exception as e:
                logger.warning(f"Error loading profile: {e}")
        
        # Create default profile
        profile = UserProfile()
        self.save_profile(profile)
        
        logger.info("Created default profile file: linkedin_profile.json")
        logger.info("Please update your profile information before running automation")
        return profile
    
    def save_profile(self, profile: UserProfile):
        """Save user profile to JSON file"""
        try:
            with open("linkedin_profile.json", 'w') as f:
                json.dump(asdict(profile), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving profile: {e}")
    
    def load_applied_jobs(self) -> List[JobApplication]:
        """Load applied jobs history"""
        jobs_file = Path("applied_jobs.json")
        
        if jobs_file.exists():
            try:
                with open(jobs_file, 'r') as f:
                    data = json.load(f)
                return [JobApplication(**job) for job in data]
            except Exception as e:
                logger.warning(f"Error loading applied jobs: {e}")
        
        return []
    
    def save_applied_jobs(self):
        """Save applied jobs history"""
        try:
            with open("applied_jobs.json", 'w') as f:
                json.dump([asdict(job) for job in self.applied_jobs], f, indent=2)
        except Exception as e:
            logger.error(f"Error saving applied jobs: {e}")
    
    def get_applied_job_ids(self) -> set:
        """Get set of already applied job IDs"""
        return {job.job_id for job in self.applied_jobs}
    
    async def initialize_browser(self):
        """Initialize Playwright browser"""
        logger.info("Initializing browser...")
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        
        # Create context with realistic settings
        self.context = await self.browser.new_context(
            viewport={'width': 1366, 'height': 768},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # Add stealth settings
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        self.page = await self.context.new_page()
        logger.info("Browser initialized successfully")
    
    async def login_to_linkedin(self, email: str, password: str) -> bool:
        """Login to LinkedIn"""
        try:
            logger.info("Logging into LinkedIn...")
            
            await self.page.goto("https://www.linkedin.com/login")
            await self.page.wait_for_load_state('networkidle')
            
            # Fill login form
            await self.page.fill('#username', email)
            await self.random_delay(1, 2)
            await self.page.fill('#password', password)
            await self.random_delay(1, 2)
            
            # Click login button
            await self.page.click('button[type="submit"]')
            await self.page.wait_for_load_state('networkidle')
            
            # Check if login was successful
            current_url = self.page.url
            if 'feed' in current_url or 'mynetwork' in current_url:
                logger.info("Successfully logged into LinkedIn")
                return True
            elif 'challenge' in current_url:
                logger.error("LinkedIn security challenge detected. Please login manually first.")
                return False
            else:
                logger.error("Login failed - check credentials or handle 2FA manually")
                return False
                
        except Exception as e:
            logger.error(f"Error during LinkedIn login: {e}")
            return False
    
    async def search_easy_apply_jobs(self, job_title: str, location: str = "", remote: bool = True) -> List[Dict]:
        """Search for Easy Apply jobs on LinkedIn"""
        try:
            logger.info(f"Searching for '{job_title}' jobs...")
            
            # Build search URL
            search_params = {
                'keywords': job_title,
                'location': location,
                'f_LF': 'f_AL' if remote else '',  # Remote jobs
                'f_AL': 'true',  # Easy Apply filter
                'sortBy': 'DD'  # Sort by date
            }
            
            # Remove empty params
            search_params = {k: v for k, v in search_params.items() if v}
            
            # Create search URL
            base_url = "https://www.linkedin.com/jobs/search/?"
            search_url = base_url + "&".join([f"{k}={v}" for k, v in search_params.items()])
            
            await self.page.goto(search_url)
            await self.page.wait_for_load_state('networkidle')
            await self.random_delay(2, 4)
            
            jobs = []
            applied_job_ids = self.get_applied_job_ids()
            
            # Scroll to load more jobs
            for _ in range(3):
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await self.random_delay(2, 3)
            
            # Get job cards
            job_cards = await self.page.locator('.job-search-card').all()
            logger.info(f"Found {len(job_cards)} job listings")
            
            for i, card in enumerate(job_cards[:20]):  # Limit to first 20
                try:
                    # Extract job information
                    title_element = card.locator('.base-search-card__title')
                    title = await title_element.inner_text() if await title_element.count() > 0 else "Unknown Title"
                    
                    company_element = card.locator('.base-search-card__subtitle')
                    company = await company_element.inner_text() if await company_element.count() > 0 else "Unknown Company"
                    
                    location_element = card.locator('.job-search-card__location')
                    job_location = await location_element.inner_text() if await location_element.count() > 0 else "Unknown Location"
                    
                    # Get job URL and ID
                    link_element = card.locator('.base-card__full-link')
                    job_url = await link_element.get_attribute('href') if await link_element.count() > 0 else ""
                    
                    # Extract job ID from URL
                    job_id = ""
                    if job_url and "/jobs/view/" in job_url:
                        job_id = job_url.split("/jobs/view/")[1].split("?")[0]
                    
                    # Check if it's Easy Apply and not already applied
                    easy_apply = await card.locator('text=Easy Apply').count() > 0
                    
                    if easy_apply and job_id and job_id not in applied_job_ids:
                        job_data = {
                            'title': title.strip(),
                            'company': company.strip(),
                            'location': job_location.strip(),
                            'job_id': job_id,
                            'url': job_url,
                            'card_element': card
                        }
                        jobs.append(job_data)
                        logger.info(f"Found Easy Apply job: {title} at {company}")
                    elif job_id in applied_job_ids:
                        logger.info(f"Already applied to: {title} at {company}")
                
                except Exception as e:
                    logger.debug(f"Error extracting job {i}: {e}")
                    continue
            
            logger.info(f"Found {len(jobs)} new Easy Apply jobs to apply to")
            return jobs
            
        except Exception as e:
            logger.error(f"Error searching for jobs: {e}")
            return []
    
    async def apply_to_job(self, job_data: Dict) -> bool:
        """Apply to a specific job using Easy Apply"""
        try:
            title = job_data['title']
            company = job_data['company']
            job_id = job_data['job_id']
            
            logger.info(f"Applying to: {title} at {company}")
            
            # Click on the job card first
            await job_data['card_element'].click()
            await self.random_delay(2, 3)
            
            # Look for Easy Apply button
            easy_apply_button = self.page.locator('button:has-text("Easy Apply")')
            
            if await easy_apply_button.count() == 0:
                logger.warning(f"Easy Apply button not found for {title}")
                return False
            
            # Click Easy Apply
            await easy_apply_button.first.click()
            await self.page.wait_for_load_state('networkidle')
            await self.random_delay(2, 4)
            
            # Handle multi-step application process
            steps_completed = 0
            max_steps = 5  # Safety limit
            
            while steps_completed < max_steps:
                # Fill current form
                await self._fill_current_form()
                await self.random_delay(2, 3)
                
                # Look for next button or submit
                next_button = None
                
                # Try different button texts
                for button_text in ['Next', 'Review', 'Submit application', 'Submit']:
                    button = self.page.locator(f'button:has-text("{button_text}")').first
                    if await button.count() > 0 and await button.is_enabled():
                        next_button = button
                        button_label = button_text
                        break
                
                if next_button:
                    await next_button.click()
                    await self.random_delay(2, 4)
                    steps_completed += 1
                    
                    # If we clicked Submit, we're done
                    if button_label in ['Submit application', 'Submit']:
                        logger.info(f"Successfully applied to {title}!")
                        
                        # Save to applied jobs
                        application = JobApplication(
                            title=title,
                            company=company,
                            location=job_data['location'],
                            job_id=job_id,
                            url=job_data['url'],
                            applied_at=datetime.now().isoformat()
                        )
                        self.applied_jobs.append(application)
                        self.save_applied_jobs()
                        return True
                else:
                    # No next button found, might be complete or error
                    logger.warning(f"No next button found for {title}")
                    break
            
            logger.warning(f"Application process incomplete for {title}")
            return False
            
        except Exception as e:
            logger.error(f"Error applying to {job_data.get('title', 'Unknown')}: {e}")
            return False
    
    async def _fill_current_form(self):
        """Fill the current form with profile data"""
        try:
            # Get all visible form fields
            inputs = await self.page.locator('input:visible, select:visible, textarea:visible').all()
            
            for input_field in inputs:
                try:
                    field_type = await input_field.get_attribute('type') or 'text'
                    field_name = (await input_field.get_attribute('name') or '').lower()
                    field_id = (await input_field.get_attribute('id') or '').lower()
                    placeholder = (await input_field.get_attribute('placeholder') or '').lower()
                    
                    # Skip hidden, submit, and button fields
                    if field_type in ['hidden', 'submit', 'button']:
                        continue
                    
                    # Determine what to fill
                    identifiers = f"{field_name} {field_id} {placeholder}"
                    value = self._get_field_value(identifiers, field_type)
                    
                    if value:
                        if field_type == 'file':
                            # Handle file upload (resume)
                            if self.profile.resume_path and Path(self.profile.resume_path).exists():
                                await input_field.set_input_files(self.profile.resume_path)
                                logger.info("Resume uploaded")
                        elif field_type in ['checkbox', 'radio']:
                            if value.lower() in ['true', 'yes', '1']:
                                await input_field.check()
                        else:
                            # Regular text input
                            await input_field.fill(value)
                        
                        await self.random_delay(0.5, 1.5)
                
                except Exception as e:
                    logger.debug(f"Error filling field: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error filling form: {e}")
    
    def _get_field_value(self, identifiers: str, field_type: str) -> Optional[str]:
        """Get the appropriate value for a form field"""
        identifiers = identifiers.lower()
        
        # Name fields
        if 'first' in identifiers and 'name' in identifiers:
            return self.profile.first_name
        elif 'last' in identifiers and 'name' in identifiers:
            return self.profile.last_name
        elif 'name' in identifiers and 'first' not in identifiers and 'last' not in identifiers:
            return f"{self.profile.first_name} {self.profile.last_name}"
        
        # Contact info
        if 'email' in identifiers:
            return self.profile.email
        if 'phone' in identifiers:
            return self.profile.phone
        
        # Location
        if 'address' in identifiers:
            return self.profile.address
        if 'city' in identifiers:
            return self.profile.city
        if 'state' in identifiers:
            return self.profile.state
        if 'zip' in identifiers or 'postal' in identifiers:
            return self.profile.zip_code
        if 'country' in identifiers:
            return self.profile.country
        
        # Professional
        if 'linkedin' in identifiers:
            return self.profile.linkedin_url
        if 'portfolio' in identifiers or 'website' in identifiers:
            return self.profile.portfolio_url
        if 'github' in identifiers:
            return self.profile.github_url
        
        # Work details
        if 'company' in identifiers and 'current' in identifiers:
            return self.profile.current_company
        if 'title' in identifiers and 'current' in identifiers:
            return self.profile.current_title
        if 'experience' in identifiers or 'years' in identifiers:
            return self.profile.years_experience
        if 'salary' in identifiers:
            return self.profile.salary_expectation
        
        # Cover letter
        if 'cover' in identifiers or 'letter' in identifiers or 'why' in identifiers:
            return self.profile.cover_letter
        
        # Work authorization (checkboxes/radio)
        if field_type in ['checkbox', 'radio']:
            if 'authorized' in identifiers or 'eligible' in identifiers:
                return 'true' if self.profile.work_authorized else 'false'
            if 'sponsor' in identifiers or 'visa' in identifiers:
                return 'true' if self.profile.require_sponsorship else 'false'
        
        return None
    
    async def random_delay(self, min_seconds: float = None, max_seconds: float = None):
        """Add random delay to appear human-like"""
        min_delay = min_seconds or self.delay_min
        max_delay = max_seconds or self.delay_max
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)
    
    async def run_automation(self, email: str, password: str, job_title: str, 
                           location: str = "", max_applications: int = 5):
        """Main automation workflow"""
        try:
            self.max_applications = max_applications
            
            await self.initialize_browser()
            
            # Login to LinkedIn
            if not await self.login_to_linkedin(email, password):
                logger.error("Failed to login to LinkedIn")
                return
            
            # Search for jobs
            jobs = await self.search_easy_apply_jobs(job_title, location)
            
            if not jobs:
                logger.info("No new Easy Apply jobs found")
                return
            
            # Apply to jobs
            applications_sent = 0
            for job in jobs[:self.max_applications]:
                if applications_sent >= self.max_applications:
                    logger.info(f"Reached maximum applications limit ({self.max_applications})")
                    break
                
                success = await self.apply_to_job(job)
                if success:
                    applications_sent += 1
                    logger.info(f"Applications sent: {applications_sent}")
                
                # Delay between applications
                await self.random_delay(10, 20)
            
            logger.info(f"Automation completed. Applied to {applications_sent} jobs.")
            
        except Exception as e:
            logger.error(f"Error in automation: {e}")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up browser resources"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()

def setup_profile():
    """Interactive setup for user profile"""
    print("LinkedIn Auto Apply Setup")
    print("=" * 40)
    
    profile = UserProfile()
    
    # Basic info
    profile.first_name = input("First Name: ").strip()
    profile.last_name = input("Last Name: ").strip()
    profile.email = input("Email: ").strip()
    profile.phone = input("Phone: ").strip()
    
    # Location
    profile.address = input("Address (optional): ").strip()
    profile.city = input("City: ").strip()
    profile.state = input("State: ").strip()
    profile.zip_code = input("Zip Code: ").strip()
    
    # Professional
    profile.linkedin_url = input("LinkedIn URL (optional): ").strip()
    profile.portfolio_url = input("Portfolio URL (optional): ").strip()
    profile.github_url = input("GitHub URL (optional): ").strip()
    profile.resume_path = input("Resume file path (optional): ").strip()
    
    # Work details
    profile.current_company = input("Current Company (optional): ").strip()
    profile.current_title = input("Current Title (optional): ").strip()
    profile.years_experience = input("Years of Experience [5]: ").strip() or "5"
    profile.salary_expectation = input("Salary Expectation (optional): ").strip()
    
    # Work authorization
    work_auth = input("Are you authorized to work in the US? [y/N]: ").strip().lower()
    profile.work_authorized = work_auth in ['y', 'yes']
    
    if not profile.work_authorized:
        sponsor = input("Do you require sponsorship? [y/N]: ").strip().lower()
        profile.require_sponsorship = sponsor in ['y', 'yes']
    
    # Cover letter
    print("\nCover Letter Template:")
    print("(Press Enter for default, or write your own)")
    custom_cover = input().strip()
    if custom_cover:
        profile.cover_letter = custom_cover
    
    # Save profile
    automator = LinkedInAutomator()
    automator.save_profile(profile)
    
    print("\nProfile saved to linkedin_profile.json")
    print("You can edit this file anytime to update your information")

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="LinkedIn Easy Apply Automation")
    parser.add_argument("--setup", action="store_true", help="Setup user profile")
    parser.add_argument("--email", help="LinkedIn email")
    parser.add_argument("--password", help="LinkedIn password")
    parser.add_argument("--job-title", default="software engineer", help="Job title to search for")
    parser.add_argument("--location", default="", help="Job location (optional)")
    parser.add_argument("--max-apps", type=int, default=5, help="Maximum applications to send")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    
    args = parser.parse_args()
    
    if args.setup:
        setup_profile()
        return
    
    if not args.email or not args.password:
        print("LinkedIn email and password required")
        print("Usage: python linkedin_auto_apply.py --email your@email.com --password yourpass --job-title 'python developer'")
        print("Setup: python linkedin_auto_apply.py --setup")
        return
    
    # Check if profile exists
    if not Path("linkedin_profile.json").exists():
        print("Profile not found. Run --setup first:")
        print("python linkedin_auto_apply.py --setup")
        return
    
    try:
        automator = LinkedInAutomator(headless=args.headless)
        await automator.run_automation(
            email=args.email,
            password=args.password,
            job_title=args.job_title,
            location=args.location,
            max_applications=args.max_apps
        )
        
    except KeyboardInterrupt:
        logger.info("Automation stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    asyncio.run(main())