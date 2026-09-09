"""
Deduplication Engine.
Tracks previously alerted jobs using Google Cloud Storage (in production)
or a local JSON file (during development/testing), preventing duplicate alerts.
"""

import json
import time
import logging
from typing import List, Set, Dict
from pathlib import Path
from core.models import JobPosting
from config import GCS_BUCKET_NAME, STATE_FILE_NAME, LOCAL_STATE_FILE

logger = logging.getLogger(__name__)

class Deduplicator:
    def __init__(self, bucket_name: str = GCS_BUCKET_NAME, local_file: Path = LOCAL_STATE_FILE):
        self.bucket_name = bucket_name
        self.local_file = local_file
        self.seen_records: Dict[str, float] = {}  # id -> timestamp
        self._load_state()

    def _load_state(self):
        """Loads seen job records from GCS or local file."""
        if self.bucket_name:
            try:
                from google.cloud import storage
                client = storage.Client()
                bucket = client.bucket(self.bucket_name)
                blob = bucket.blob(STATE_FILE_NAME)
                if blob.exists():
                    data = blob.download_as_text()
                    self.seen_records = json.loads(data)
                    logger.info(f"Loaded {len(self.seen_records)} seen jobs from GCS bucket {self.bucket_name}")
                    return
            except Exception as e:
                logger.warning(f"Could not load state from GCS ({e}), falling back to local file.")

        # Fallback to local file
        if self.local_file.exists():
            try:
                with open(self.local_file, "r", encoding="utf-8") as f:
                    self.seen_records = json.load(f)
                    logger.info(f"Loaded {len(self.seen_records)} seen jobs from local state file.")
            except Exception as e:
                logger.warning(f"Error reading local state file: {e}")
                self.seen_records = {}
        else:
            self.seen_records = {}

    def save_state(self):
        """Persists seen job records to GCS or local file, pruning records older than 45 days."""
        now = time.time()
        max_age = 45 * 24 * 3600  # 45 days
        pruned_records = {
            job_id: ts for job_id, ts in self.seen_records.items()
            if (now - ts) < max_age
        }
        self.seen_records = pruned_records

        # Save to GCS if configured
        if self.bucket_name:
            try:
                from google.cloud import storage
                client = storage.Client()
                bucket = client.bucket(self.bucket_name)
                blob = bucket.blob(STATE_FILE_NAME)
                blob.upload_from_string(json.dumps(self.seen_records), content_type="application/json")
                logger.info(f"Saved {len(self.seen_records)} seen jobs to GCS bucket {self.bucket_name}")
                return
            except Exception as e:
                logger.error(f"Failed to save state to GCS ({e}), falling back to local file.")

        # Save to local file
        try:
            self.local_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.local_file, "w", encoding="utf-8") as f:
                json.dump(self.seen_records, f, indent=2)
            logger.info(f"Saved {len(self.seen_records)} seen jobs to local file {self.local_file}")
        except Exception as e:
            logger.error(f"Failed to write local state file: {e}")

    def filter_new_jobs(self, jobs: List[JobPosting]) -> List[JobPosting]:
        """Returns only jobs that haven't been alerted yet."""
        new_jobs = []
        for job in jobs:
            if job.id not in self.seen_records:
                new_jobs.append(job)
        return new_jobs

    def mark_as_seen(self, jobs: List[JobPosting]):
        """Marks a list of jobs as seen and saves state."""
        now = time.time()
        for job in jobs:
            self.seen_records[job.id] = now
        self.save_state()
