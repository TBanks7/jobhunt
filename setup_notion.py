# =============================================================================
# setup_notion.py — One-time script to create the Notion job tracker database
# =============================================================================
#
# Run ONCE before using the main pipeline:
#   python setup_notion.py
#
# Steps:
#   1. Go to https://www.notion.so/my-integrations
#   2. Create a new integration → copy the "Internal Integration Secret" key
#   3. Paste it as NOTION_API_KEY in config.py
#   4. Open Notion → create a blank page (this will be the parent)
#   5. Share that page with your integration (click Share → Invite → your integration)
#   6. Copy the page ID from the URL:
#      https://notion.so/My-Page-abc123def456  →  ID = abc123def456
#   7. Paste the ID as PARENT_PAGE_ID below
#   8. Run this script — it creates the database and prints the DATABASE_ID
#   9. Paste that DATABASE_ID into config.py
#
# =============================================================================

import sys
from notion_client import Client
from config import NOTION_API_KEY

# ⚠️  PASTE YOUR PARENT PAGE ID HERE (the Notion page that will contain the DB)
PARENT_PAGE_ID = "310232bd58978037b539d278aa63afab"


def create_job_tracker_database():
    if PARENT_PAGE_ID == "your-parent-page-id-here":
        print("ERROR: Please set PARENT_PAGE_ID in setup_notion.py before running.")
        sys.exit(1)

    notion = Client(auth=NOTION_API_KEY)

    print("Creating Notion job tracker database...")

    db = notion.databases.create(
        parent={"type": "page_id", "page_id": PARENT_PAGE_ID},
        title=[{"type": "text", "text": {"content": "🇨🇦 Job Applications"}}],
        properties={
            # Primary key — job title
            "Job Title": {"title": {}},

            # Text fields
            "Company":            {"rich_text": {}},
            "Location":           {"rich_text": {}},
            "Resume Path":        {"rich_text": {}},
            "Cover Letter Path":  {"rich_text": {}},
            "Notes":              {"rich_text": {}},

            # URL
            "Job URL": {"url": {}},

            # Selects
            "Status": {
                "select": {
                    "options": [
                        {"name": "Ready to Apply", "color": "blue"},
                        {"name": "Applied",         "color": "yellow"},
                        {"name": "Interview",        "color": "orange"},
                        {"name": "Offer",            "color": "green"},
                        {"name": "Rejected",         "color": "red"},
                        {"name": "Error",            "color": "gray"},
                    ]
                }
            },
            "Platform": {
                "select": {
                    "options": [
                        {"name": "linkedin",      "color": "blue"},
                        {"name": "indeed",        "color": "purple"},
                        {"name": "glassdoor",     "color": "green"},
                        {"name": "zip_recruiter", "color": "orange"},
                        {"name": "unknown",       "color": "gray"},
                    ]
                }
            },

            # Dates
            "Date Posted": {"date": {}},
            "Applied At":  {"date": {}},
        }
    )

    db_id = db["id"]
    print("\n✅ Notion database created successfully!")
    print(f"\nDatabase ID: {db_id}")
    print(f"\n👉 Copy this ID and paste it as NOTION_DATABASE_ID in config.py")
    print(f"\nYou can view your database at:")
    print(f"   https://www.notion.so/{db_id.replace('-', '')}")

    return db_id


if __name__ == "__main__":
    create_job_tracker_database()
