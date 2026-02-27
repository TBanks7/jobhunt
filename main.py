# =============================================================================
# main.py — Orchestrator: runs the full pipeline on schedule
# =============================================================================
#
# Usage:
#   python main.py          → runs on schedule (daily at RUN_TIME in config.py)
#   python main.py --now    → run immediately (for testing)
#
# Windows Task Scheduler setup (alternative to keeping this running):
#   Action: python C:\path\to\job_automator\main.py --now
#   Trigger: Daily at 9:00 AM
#   Working directory: C:\path\to\job_automator
#
# =============================================================================

import argparse
import logging
import sys
import webbrowser
from datetime import datetime

import schedule
import time

from config import RUN_TIME
from scraper import scrape_new_jobs
from tracker import filter_new_jobs, track_job
from generator import generate_application_docs
from compiler import compile_all

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("job_automator.log", encoding="utf-8"),
    ]
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------

def run_pipeline():
    """
    Full job automation pipeline:
      1. Scrape new jobs
      2. Filter already-tracked jobs
      3. For each new job: generate tailored resume + cover letter
      4. Compile to PDF
      5. Log to CSV + Notion
      6. Open application URLs in browser
    """
    start = datetime.now()
    log.info("=" * 60)
    log.info(f"Job automation pipeline started at {start.strftime('%Y-%m-%d %H:%M')}")
    log.info("=" * 60)

    # Step 1: Scrape
    jobs_df = scrape_new_jobs()
    if jobs_df.empty:
        log.info("No jobs found today. Pipeline complete.")
        return

    # Step 2: Filter already-tracked
    new_jobs_df = filter_new_jobs(jobs_df)
    if new_jobs_df.empty:
        log.info("All scraped jobs already tracked. Nothing to process.")
        return

    log.info(f"Processing {len(new_jobs_df)} new jobs...")

    results = []
    for idx, row in new_jobs_df.iterrows():
        job = row.to_dict()
        company = job.get("company", "Unknown")
        title   = job.get("title", "Unknown")

        log.info(f"\n--- [{idx+1}/{len(new_jobs_df)}] {company} — {title} ---")

        try:
            # Step 3: Generate tailored docs
            paths = generate_application_docs(job)

            # Step 4: Compile to PDF
            paths = compile_all(paths)

            # Step 5: Track in CSV + Notion
            notion_id = track_job(
                job,
                status="Ready to Apply",
                resume_path=paths.get("resume_pdf") or paths.get("resume_tex", ""),
                cover_letter_path=paths.get("cover_letter_pdf") or paths.get("cover_letter_docx", ""),
            )

            results.append({
                "job":       job,
                "paths":     paths,
                "notion_id": notion_id,
                "success":   True,
            })

            log.info(f"✓ Ready: {company} — {title}")
            log.info(f"  Output dir: {paths.get('output_dir')}")
            if paths.get("resume_pdf"):
                log.info(f"  Resume PDF: {paths['resume_pdf']}")
            if paths.get("cover_letter_pdf"):
                log.info(f"  Cover letter PDF: {paths['cover_letter_pdf']}")

        except Exception as e:
            log.error(f"✗ Failed for {company} — {title}: {e}", exc_info=True)
            # Still track it so we don't retry it next run
            track_job(job, status="Error")
            results.append({"job": job, "success": False, "error": str(e)})

    # Step 6: Open application URLs in browser
    # crashes sometimes and is disruptive if you just want to generate docs, so commenting out for now. You can open the URLs manually from the CSV or Notion tracker.

    # successful = [r for r in results if r.get("success")]
    # if successful:
    #     log.info(f"\nOpening {len(successful)} application URLs in browser...")
    #     for r in successful:
    #         url = r["job"].get("job_url", "")
    #         if url:
    #             try:
    #                 webbrowser.open(url)
    #             except Exception as e:
    #                 log.warning(f"Could not open URL {url}: {e}")

    # Summary
    elapsed = (datetime.now() - start).seconds
    log.info("\n" + "=" * 60)
    log.info(f"Pipeline complete in {elapsed}s")
    log.info(f"  Processed: {len(new_jobs_df)} jobs")
    log.info(f"  Success:   {len(successful)}")
    log.info(f"  Failed:    {len(results) - len(successful)}")
    log.info("=" * 60)

    _print_summary_table(successful)


def _print_summary_table(results: list):
    """Print a clean summary of processed jobs."""
    if not results:
        return
    print("\n" + "=" * 80)
    print(f"{'COMPANY':<30} {'TITLE':<35} {'STATUS'}")
    print("-" * 80)
    for r in results:
        job = r["job"]
        print(f"{str(job.get('company','')):<30} {str(job.get('title','')):<35} Ready to Apply")
    print("=" * 80)
    print(f"\nAll documents saved to: output/")
    print("Review, then mark as 'Applied' in your Notion tracker.\n")


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

def start_scheduler():
    """Run the pipeline daily at the configured time."""
    log.info(f"Scheduler started. Pipeline will run daily at {RUN_TIME}.")
    log.info("Keep this terminal open, or use Windows Task Scheduler instead.")
    log.info("Press Ctrl+C to stop.\n")

    schedule.every().day.at(RUN_TIME).do(run_pipeline)

    while True:
        schedule.run_pending()
        time.sleep(30)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Job Application Automator")
    parser.add_argument(
        "--now",
        action="store_true",
        help="Run pipeline immediately instead of waiting for scheduled time"
    )
    args = parser.parse_args()

    if args.now:
        run_pipeline()
    else:
        start_scheduler()
