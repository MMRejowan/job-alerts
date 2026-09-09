"""
Ashby Public Board Harvester.
Harvests job postings from modern high-growth tech companies using Ashby ATS,
yielding direct company apply links.
"""

import requests
import logging
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from harvesters.base import BaseHarvester
from core.models import JobPosting
from config import ASHBY_ORGANIZATIONS

logger = logging.getLogger(__name__)

class AshbyHarvester(BaseHarvester):
    @property
    def name(self) -> str:
        return "Ashby ATS"

    def _fetch_org(self, org_token: str) -> List[JobPosting]:
        url = f"https://api.ashbyhq.com/posting-api/job-board/{org_token}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JobAlertBot/1.0"}
        jobs: List[JobPosting] = []

        try:
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code != 200:
                logger.debug(f"Ashby org '{org_token}' returned status {resp.status_code}")
                return []

            data = resp.json()
            raw_jobs = data.get("jobs", [])
            company_name = org_token.capitalize()

            for item in raw_jobs:
                title = item.get("title", "").strip()
                apply_url = item.get("jobUrl", "").strip()
                location = item.get("location", "Remote")
                is_remote = item.get("isRemote", False)
                if is_remote and "remote" not in location.lower():
                    location = f"Remote ({location})" if location else "Remote"

                department = item.get("department", "")

                if title and apply_url:
                    jobs.append(
                        JobPosting(
                            title=title,
                            company=company_name,
                            url=apply_url,
                            location=location,
                            source="Ashby",
                            description=f"Department: {department}",
                        )
                    )
        except Exception as e:
            logger.debug(f"Error harvesting Ashby org '{org_token}': {e}")

        return jobs

    def harvest(self) -> List[JobPosting]:
        all_jobs: List[JobPosting] = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_org = {
                executor.submit(self._fetch_org, org): org
                for org in ASHBY_ORGANIZATIONS
            }
            for future in as_completed(future_to_org):
                org = future_to_org[future]
                try:
                    jobs = future.result()
                    all_jobs.extend(jobs)
                except Exception as e:
                    logger.debug(f"Failed harvesting Ashby {org}: {e}")

        logger.info(f"AshbyHarvester: Harvested {len(all_jobs)} total raw jobs from {len(ASHBY_ORGANIZATIONS)} organizations.")
        return all_jobs
