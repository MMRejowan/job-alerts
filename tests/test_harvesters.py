"""
Unit tests for JobPosting model and Deduplicator.
"""

import unittest
from pathlib import Path
import tempfile
import json
from core.models import JobPosting
from core.deduplicator import Deduplicator

class TestModelsAndDedupe(unittest.TestCase):
    def test_job_posting_initialization(self):
        job = JobPosting(
            title="Senior Backend Engineer",
            company="GitLab",
            url="https://job-boards.greenhouse.io/gitlab/jobs/12345",
            location="Remote",
            source="Greenhouse",
        )
        self.assertIsNotNone(job.id)
        self.assertTrue(job.is_direct_ats)

    def test_direct_ats_detection(self):
        gh_job = JobPosting(
            title="Software Engineer",
            company="Stripe",
            url="https://boards.greenhouse.io/stripe/jobs/555",
            location="Remote",
            source="Greenhouse",
        )
        self.assertTrue(gh_job.is_direct_ats)

        lever_job = JobPosting(
            title="Backend Engineer",
            company="Spotify",
            url="https://jobs.lever.co/spotify/abc-123/apply",
            location="Remote",
            source="Lever",
        )
        self.assertTrue(lever_job.is_direct_ats)

        ashby_job = JobPosting(
            title="Software Engineer",
            company="Linear",
            url="https://jobs.ashbyhq.com/linear/xyz",
            location="Remote",
            source="Ashby",
        )
        self.assertTrue(ashby_job.is_direct_ats)

    def test_deduplicator_local_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_state_file = Path(tmp_dir) / "test_seen.json"
            dedup = Deduplicator(bucket_name="", local_file=tmp_state_file)

            job1 = JobPosting(title="Eng 1", company="A", url="https://a.com/1", location="Remote", source="Test")
            job2 = JobPosting(title="Eng 2", company="B", url="https://b.com/2", location="Remote", source="Test")

            # Initially both are new
            new_jobs = dedup.filter_new_jobs([job1, job2])
            self.assertEqual(len(new_jobs), 2)

            # Mark job1 as seen
            dedup.mark_as_seen([job1])

            # Now only job2 is new
            new_jobs_after = dedup.filter_new_jobs([job1, job2])
            self.assertEqual(len(new_jobs_after), 1)
            self.assertEqual(new_jobs_after[0].id, job2.id)

            # Verify file was written
            self.assertTrue(tmp_state_file.exists())
            with open(tmp_state_file, "r") as f:
                data = json.load(f)
                self.assertIn(job1.id, data)

if __name__ == "__main__":
    unittest.main()
