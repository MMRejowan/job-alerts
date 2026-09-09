"""
Lever Public Postings Harvester.
Harvests public JSON job postings from target companies using Lever ATS,
yielding direct 1-click apply links.
"""

import requests
import logging
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from harvesters.base import BaseHarvester
from core.models import JobPosting
from config import LEVER_COMPANIES

logger = logging.getLogger(__name__)

class LeverHarvester(BaseHarvester):
    @property
    def name(self) -> str:
        return "Lever ATS"

    def _fetch_company(self, company_token: str) -> List[JobPosting]:
        url = f"https://api.lever.co/v0/postings/{company_token}?mode=json"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JobAlertBot/1.0"}
        jobs: List[JobPosting] = []

        try:
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code != 200:
                logger.debug(f"Lever company '{company_token}' returned status {resp.status_code}")
                return []

            raw_jobs = resp.json()
            if not isinstance(raw_jobs, list):
                return []

            company_name = company_token.capitalize()

            for item in raw_jobs:
                title = item.get("text", "").strip()
                apply_url = item.get("applyUrl") or item.get("hostedUrl") or ""
                categories = item.get("categories", {})
                location = categories.get("location", "Remote / Flexible") if isinstance(categories, dict) else "Remote"
                description = item.get("descriptionPlain", "")

                if title and apply_url:
                    jobs.append(
                        JobPosting(
                            title=title,
                            company=company_name,
                            url=apply_url,
                            location=location,
                            source="Lever",
                            description=description[:1000] if description else "",
                        )
                    )
        except Exception as e:
            logger.debug(f"Error harvesting Lever company '{company_token}': {e}")

        return jobs

    def harvest(self) -> List[JobPosting]:
        all_jobs: List[JobPosting] = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_company = {
                executor.submit(self._fetch_company, c): c
                for c in LEVER_COMPANIES
            }
            for future in as_completed(future_to_company):
                company = future_to_company[future]
                try:
                    jobs = future.result()
                    all_jobs.extend(jobs)
                except Exception as e:
                    logger.debug(f"Failed harvesting Lever {company}: {e}")

        logger.info(f"LeverHarvester: Harvested {len(all_jobs)} total raw jobs from {len(LEVER_COMPANIES)} companies.")
        return all_jobs
