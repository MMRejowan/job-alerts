"""
Email Notification Service.
Renders categorized HTML email digests and dispatches them via Gmail SMTP over TLS 587.
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import Dict, List
from pathlib import Path
from core.models import JobPosting
from config import (
    GMAIL_USER,
    GMAIL_APP_PASSWORD,
    ALERT_RECIPIENT,
    DEV_CATEGORIES,
    BASE_DIR,
)

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self, template_path: Path = BASE_DIR / "templates" / "email_digest.html"):
        self.template_path = template_path

    def render_digest(self, categorized_jobs: Dict[str, List[JobPosting]]) -> str:
        """Generates the full HTML email string from categorized jobs."""
        now = datetime.now()
        date_str = now.strftime("%A, %b %d, %Y")
        total_jobs = sum(len(jobs) for jobs in categorized_jobs.values())

        if not self.template_path.exists():
            raise FileNotFoundError(f"Template not found at {self.template_path}")

        with open(self.template_path, "r", encoding="utf-8") as f:
            template = f.read()

        sections_html = []

        for cat_key, cat_meta in DEV_CATEGORIES.items():
            jobs = categorized_jobs.get(cat_key, [])
            if not jobs:
                continue

            # Section Header
            sec_header = (
                f'<div class="section-title">'
                f'{cat_meta["icon"]} {cat_meta["label"]} '
                f'<span style="margin-left: 8px; font-size: 11px; background: #334155; padding: 2px 8px; border-radius: 10px; color: #94a3b8;">{len(jobs)}</span>'
                f'</div>'
            )
            sections_html.append(sec_header)

            # Job Cards
            for job in jobs:
                skills_html = ""
                if job.matched_skills:
                    tags = "".join(f'<span class="skill-tag">{skill}</span>' for skill in job.matched_skills)
                    skills_html = f'<div class="skills-row">{tags}</div>'

                card = f"""
                <div class="job-card">
                  <div class="job-top">
                    <a href="{job.url}" target="_blank" class="job-title">{job.title}</a>
                    <span class="company-name">{job.company}</span>
                  </div>
                  <div class="badge-row">
                    <span class="badge-match">🔥 {job.match_score}% Match</span>
                    <span class="badge-location">📍 {job.location}</span>
                    <span class="badge-source">🏢 {job.source}</span>
                  </div>
                  {skills_html}
                  <a href="{job.url}" target="_blank" class="apply-btn">Apply on Company Site &rarr;</a>
                </div>
                """
                sections_html.append(card)

        all_sections_str = "\n".join(sections_html)
        if not all_sections_str.strip():
            all_sections_str = '<p style="text-align:center; color:#94a3b8; padding: 40px 0;">No new developer roles matching the filters were found today. Check back tomorrow!</p>'

        html_content = (
            template
            .replace("{{ date_str }}", date_str)
            .replace("{{ total_jobs }}", str(total_jobs))
            .replace("{{ category_sections }}", all_sections_str)
        )

        return html_content

    def send_email(self, subject: str, html_content: str, recipient: str = ALERT_RECIPIENT) -> bool:
        """Sends an HTML email digest via Gmail SMTP (TLS 587)."""
        if not GMAIL_USER or not GMAIL_APP_PASSWORD:
            logger.warning("GMAIL_USER or GMAIL_APP_PASSWORD not set in environment. Skipping email dispatch.")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"Job Alert Bot <{GMAIL_USER}>"
            msg["To"] = recipient

            # Plain text fallback
            plain_text = "Your daily developer job digest is ready. Please view in an HTML-compatible email client."
            msg.attach(MIMEText(plain_text, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            logger.info(f"Connecting to smtp.gmail.com:587 as {GMAIL_USER}...")
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
                server.starttls()
                server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
                server.sendmail(GMAIL_USER, [recipient], msg.as_string())

            logger.info(f"Successfully sent daily job digest email to {recipient}!")
            return True
        except Exception as e:
            logger.error(f"Failed to send email via Gmail SMTP: {e}")
            return False
