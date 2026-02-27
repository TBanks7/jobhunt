# =============================================================================
# config.py — All settings, keys, and search parameters in one place
# =============================================================================
# SETUP INSTRUCTIONS:
# 1. Fill in your API keys below
# 2. Install dependencies: pip install -r requirements.txt
# 3. Run once manually to test: python main.py --now
# 4. Schedule with Windows Task Scheduler to run main.py daily at 9am
# =============================================================================

import os
from dotenv import load_dotenv

# Load local .env for development (ignored by git). In production, set real env vars.
load_dotenv()

# --- API KEYS (must be provided via environment variables) ---
# Set these in your environment or in a local .env file (see .env.example).
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
NOTION_API_KEY    = os.getenv("NOTION_API_KEY")

# --- NOTION ---
# After running setup_notion.py, paste the database ID here
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# --- JOB SEARCH PARAMETERS ---
SEARCH_QUERIES = [
    "fullstack developer",
    "full stack developer",
    "Java engineer",
    "backend engineer",
    "software engineer",
]

SEARCH_LOCATIONS = [
    "Canada",
    "Ontario",
    "Vancouver, British Columbia",
    "Remote, Canada",
]

# Platforms to search (jobspy supports: linkedin, indeed, glassdoor, zip_recruiter)
SEARCH_PLATFORMS = ["linkedin", "indeed", "glassdoor", "zip_recruiter"]

# Only fetch jobs posted in the last N hours
HOURS_OLD = 24

# Max results per query/platform combo
RESULTS_PER_QUERY = 20

# --- EXPERIENCE LEVEL FILTERING ---
# Jobs mentioning more than this many years required will be skipped
MAX_YEARS_EXPERIENCE = 5

# Keywords that suggest senior/lead roles to skip
SENIOR_KEYWORDS = [
    "senior", "sr.", "lead", "principal", "staff", "architect",
    "head of", "director", "manager", "10+ years", "8+ years", "7+ years"
]

# Keywords that confirm junior/intermediate targeting
JUNIOR_KEYWORDS = [
    "junior", "intermediate", "mid-level", "associate", "entry",
    "0-3 years", "1-3 years", "2-4 years", "2-5 years", "3-5 years", "new grad"
]

# --- FILE PATHS ---
BASE_DIR         = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR    = os.path.join(BASE_DIR, "templates")
OUTPUT_DIR       = os.path.join(BASE_DIR, "output")
RESUME_TEX       = os.path.join(TEMPLATES_DIR, "resume.tex")
COVER_LETTER_DOC = os.path.join(TEMPLATES_DIR, "cover_letter.docx")
CSV_TRACKER      = os.path.join(BASE_DIR, "applied_jobs.csv")

# --- CANDIDATE PROFILE (used in Claude prompts) ---
CANDIDATE_PROFILE = """
Name: Temitope Bankole
Location: Peterborough, ON, Canada
Email: temitopebankole@aol.com
Phone: (705) 917-8517
Portfolio: temitopebankole.vercel.app
LinkedIn: linkedin.com/in/temitopebankole
GitHub: github.com/TBanks7

Summary:
Full-stack software engineer and programmer analyst with 5+ years of professional experience 
building and supporting enterprise web applications and data-driven systems. Just completed 
an MSc in Big Data Analytics at Trent University (2025). Strong background in C#, ASP.NET, Java, 
JavaScript, Python, and SQL. Experience spans production support, backend APIs, database optimization, 
and frontend development. Comfortable working across the stack and in data engineering contexts.

Education:
- MSc Big Data Analytics, Trent University, Canada (2025) — Data Engineering, Cloud Computing
- BSc Computer Science, Covenant University, Nigeria (2021)

Work Experience:
- Software Engineer, Migranium Platforms Inc., Toronto (Jun 2024–Feb 2025)
  AWS EC2/S3, Python, SQL, REST APIs, production support, 2+ web apps, 100+ users
- Contract Software Engineer, Bennett Design Associates, Ontario (Dec 2022 – Mar 2024)
  NodeJs, Nextjs, PostgreSQL, , 1 web app, 50+ users
- Full-Stack Software Engineer, CSDC Inc., Lagos (Dec 2021–Nov 2023)
  JavaScript, HTML/CSS, Java, SQL Server, ERP systems, 3+ enterprise web apps, Agile/Scrum
- Frontend Developer (Intern), Cloud Interactive Associates, Nigeria (Mar 2020–Aug 2020)
  HTML/CSS, JavaScript, React, UI development for client projects

Key Skills:
Languages: Java, JavaScript, Python, SQL, VBA, HTML5, CSS3
Frameworks: Spring, React, Node.js, Next.js, Spring Boot
Databases: SQL Server, PostgreSQL, MongoDb MySQL, NoSQL
Cloud: AWS (EC2, S3)
Tools: Git, Docker, CI/CD, IIS, Windows Server
Practices: Agile/Scrum, code reviews, production support, debugging
"""

# --- CLAUDE MODEL ---
CLAUDE_MODEL = "claude-sonnet-4-6"

# --- SCHEDULER ---
RUN_TIME = "09:00"  # 24hr format, local time
