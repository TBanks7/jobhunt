# =============================================================================
# tracker.py — CSV + Notion job tracking and deduplication
# =============================================================================

import logging
import os
from datetime import datetime
from typing import Optional

import pandas as pd
from notion_client import Client

from config import (
    NOTION_API_KEY, NOTION_DATABASE_ID, CSV_TRACKER
)

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CSV Tracker
# ---------------------------------------------------------------------------

CSV_COLUMNS = [
    "job_url", "title", "company", "location", "site",
    "date_posted", "scraped_at", "applied_at", "status",
    "resume_path", "cover_letter_path", "notion_page_id", "notes"
]


def _load_csv() -> pd.DataFrame:
    """Load the CSV tracker, creating it if it doesn't exist."""
    if os.path.exists(CSV_TRACKER):
        df = pd.read_csv(CSV_TRACKER, dtype=str)
        # Ensure all expected columns exist
        for col in CSV_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df
    else:
        df = pd.DataFrame(columns=CSV_COLUMNS)
        df.to_csv(CSV_TRACKER, index=False)
        log.info(f"Created new CSV tracker at {CSV_TRACKER}")
        return df


def _save_csv(df: pd.DataFrame):
    df.to_csv(CSV_TRACKER, index=False)


def is_already_tracked(job_url: str) -> bool:
    """Return True if this job URL is already in the CSV tracker."""
    df = _load_csv()
    return job_url in df["job_url"].values


def filter_new_jobs(jobs_df: pd.DataFrame) -> pd.DataFrame:
    """Remove jobs already in the CSV tracker. Returns only new jobs."""
    if jobs_df.empty:
        return jobs_df
    tracked = _load_csv()
    tracked_urls = set(tracked["job_url"].dropna().values)
    new = jobs_df[~jobs_df["job_url"].isin(tracked_urls)].copy()
    skipped = len(jobs_df) - len(new)
    if skipped:
        log.info(f"Skipping {skipped} already-tracked jobs")
    log.info(f"{len(new)} new jobs to process")
    return new


def log_job_to_csv(
    job: dict,
    status: str = "Ready to Apply",
    resume_path: str = "",
    cover_letter_path: str = "",
    notion_page_id: str = "",
):
    """Add or update a job entry in the CSV tracker."""
    df = _load_csv()

    # If URL already exists, update status
    if job.get("job_url") in df["job_url"].values:
        idx = df[df["job_url"] == job["job_url"]].index[0]
        df.at[idx, "status"] = status
        df.at[idx, "resume_path"] = resume_path
        df.at[idx, "cover_letter_path"] = cover_letter_path
        if notion_page_id:
            df.at[idx, "notion_page_id"] = notion_page_id
    else:
        new_row = {
            "job_url":            job.get("job_url", ""),
            "title":              job.get("title", ""),
            "company":            job.get("company", ""),
            "location":           job.get("location", ""),
            "site":               job.get("site", ""),
            "date_posted":        str(job.get("date_posted", "")),
            "scraped_at":         job.get("scraped_at", datetime.now().isoformat()),
            "applied_at":         "",
            "status":             status,
            "resume_path":        resume_path,
            "cover_letter_path":  cover_letter_path,
            "notion_page_id":     notion_page_id,
            "notes":              "",
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    _save_csv(df)
    log.info(f"CSV updated: {job.get('company')} — {job.get('title')} [{status}]")


# ---------------------------------------------------------------------------
# Notion Tracker
# ---------------------------------------------------------------------------

def _get_notion_client() -> Client:
    return Client(auth=NOTION_API_KEY)


def create_notion_page(
    job: dict,
    status: str = "Ready to Apply",
    resume_path: str = "",
    cover_letter_path: str = "",
) -> Optional[str]:
    """
    Create a new page in the Notion job tracker database.
    Returns the page ID on success, None on failure.

    Expected Notion DB properties:
      - Job Title (title)
      - Company (rich_text)
      - Location (rich_text)
      - Status (select): Ready to Apply | Applied | Interview | Offer | Rejected
      - Platform (select): linkedin | indeed | glassdoor | zip_recruiter
      - Job URL (url)
      - Date Posted (date)
      - Applied At (date)
      - Resume Path (rich_text)
      - Cover Letter Path (rich_text)
      - Notes (rich_text)
    """
    try:
        notion = _get_notion_client()

        date_posted = job.get("date_posted")
        date_str = None
        if date_posted and str(date_posted) not in ("None", "NaT", "nan", ""):
            try:
                # Try to parse various formats
                date_str = pd.to_datetime(str(date_posted)).strftime("%Y-%m-%d")
            except Exception:
                date_str = None

        properties = {
            "Job Title": {
                "title": [{"text": {"content": str(job.get("title", ""))}}]
            },
            "Company": {
                "rich_text": [{"text": {"content": str(job.get("company", ""))}}]
            },
            "Location": {
                "rich_text": [{"text": {"content": str(job.get("location", ""))}}]
            },
            "Status": {
                "select": {"name": status}
            },
            "Platform": {
                "select": {"name": str(job.get("site", "unknown"))}
            },
            "Job URL": {
                "url": str(job.get("job_url", "")) or None
            },
            "Resume Path": {
                "rich_text": [{"text": {"content": resume_path}}]
            },
            "Cover Letter Path": {
                "rich_text": [{"text": {"content": cover_letter_path}}]
            },
        }

        if date_str:
            properties["Date Posted"] = {"date": {"start": date_str}}

        page = notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties=properties,
        )
        page_id = page["id"]
        log.info(f"Notion page created: {job.get('company')} — {job.get('title')} (ID: {page_id})")
        return page_id

    except Exception as e:
        log.error(f"Failed to create Notion page for {job.get('company')}: {e}")
        return None


def update_notion_status(page_id: str, status: str, applied_at: str = ""):
    """Update the status of an existing Notion page."""
    try:
        notion = _get_notion_client()
        props = {"Status": {"select": {"name": status}}}
        if applied_at:
            props["Applied At"] = {"date": {"start": applied_at}}
        notion.pages.update(page_id=page_id, properties=props)
        log.info(f"Notion page {page_id} updated to '{status}'")
    except Exception as e:
        log.error(f"Failed to update Notion page {page_id}: {e}")


# ---------------------------------------------------------------------------
# Combined log function
# ---------------------------------------------------------------------------

def track_job(
    job: dict,
    status: str = "Ready to Apply",
    resume_path: str = "",
    cover_letter_path: str = "",
):
    """Log a job to both CSV and Notion. Returns notion_page_id."""
    notion_page_id = create_notion_page(
        job, status=status,
        resume_path=resume_path,
        cover_letter_path=cover_letter_path
    )
    log_job_to_csv(
        job, status=status,
        resume_path=resume_path,
        cover_letter_path=cover_letter_path,
        notion_page_id=notion_page_id or "",
    )
    return notion_page_id
