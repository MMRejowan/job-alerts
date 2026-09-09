"""
Data models representing job postings and match results.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import hashlib

@dataclass
class JobPosting:
    title: str
    company: str
    url: str
    location: str
    source: str
    description: str = ""
    category: str = "backend"
    category_label: str = "Backend & Software Engineering"
    category_icon: str = "🌟"
    match_score: int = 0
    matched_skills: List[str] = field(default_factory=list)
    salary: Optional[str] = None
    posted_date: Optional[str] = None
    id: Optional[str] = None

    def __post_init__(self):
        if not self.id:
            # Generate deterministic unique ID from company and url
            clean_str = f"{self.company.lower().strip()}_{self.url.strip()}"
            self.id = hashlib.sha256(clean_str.encode("utf-8")).hexdigest()[:16]

    @property
    def is_direct_ats(self) -> bool:
        """Checks if URL is a direct ATS or company portal link."""
        lower_url = self.url.lower()
        direct_indicators = [
            "boards.greenhouse.io", "job-boards.greenhouse.io", "greenhouse.io",
            "jobs.lever.co", "api.lever.co",
            "jobs.ashbyhq.com", "ashbyhq.com",
            "myworkdayjobs.com", "smartrecruiters.com",
            "jobvite.com", "bamboohr.com", "lever.co",
        ]
        return any(ind in lower_url for ind in direct_indicators) or (not any(
            agg in lower_url for agg in ["indeed.com", "linkedin.com/jobs", "naukri.com"]
        ))
