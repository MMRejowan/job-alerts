"""
Remote Developer Feeds Harvester.
Queries Remotive and Jobicy developer APIs for remote software engineering roles.
"""

import requests
import logging
from typing import List
from harvesters.base import BaseHarvester
from core.models import JobPosting

logger = logging.getLogger(__name__)

class RemoteDevHarvester(BaseHarvester):
    @property
    def name(self) -> str:
        return "Remote Developer Feeds"

    def _harvest_remotive(self) -> List[JobPosting]:
        url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=40"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JobAlertBot/1.0"}
        jobs: List[JobPosting] = []

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("jobs", []):
                    title = item.get("title", "").strip()
                    company = item.get("company_name", "").strip()
                    url_link = item.get("url", "").strip()
                    loc = item.get("candidate_required_location", "Worldwide / Remote").strip()
                    tags = " ".join(item.get("tags", []))
                    desc = f"{tags} {item.get('description', '')[:500]}"
                    salary = item.get("salary")

                    if title and url_link:
                        jobs.append(
                            JobPosting(
                                title=title,
                                company=company,
                                url=url_link,
                                location=f"Remote ({loc})" if loc else "Remote",
                                source="Remotive Dev",
                                description=desc,
                                salary=salary if salary else None,
                            )
                        )
        except Exception as e:
            logger.debug(f"Remotive harvester error: {e}")

        return jobs

    def _harvest_jobicy(self) -> List[JobPosting]:
        url = "https://jobicy.com/api/v2/remote-jobs?count=40&industry=dev"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JobAlertBot/1.0"}
        jobs: List[JobPosting] = []

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("jobs", []):
                    title = item.get("jobTitle", "").strip()
                    company = item.get("companyName", "").strip()
                    url_link = item.get("url", "").strip()
                    geo = item.get("jobGeo", "Worldwide / Remote").strip()
                    excerpt = item.get("jobExcerpt", "")

                    if title and url_link:
                        jobs.append(
                            JobPosting(
                                title=title,
                                company=company,
                                url=url_link,
                                location=f"Remote ({geo})" if geo else "Remote",
                                source="Jobicy Dev",
                                description=excerpt[:500] if excerpt else "",
                            )
                        )
        except Exception as e:
            logger.debug(f"Jobicy harvester error: {e}")

        return jobs

    def harvest(self) -> List[JobPosting]:
        jobs = []
        jobs.extend(self._harvest_remotive())
        jobs.extend(self._harvest_jobicy())
        logger.info(f"RemoteDevHarvester: Harvested {len(jobs)} total raw jobs.")
        return jobs
