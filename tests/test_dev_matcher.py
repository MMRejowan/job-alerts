"""
Unit tests for DevMatcher.
Verifies strict exclusion of QA/Test roles, location filtering,
and accurate dev-track classification & skill matching.
"""

import unittest
from core.models import JobPosting
from core.dev_matcher import DevMatcher

class TestDevMatcher(unittest.TestCase):
    def setUp(self):
        self.matcher = DevMatcher(min_score=50)

    def test_strict_qa_exclusion(self):
        """Ensures that all test/QA/SDET positions are rejected."""
        negative_titles = [
            "Senior SDET",
            "QA Automation Engineer",
            "Software Test Engineer",
            "Lead QA Specialist",
            "Quality Assurance Engineer II",
            "Manual Tester - Mobile",
            "Test Automation Architect",
            "Automation Tester (Selenium / Playwright)",
            "Software Development Engineer in Test (SDET)",
            "UAT Test Lead",
        ]
        for title in negative_titles:
            self.assertTrue(
                self.matcher.is_negative_role(title),
                f"Expected '{title}' to be rejected by negative filter, but it was allowed."
            )

    def test_non_engineering_exclusion(self):
        """Ensures that HR, sales, interns, and executives are rejected."""
        unwanted_titles = [
            "Technical Recruiter",
            "Account Executive - Enterprise Sales",
            "Software Engineering Intern",
            "VP of Engineering",
            "Director of Operations",
            "HR Generalist",
            "UI/UX Designer",
        ]
        for title in unwanted_titles:
            self.assertTrue(
                self.matcher.is_negative_role(title),
                f"Expected '{title}' to be rejected, but it was allowed."
            )

    def test_backend_dev_matching(self):
        """Ensures that backend and software engineering roles are matched."""
        job = JobPosting(
            title="Backend Engineer - Python & Distributed Systems",
            company="Stripe",
            url="https://stripe.com/jobs/123",
            location="Remote - India",
            source="Greenhouse",
            description="Building high throughput payment APIs using Python, REST, and PostgreSQL.",
        )
        evaluated = self.matcher.evaluate_job(job)
        self.assertIsNotNone(evaluated)
        self.assertEqual(evaluated.category, "backend")
        self.assertGreaterEqual(evaluated.match_score, 60)
        self.assertTrue(any("Python" in s for s in evaluated.matched_skills))

    def test_sre_platform_matching(self):
        """Ensures that SRE and infrastructure roles are matched."""
        job = JobPosting(
            title="Site Reliability Engineer (SRE)",
            company="Datadog",
            url="https://datadog.com/jobs/456",
            location="Bengaluru, India",
            source="Greenhouse",
            description="Focus on Prometheus, Grafana observability, Docker, Kubernetes, and incident triage.",
        )
        evaluated = self.matcher.evaluate_job(job)
        self.assertIsNotNone(evaluated)
        self.assertEqual(evaluated.category, "sre_platform")
        self.assertGreaterEqual(evaluated.match_score, 60)

    def test_solutions_integration_matching(self):
        """Ensures that API and solutions engineering roles are matched."""
        job = JobPosting(
            title="Solutions Engineer - APIs & Platform Integrations",
            company="Postman",
            url="https://postman.com/jobs/789",
            location="Remote - Worldwide",
            source="Greenhouse",
            description="Designing REST API workflows, OAuth authentication, webhooks, and partner integrations.",
        )
        evaluated = self.matcher.evaluate_job(job)
        self.assertIsNotNone(evaluated)
        self.assertEqual(evaluated.category, "solutions_integration")

    def test_data_systems_matching(self):
        """Ensures that data and streaming roles are matched."""
        job = JobPosting(
            title="Data Engineer - Event Streaming",
            company="Spotify",
            url="https://spotify.com/jobs/999",
            location="Remote",
            source="Lever",
            description="Working with Apache Kafka, PostgreSQL, complex SQL, and real-time event streaming pipelines.",
        )
        evaluated = self.matcher.evaluate_job(job)
        self.assertIsNotNone(evaluated)
        self.assertEqual(evaluated.category, "data_systems")

    def test_location_filtering(self):
        """Ensures that ineligible regions are filtered out and eligible locations are allowed."""
        # Allowed locations
        self.assertTrue(self.matcher.is_location_eligible("Remote"))
        self.assertTrue(self.matcher.is_location_eligible("Remote - India"))
        self.assertTrue(self.matcher.is_location_eligible("Bengaluru, Karnataka, India"))
        self.assertTrue(self.matcher.is_location_eligible("Worldwide"))
        self.assertTrue(self.matcher.is_location_eligible("Pune, India"))

        # Excluded locations
        self.assertFalse(self.matcher.is_location_eligible("US Only"))
        self.assertFalse(self.matcher.is_location_eligible("Germany Only"))

if __name__ == "__main__":
    unittest.main()
