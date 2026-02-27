# =============================================================================
# scraper.py — JobSpy multi-platform scraper with experience-level filtering
# =============================================================================

import re
import logging
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
from jobspy import scrape_jobs

from config import (
    SEARCH_QUERIES, SEARCH_LOCATIONS, SEARCH_PLATFORMS,
    HOURS_OLD, RESULTS_PER_QUERY, MAX_YEARS_EXPERIENCE,
    SENIOR_KEYWORDS, JUNIOR_KEYWORDS
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_years_required(text: str) -> Optional[int]:
    """
    Parse the maximum years of experience mentioned in a job description.
    Returns the highest number found in patterns like '5 years', '3+ years', '2-4 years'.
    Returns None if no pattern found.
    """
    if not text:
        return None
    # Patterns: "5 years", "5+ years", "3-5 years" (we take the upper bound)
    patterns = [
        r'(\d+)\+?\s*(?:to|-)\s*(\d+)\s*years?',  # range: 3-5 years → 5
        r'(\d+)\+\s*years?',                         # 5+ years → 5
        r'(\d+)\s*years?\s*(?:of)?\s*experience',   # 5 years of experience → 5
    ]
    max_years = None
    for pat in patterns:
        for match in re.finditer(pat, text, re.IGNORECASE):
            groups = [int(g) for g in match.groups() if g is not None]
            found = max(groups)
            if max_years is None or found > max_years:
                max_years = found
    return max_years


def _is_senior_role(title: str, description: str) -> bool:
    """Return True if the role appears to be senior/lead level."""
    combined = f"{title} {description}".lower()
    return any(kw in combined for kw in SENIOR_KEYWORDS)


def _is_junior_role(title: str, description: str) -> bool:
    """Return True if the role appears to target junior/intermediate candidates."""
    combined = f"{title} {description}".lower()
    return any(kw in combined for kw in JUNIOR_KEYWORDS)


def _passes_experience_filter(title: str, description: str) -> bool:
    """
    Return True if the job is likely junior/intermediate (≤ MAX_YEARS_EXPERIENCE).
    Logic:
      1. If any senior keyword found → reject
      2. If years required > MAX_YEARS_EXPERIENCE → reject
      3. Otherwise → accept
    """
    # Reject explicit senior roles
    if _is_senior_role(title, description):
        return False

    years = _extract_years_required(description or "")
    # If a years requirement is present and exceeds our max, normally reject
    if years is not None and years > MAX_YEARS_EXPERIENCE:
        # However, if the posting explicitly uses junior keywords (e.g. "junior", "entry"),
        # treat it as acceptable — some postings list broad ranges but still target junior hires.
        if _is_junior_role(title, description):
            return True
        return False

    return True


def _deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate job postings by job_url, then by (company, title) pair."""
    before = len(df)
    df = df.drop_duplicates(subset=["job_url"], keep="first")
    df = df.drop_duplicates(subset=["company", "title"], keep="first")
    log.info(f"Deduplication: {before} → {len(df)} jobs")
    return df


# ---------------------------------------------------------------------------
# Main scrape function
# ---------------------------------------------------------------------------

def scrape_new_jobs() -> pd.DataFrame:
    """
    Scrape jobs across all configured platforms, queries, and locations.
    Filters to last HOURS_OLD hours and experience level ≤ MAX_YEARS_EXPERIENCE.
    Returns a cleaned DataFrame.
    """
    all_jobs = []
    cutoff = datetime.now() - timedelta(hours=HOURS_OLD)

    for query in SEARCH_QUERIES:
        for location in SEARCH_LOCATIONS:
            log.info(f"Scraping: '{query}' in '{location}'")
            try:
                jobs = scrape_jobs(
                    site_name=SEARCH_PLATFORMS,
                    search_term=query,
                    location=location,
                    results_wanted=RESULTS_PER_QUERY,
                    hours_old=HOURS_OLD,
                    country_indeed="Canada",
                    linkedin_fetch_description=True,  # needed for experience parsing
                )
                if jobs is not None and not jobs.empty:
                    log.info(f"  → {len(jobs)} raw results")
                    all_jobs.append(jobs)
                else:
                    log.info(f"  → 0 results")
            except Exception as e:
                log.warning(f"  → Scrape failed for '{query}' / '{location}': {e}")

    if not all_jobs:
        log.warning("No jobs scraped across all queries/locations.")
        return pd.DataFrame()

    # Combine all results
    df = pd.concat(all_jobs, ignore_index=True)
    log.info(f"Total raw jobs before filtering: {len(df)}")

    # Standardise column names (jobspy may vary slightly)
    df.columns = [c.lower().strip() for c in df.columns]

    # Ensure required columns exist
    for col in ["title", "company", "location", "job_url", "description", "date_posted"]:
        if col not in df.columns:
            df[col] = None

    # --- Filter: experience level ---
    mask = df.apply(
        lambda row: _passes_experience_filter(
            str(row.get("title", "") or ""),
            str(row.get("description", "") or "")
        ),
        axis=1
    )
    df = df[mask].copy()
    log.info(f"After experience filter: {len(df)} jobs")

    # --- Filter: Canada only (belt-and-suspenders) ---
    canada_mask = df["location"].fillna("").str.contains(
        r"canada|ontario|bc|alberta|quebec|british columbia|toronto|vancouver|montreal|calgary|ottawa",
        case=False, regex=True
    )
    # Also keep "Remote" jobs (likely Canada-targeted from Canada search)
    remote_mask = df["location"].fillna("").str.contains("remote", case=False)
    df = df[canada_mask | remote_mask].copy()
    log.info(f"After Canada/Remote filter: {len(df)} jobs")

    # --- Deduplicate ---
    df = _deduplicate(df)

    # --- Junior-match metadata ---
    # Add boolean flag when junior keywords appear in title/description so callers
    # can prioritise or inspect these results.
    df["junior_match"] = df.apply(
        lambda row: _is_junior_role(
            str(row.get("title", "") or ""),
            str(row.get("description", "") or "")
        ),
        axis=1
    )

    # Extract experience-years (if present) into a column for easier downstream use
    df["experience_years"] = df["description"].fillna("").apply(_extract_years_required)

    # --- Add metadata ---
    df["scraped_at"] = datetime.now().isoformat()
    df["status"] = "New"

    # --- Keep only useful columns ---
    keep_cols = [
        "title", "company", "location", "job_url",
        "description", "date_posted", "site",
        "min_amount", "max_amount", "currency",
        "scraped_at", "status",
        "junior_match", "experience_years",
    ]
    existing = [c for c in keep_cols if c in df.columns]
    df = df[existing].reset_index(drop=True)

    log.info(f"Final job count to process: {len(df)}")
    return df


if __name__ == "__main__":
    # Quick test
    jobs = scrape_new_jobs()
    print(jobs[["title", "company", "location", "site"]].to_string())
