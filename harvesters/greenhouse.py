"""
Greenhouse Public Board Harvester.
Directly accesses Greenhouse public JSON feeds for target top tech companies,
yielding 100% direct company career application URLs.
"""

import requests
import logging
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from harvesters.base import BaseHarvester
from core.models import JobPosting
from config import GREENHOUSE_BOARDS

logger = logging.getLogger(__name__)

class GreenhouseHarvester(BaseHarvester):
    @property
    def name(self) -> str:
        return "Greenhouse ATS"

    def _fetch_board(self, board_token: str) -> List[JobPosting]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JobAlertBot/1.0"}
        jobs: List[JobPosting] = []

        try:
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code != 200:
                logger.debug(f"Greenhouse board '{board_token}' returned status {resp.status_code}")
                return []

            data = resp.json()
            raw_jobs = data.get("jobs", [])
            company_name = board_token.capitalize()

            for item in raw_jobs:
                title = item.get("title", "").strip()
                apply_url = item.get("absolute_url", "").strip()
                loc_obj = item.get("location", {})
                location = loc_obj.get("name", "Remote / Flexible").strip() if isinstance(loc_obj, dict) else "Remote"
                updated_at = item.get("updated_at")

                if title and apply_url:
                    jobs.append(
                        JobPosting(
                            title=title,
                            company=company_name,
                            url=apply_url,
                            location=location,
                            source="Greenhouse",
                            posted_date=str(updated_at) if updated_at else None,
                        )
                    )
        except Exception as e:
            logger.debug(f"Error harvesting Greenhouse board '{board_token}': {e}")

        return jobs

    def harvest(self) -> List[JobPosting]:
        all_jobs: List[JobPosting] = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_board = {
                executor.submit(self._fetch_board, board): board
                for board in GREENHOUSE_BOARDS
            }
            for future in as_completed(future_to_board):
                board = future_to_board[future]
                try:
                    jobs = future.result()
                    all_jobs.extend(jobs)
                except Exception as e:
                    logger.debug(f"Failed harvesting {board}: {e}")

        logger.info(f"GreenhouseHarvester: Harvested {len(all_jobs)} total raw jobs from {len(GREENHOUSE_BOARDS)} boards.")
        return all_jobs
