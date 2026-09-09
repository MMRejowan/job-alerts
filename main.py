"""
Main Entry Point for Dev-Oriented Daily Job Alerts.
Functions as both:
1. Google Cloud Function (Gen 2) HTTP endpoint: daily_job_alert(request)
2. Standalone CLI runner: python main.py [--dry-run | --test-email | --send-now]
"""

import sys
import logging
import argparse
from typing import Dict, List
from collections import defaultdict
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

from core.models import JobPosting
from core.dev_matcher import DevMatcher
from core.deduplicator import Deduplicator
from core.email_service import EmailService
from harvesters.greenhouse import GreenhouseHarvester
from harvesters.lever import LeverHarvester
from harvesters.ashby import AshbyHarvester
from harvesters.remote_apis import RemoteDevHarvester
from config import BASE_DIR, MAX_JOBS_PER_CATEGORY, ALERT_RECIPIENT

def run_job_pipeline(dry_run: bool = False, test_email: bool = False) -> Dict:
    """Executes the full harvest -> classify -> dedupe -> email pipeline."""
    logger.info("Starting Dev Job Alert Pipeline...")

    # 1. Initialize Components
    harvesters = [
        GreenhouseHarvester(),
        LeverHarvester(),
        AshbyHarvester(),
        RemoteDevHarvester(),
    ]
    matcher = DevMatcher()
    deduplicator = Deduplicator()
    email_service = EmailService()

    # 2. Harvest raw jobs across all sources
    raw_jobs: List[JobPosting] = []
    for h in harvesters:
        try:
            logger.info(f"Harvesting from {h.name}...")
            jobs = h.harvest()
            raw_jobs.extend(jobs)
        except Exception as e:
            logger.error(f"Error during harvest from {h.name}: {e}")

    logger.info(f"Total raw postings fetched: {len(raw_jobs)}")

    # 3. Filter and categorize dev roles (strictly dropping QA/test roles)
    matched_jobs: List[JobPosting] = []
    for job in raw_jobs:
        evaluated = matcher.evaluate_job(job)
        if evaluated:
            matched_jobs.append(evaluated)

    logger.info(f"Total dev-oriented matching roles: {len(matched_jobs)}")

    # 4. Deduplicate (filter out previously alerted jobs)
    if dry_run or test_email:
        # In dry run or test email, show all top matches without skipping or modifying state
        new_jobs = matched_jobs
        logger.info(f"Running in preview/test mode: evaluating {len(new_jobs)} matched jobs.")
    else:
        new_jobs = deduplicator.filter_new_jobs(matched_jobs)
        logger.info(f"New (unseen) jobs after deduplication: {len(new_jobs)}")

    # 5. Group and rank by category
    categorized: Dict[str, List[JobPosting]] = defaultdict(list)
    for job in new_jobs:
        categorized[job.category].append(job)

    # Sort each category by match_score descending, and cap at MAX_JOBS_PER_CATEGORY
    final_categorized: Dict[str, List[JobPosting]] = {}
    total_selected = 0
    selected_jobs_list: List[JobPosting] = []

    for cat, jobs in categorized.items():
        jobs.sort(key=lambda j: j.match_score, reverse=True)
        top_slice = jobs[:MAX_JOBS_PER_CATEGORY]
        final_categorized[cat] = top_slice
        total_selected += len(top_slice)
        selected_jobs_list.extend(top_slice)

    logger.info(f"Selected {total_selected} top dev roles across {len(final_categorized)} categories.")

    # 6. Render HTML Email Digest
    html_content = email_service.render_digest(final_categorized)

    # 7. Action based on execution mode
    preview_file = BASE_DIR / "preview_email.html"
    with open(preview_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    logger.info(f"HTML email preview saved to: {preview_file}")

    email_sent = False
    if test_email or (not dry_run and total_selected > 0):
        subject = f"🚀 Daily Dev Job Digest: {total_selected} New Engineering Roles"
        email_sent = email_service.send_email(subject, html_content, recipient=ALERT_RECIPIENT)

        if email_sent and not test_email and not dry_run:
            # Mark selected jobs as seen only on genuine production alert
            deduplicator.mark_as_seen(selected_jobs_list)
            logger.info(f"Marked {len(selected_jobs_list)} jobs as seen.")

    return {
        "status": "success",
        "raw_harvested": len(raw_jobs),
        "dev_matched": len(matched_jobs),
        "new_unseen": len(new_jobs),
        "alerted_count": total_selected,
        "email_sent": email_sent,
        "categories": {cat: len(jobs) for cat, jobs in final_categorized.items()}
    }

# Google Cloud Function Gen 2 Entrypoint
def daily_job_alert(request):
    """HTTP Cloud Function Gen 2 handler triggered by Cloud Scheduler."""
    try:
        # Check query parameters for dry-run
        args = request.args if hasattr(request, "args") else {}
        dry_run = args.get("dry_run", "false").lower() == "true"
        
        results = run_job_pipeline(dry_run=dry_run)
        return (results, 200, {"Content-Type": "application/json"})
    except Exception as e:
        logger.exception("Error during Cloud Function execution:")
        return ({"status": "error", "error": str(e)}, 500, {"Content-Type": "application/json"})

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily Dev Job Alert Engine")
    parser.add_argument("--dry-run", action="store_true", help="Harvest and generate preview_email.html without sending email or updating state")
    parser.add_argument("--test-email", action="store_true", help="Harvest, render, and send a test email to verify Gmail credentials without updating state")
    parser.add_argument("--send-now", action="store_true", help="Run full production alert: harvest, send email, and update seen state")

    cli_args = parser.parse_args()

    # Default to dry-run if no arguments provided
    is_dry = cli_args.dry_run or (not cli_args.test_email and not cli_args.send_now)
    is_test = cli_args.test_email

    res = run_job_pipeline(dry_run=is_dry, test_email=is_test)
    print("\n" + "="*50)
    print("PIPELINE EXECUTION SUMMARY")
    print("="*50)
    for k, v in res.items():
        print(f"  {k}: {v}")
    print("="*50)
