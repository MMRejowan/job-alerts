"""
Dev Role Classifier & Skill Matcher.
Strictly filters out QA/Test roles, evaluates location compatibility,
categorizes into dev tracks, and computes match scores based on Mushtaq's stack.
"""

import re
from typing import Optional, List, Tuple
from core.models import JobPosting
from config import (
    NEGATIVE_TITLE_KEYWORDS,
    TARGET_LOCATIONS,
    DEV_CATEGORIES,
    MIN_MATCH_SCORE,
)

# Regex for strict word boundary check on short acronyms
NEGATIVE_REGEX = re.compile(
    r"\b(qa|sdet|tester|testing|uat|sqa|qae)\b",
    re.IGNORECASE
)

# Locations strictly outside target region
EXCLUDED_REGION_REGEX = re.compile(
    r"\b(us only|usa only|united states only|uk only|canada only|emea only|latam only|germany only)\b",
    re.IGNORECASE
)

class DevMatcher:
    def __init__(self, min_score: int = MIN_MATCH_SCORE):
        self.min_score = min_score

    def is_negative_role(self, title: str) -> bool:
        """Returns True if the role is QA/Test, non-engineering, or executive."""
        title_clean = title.lower()

        # Strict regex check for QA acronyms
        if NEGATIVE_REGEX.search(title_clean):
            return True

        # Check full exclusion phrases
        for kw in NEGATIVE_TITLE_KEYWORDS:
            if " " in kw:
                if kw in title_clean:
                    return True
            else:
                # Word boundary check for single words
                if re.search(rf"\b{re.escape(kw)}\b", title_clean):
                    return True

        return False

    def is_location_eligible(self, location: str) -> bool:
        """Checks if the role is Remote, Global, India, or in Indian tech hubs."""
        if not location:
            return True  # Default to eligible if unstated on remote feeds

        loc_lower = location.lower()

        # If explicitly restricted to another country only and doesn't mention global/worldwide
        if EXCLUDED_REGION_REGEX.search(loc_lower):
            if not any(w in loc_lower for w in ["worldwide", "global", "anywhere", "india"]):
                return False

        # Match target locations
        for target in TARGET_LOCATIONS:
            if target in loc_lower:
                return True

        return False

    def evaluate_job(self, job: JobPosting) -> Optional[JobPosting]:
        """
        Classifies and scores a job posting.
        Returns the enriched JobPosting if it meets criteria, or None.
        """
        # Step 1: Strict rejection of test/QA and non-dev roles
        if self.is_negative_role(job.title):
            return None

        # Step 2: Location compatibility check
        if not self.is_location_eligible(job.location):
            return None

        title_lower = job.title.lower()
        desc_lower = (job.description or "").lower()
        full_text = f"{title_lower} {desc_lower}"

        best_category = None
        best_score = 0
        all_matched_skills: List[str] = []

        # Step 3: Categorize and compute score across dev tracks
        for cat_key, cat_meta in DEV_CATEGORIES.items():
            cat_score = 0
            cat_skills = []

            # Title matching (Base 40-50 pts)
            for kw in cat_meta["title_keywords"]:
                if kw in title_lower:
                    cat_score += 45
                    break

            # If general 'Software Engineer' or 'Engineer' in title
            if cat_score == 0 and any(t in title_lower for t in ["software engineer", "developer", "engineer"]):
                cat_score += 35

            # Skill matching in title and description (+6 to +10 pts each)
            for skill in cat_meta["tech_boost"]:
                # Check with word boundary
                if re.search(rf"\b{re.escape(skill)}\b", full_text):
                    cat_skills.append(skill.title() if len(skill) > 3 else skill.upper())
                    if re.search(rf"\b{re.escape(skill)}\b", title_lower):
                        cat_score += 15
                    else:
                        cat_score += 6

            if cat_score > best_score:
                best_score = cat_score
                best_category = cat_key
                all_matched_skills = cat_skills

        # If no specific dev track matched above threshold, check for generic software engineering
        if not best_category and any(t in title_lower for t in ["engineer", "developer"]):
            best_category = "backend"
            best_score = 40

        if not best_category:
            return None

        # Normalize score between 50 and 98
        final_score = min(best_score, 98)
        if final_score < self.min_score:
            return None

        # Populate enriched properties
        meta = DEV_CATEGORIES.get(best_category, DEV_CATEGORIES["backend"])
        job.category = best_category
        job.category_label = meta["label"]
        job.category_icon = meta["icon"]
        job.match_score = final_score
        job.matched_skills = list(dict.fromkeys(all_matched_skills))[:6]

        return job
