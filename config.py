"""
Configuration for Dev-Oriented Daily Job Alerts.
Defines target roles, skills taxonomy, location filters, negative exclusions,
company ATS boards, and environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load local .env if present
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Email Settings
GMAIL_USER = os.getenv("GMAIL_USER", "mushtaq.mdrizwan@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
ALERT_RECIPIENT = os.getenv("ALERT_RECIPIENT", GMAIL_USER)

# Google Cloud Storage Settings (for serverless deduplication)
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "")
STATE_FILE_NAME = "seen_jobs.json"
LOCAL_STATE_FILE = BASE_DIR / "data" / STATE_FILE_NAME

# Minimum score to include a job in the digest
MIN_MATCH_SCORE = int(os.getenv("MIN_MATCH_SCORE", "60"))
MAX_JOBS_PER_CATEGORY = int(os.getenv("MAX_JOBS_PER_CATEGORY", "8"))

# Target Locations (Case-insensitive substrings)
TARGET_LOCATIONS = [
    "remote",
    "anywhere",
    "worldwide",
    "global",
    "india",
    "bangalore",
    "bengaluru",
    "hyderabad",
    "pune",
    "gurgaon",
    "gurugram",
    "delhi",
    "noida",
    "mumbai",
    "chennai",
]

# Strict Negative Filters (Jobs matching these in title are strictly rejected)
NEGATIVE_TITLE_KEYWORDS = [
    # Strictly exclude QA / Testing roles
    "qa",
    "sdet",
    "tester",
    "testing",
    "test engineer",
    "test automation",
    "quality assurance",
    "quality engineer",
    "manual test",
    "automation tester",
    "test analyst",
    "qa lead",
    "software test",
    
    # Exclude non-engineering domains
    "recruiter",
    "recruiting",
    "talent acquisition",
    "human resources",
    "hr generalist",
    "sales",
    "account executive",
    "business development",
    "marketing",
    "seo",
    "growth marketer",
    "finance",
    "accountant",
    "legal",
    "counsel",
    "copywriter",
    "content writer",
    "customer success manager",
    "graphic designer",
    "product designer",
    "ui/ux designer",
    
    # Exclude non-matching seniorities
    "intern",
    "internship",
    "co-op",
    "apprentice",
    "director",
    "vp",
    "vice president",
    "head of",
    "chief",
]

# Dev Role Categories & Scoring Keywords
DEV_CATEGORIES = {
    "backend": {
        "label": "Backend & Software Engineering",
        "icon": "🌟",
        "title_keywords": [
            "backend", "back end", "software engineer", "software developer",
            "python developer", "python engineer", "node developer", "node.js developer",
            "typescript engineer", "java engineer", "java developer", "scala engineer",
            "systems engineer", "c++ engineer", "c++ developer", "api engineer"
        ],
        "tech_boost": [
            "python", "typescript", "javascript", "node.js", "java", "scala",
            "c++", "c", "rest", "graphql", "fastapi", "express", "spring", "pekko", "akka"
        ]
    },
    "sre_platform": {
        "label": "SRE, Platform & Cloud Infrastructure",
        "icon": "⚡",
        "title_keywords": [
            "site reliability", "sre", "devops", "platform engineer", "infrastructure engineer",
            "cloud engineer", "observability engineer", "reliability engineer", "systems administrator"
        ],
        "tech_boost": [
            "prometheus", "grafana", "kibana", "elasticsearch", "docker", "kubernetes",
            "k8s", "linux", "ci/cd", "jenkins", "github actions", "incident", "root cause", "rca"
        ]
    },
    "solutions_integration": {
        "label": "API, Solutions & Technical Integration",
        "icon": "🔌",
        "title_keywords": [
            "solutions engineer", "integration engineer", "technical solutions",
            "customer engineer", "partner engineer", "implementation engineer",
            "technical application support", "application support engineer", "l3 support"
        ],
        "tech_boost": [
            "api", "rest", "oauth", "jwt", "webhooks", "postman", "payload",
            "http", "integration", "troubleshooting", "debugging", "json"
        ]
    },
    "data_systems": {
        "label": "Data, Streaming & Database Engineering",
        "icon": "📊",
        "title_keywords": [
            "data engineer", "database engineer", "streaming engineer",
            "etl engineer", "analytics engineer", "pipeline engineer"
        ],
        "tech_boost": [
            "postgresql", "postgres", "mysql", "mongodb", "kafka", "sql",
            "data pipeline", "etl", "event-driven", "reactive"
        ]
    },
    "devtools": {
        "label": "Developer Productivity & Tooling",
        "icon": "🛠️",
        "title_keywords": [
            "developer tools", "devtools", "developer experience", "devex",
            "developer productivity", "tooling engineer", "internal tools"
        ],
        "tech_boost": [
            "cli", "tooling", "automation", "python", "typescript", "scripts", "build"
        ]
    }
}

# Target ATS Boards for Direct 100% Company Career Links
GREENHOUSE_BOARDS = [
    "stripe",
    "datadog",
    "cloudflare",
    "gitlab",
    "elastic",
    "figma",
    "twilio",
    "mongodb",
    "airtable",
    "reddit",
    "canva",
    "pinterest",
    "automattic",
    "coinbase",
    "instacart",
    "doordash",
    "hashicorp",
    "browserstack",
    "postman",
    "inmobi",
]

LEVER_COMPANIES = [
    "spotify",
    "palantir",
    "benchling",
    "affirm",
]

ASHBY_ORGANIZATIONS = [
    "linear",
    "ramp",
    "supabase",
    "perplexity",
    "vercel",
]
