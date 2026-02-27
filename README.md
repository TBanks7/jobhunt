# 🇨🇦 Job Application Automator

Automatically scrapes Canadian tech jobs daily, tailors your resume and cover letter
using Claude AI, and logs everything to Notion + CSV.

---

## Project Structure

```
job_automator/
├── main.py              # Orchestrator + scheduler
├── scraper.py           # JobSpy multi-platform scraping
├── generator.py         # Claude tailors resume + cover letter
├── compiler.py          # LaTeX → PDF, DOCX → PDF
├── tracker.py           # Notion + CSV logging
├── config.py            # All settings (edit this first)
├── setup_notion.py      # One-time Notion DB setup
├── requirements.txt
├── templates/
│   ├── resume.tex       # ← PUT YOUR RESUME HERE
│   └── cover_letter.docx  # ← PUT YOUR COVER LETTER TEMPLATE HERE
├── output/              # Generated per-job folders (auto-created)
└── applied_jobs.csv     # Local dedup tracker (auto-created)
```

---

## Setup (do this once)

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Install LaTeX (for resume PDF compilation)
- Download and install **MiKTeX**: https://miktex.org/download
- During install, choose "Install missing packages on-the-fly: Yes"
- Make sure `pdflatex` is available in your PATH
- Copy your `resume.cls` class file into `templates/` if it's custom

### 3. Install LibreOffice (for cover letter DOCX → PDF)
- Download: https://www.libreoffice.org/download/download/
- Alternatively, if you have Microsoft Word: `pip install docx2pdf`

### 4. Get your API keys

#### Anthropic (Claude)
1. Go to https://console.anthropic.com/
2. Create an API key
3. Paste it in `config.py` → `ANTHROPIC_API_KEY`

#### Notion
1. Go to https://www.notion.so/my-integrations
2. Click "New integration" → give it a name → Submit
3. Copy the "Internal Integration Secret" key
4. Paste in `config.py` → `NOTION_API_KEY`

### 5. Set up Notion database
1. Open Notion, create a new blank **page** (not database)
2. Click Share (top right) → Invite → select your integration
3. Copy the page ID from the URL:
   `https://notion.so/My-Page-abc123def456` → ID = `abc123def456`
4. Open `setup_notion.py` and paste the ID into `PARENT_PAGE_ID`
5. Run:
   ```bash
   python setup_notion.py
   ```
6. Copy the printed `Database ID` into `config.py` → `NOTION_DATABASE_ID`

### 6. Add your templates
- Copy your `resume.tex` into `templates/resume.tex`
- Copy your `cover_letter.docx` into `templates/cover_letter.docx`

#### Cover letter DOCX placeholders
Add these anywhere in your cover letter template:
```
{{DATE}}               → Today's date
{{COMPANY}}            → Company name
{{ROLE}}               → Job title
{{COVER_LETTER_BODY}}  → Claude's generated paragraphs
```

---

## Running

### Test immediately
```bash
python main.py --now
```

### Run on schedule (keeps terminal open)
```bash
python main.py
```
Runs every day at 9:00 AM (configurable in `config.py` → `RUN_TIME`).

### Windows Task Scheduler (recommended — no terminal needed)
1. Open Task Scheduler → Create Basic Task
2. Name: "Job Automator"
3. Trigger: Daily at 9:00 AM
4. Action: Start a program
   - Program: `C:\Python312\python.exe` (your Python path)
   - Arguments: `main.py --now`
   - Start in: `C:\path\to\job_automator`
5. Finish

---

## What it does each day

```
9:00 AM
  ↓
Scrape LinkedIn, Indeed, Glassdoor for last 24hrs
  ↓
Filter: Canada/Remote only, ≤5 years experience, no senior roles
  ↓
Skip jobs already in CSV tracker
  ↓
For each new job:
  → Claude edits resume.tex to match the job description
  → Claude writes a tailored cover letter body
  → Compiles resume.tex → resume.pdf
  → Fills cover_letter.docx → cover_letter.pdf
  → Logs to applied_jobs.csv + Notion (status: "Ready to Apply")
  → Opens job URL in your browser
  ↓
You review and submit manually
  ↓
Update status to "Applied" in Notion
```

---

## Output example

```
output/
└── Shopify_Backend_Engineer_20250215_0902/
    ├── resume.pdf
    ├── resume.tex
    ├── cover_letter.pdf
    ├── cover_letter.docx
    └── keyword_report.txt
```

---

## Customisation

- **Add/remove job titles**: edit `SEARCH_QUERIES` in `config.py`
- **Change locations**: edit `SEARCH_LOCATIONS` in `config.py`
- **Change experience cap**: edit `MAX_YEARS_EXPERIENCE` in `config.py`
- **Change Claude model**: edit `CLAUDE_MODEL` in `config.py`
- **Update your profile**: edit `CANDIDATE_PROFILE` in `config.py`

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `pdflatex not found` | Install MiKTeX, restart terminal |
| `resume.cls not found` | Copy your .cls file into `templates/` |
| DOCX → PDF fails | Install LibreOffice or Word + docx2pdf |
| Notion 401 error | Check NOTION_API_KEY; share parent page with integration |
| No jobs scraped | JobSpy may be rate-limited; try again or reduce RESULTS_PER_QUERY |
| Jobs missing descriptions | LinkedIn requires `linkedin_fetch_description=True` (already set) |
