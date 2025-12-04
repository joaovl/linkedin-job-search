# LinkedIn Job Search Automation

## QUICK START - Run After Reboot

Follow these steps IN ORDER after restarting your laptop.

---

### Step 1: Start Docker Desktop

1. Open **Docker Desktop** from Start Menu or system tray
2. Wait until Docker Desktop shows "Running" (green icon in system tray)
3. If Docker doesn't start automatically, you may need to wait 1-2 minutes after login

**Verify Docker is running:**
```powershell
docker ps
```
Should show an empty list or running containers (no errors).

---

### Step 2: Start Ollama with GPU

**Option A: Using Ollama System Tray App (Recommended)**
1. Click the Ollama icon in system tray
2. It should start automatically on boot
3. Verify it's running: open http://localhost:11434 in browser - should show "Ollama is running"

**Option B: Using PowerShell**
```powershell
# Open PowerShell and run:
ollama serve
```
Keep this window open while using the automation.

**First-time GPU setup (only needed once):**
```powershell
# Run this ONCE to enable GPU permanently:
setx OLLAMA_NUM_GPU 999

# Then RESTART PowerShell and run ollama serve again
```

**Verify GPU is being used:**
```powershell
# In a separate PowerShell window:
nvidia-smi

# Look for "ollama" or "ollama_llama_server" in the processes list
# It should show GPU memory being used (e.g., 4000MiB)
```

---

### Step 3: Start n8n Container

```powershell
cd C:\automations\n8n_linkedin
docker-compose up -d
```

**Expected output:**
```
[+] Running 1/1
 ✔ Container n8n-python  Started
```

**Verify n8n is running:**
```powershell
docker ps
```
Should show `n8n-python` container running on port 5678.

**If container doesn't exist yet (first time or after rebuild):**
```powershell
cd C:\automations\n8n_linkedin
docker-compose build
docker-compose up -d
```

---

### Step 4: Open n8n and Import Workflow

1. Open browser: **http://localhost:5678**
2. If first time:
   - Create an account (local only, any email/password works)
   - Click "Import from File"
   - Select `C:\automations\n8n_linkedin\linkedin_job_search_local.json`
3. If workflow already exists, open it from the list

---

### Step 5: Run the Workflow

1. Open workflow: **"LinkedIn Job Search - Local JSON (Ollama)"**
2. Click the **"Test Workflow"** or **"Execute Workflow"** button
3. Watch the execution - each node will light up as it runs
4. For daily automation, toggle the workflow to "Active"

---

### Step 6: View Results

Results are saved to timestamped JSON files:
```
C:\automations\n8n_linkedin\output\
├── matches_YYYY-MM-DDTHH-MM-SS.json   # Good job matches with cover letters
└── rejected_YYYY-MM-DDTHH-MM-SS.json  # Filtered out jobs
```

Open with VS Code, Notepad++, or any JSON viewer.

---

## Troubleshooting

### "Cannot connect to Docker daemon"
- Docker Desktop is not running
- Start Docker Desktop and wait for it to fully load

### "Ollama connection refused" in n8n
- Ollama is not running on Windows
- Start Ollama: `ollama serve` or via system tray
- Verify: http://localhost:11434 should show "Ollama is running"

### "Container n8n-python not found"
```powershell
cd C:\automations\n8n_linkedin
docker-compose build
docker-compose up -d
```

### Ollama not using GPU
```powershell
# Check if GPU variable is set:
echo %OLLAMA_NUM_GPU%

# If empty, set it:
setx OLLAMA_NUM_GPU 999

# Restart PowerShell, then restart Ollama
taskkill /IM ollama.exe /F
ollama serve
```

### Workflow not in n8n
Re-import from: `C:\automations\n8n_linkedin\linkedin_job_search_local.json`

---

## Quick Reference Commands

```powershell
# Start everything (run in order):
# 1. Docker Desktop (from Start Menu)
# 2. Ollama (from system tray or: ollama serve)
# 3. n8n container:
cd C:\automations\n8n_linkedin
docker-compose up -d

# Stop everything:
docker-compose down
taskkill /IM ollama.exe /F

# Check what's running:
docker ps                              # Shows n8n container
curl http://localhost:11434/api/tags   # Shows Ollama models
nvidia-smi                             # Shows GPU usage

# View logs:
docker logs n8n-python                 # n8n logs
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LINKEDIN JOB SEARCH AUTOMATION                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     ┌──────────────────────────────────────────────────┐  │
│  │   WINDOWS    │     │              DOCKER CONTAINER                     │  │
│  │    HOST      │     │              (n8n-python)                         │  │
│  │              │     │                                                   │  │
│  │ ┌──────────┐ │     │  ┌─────────┐    ┌─────────┐    ┌──────────────┐  │  │
│  │ │  Ollama  │◄├─────┼──┤   n8n   │───►│ Python  │───►│ LinkedIn     │  │  │
│  │ │  (GPU)   │ │     │  │Workflow │    │Scraper  │    │ (Public API) │  │  │
│  │ │          │ │     │  └────┬────┘    └─────────┘    └──────────────┘  │  │
│  │ │Qwen2.5   │ │     │       │                                          │  │
│  │ └──────────┘ │     │       ▼                                          │  │
│  │    :11434    │     │  ┌─────────┐                                     │  │
│  │              │     │  │  CSV    │ ──► /data/n8n_linkedin/results.csv  │  │
│  │              │     │  │ Output  │ ──► /data/n8n_linkedin/rejected.csv │  │
│  │              │     │  └─────────┘                                     │  │
│  │              │     │                                                   │  │
│  │  C:\automations\n8n_linkedin ◄──────► /data/n8n_linkedin (volume)    │  │
│  │              │     │                                                   │  │
│  └──────────────┘     └──────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

WORKFLOW FLOW:
┌──────────┐   ┌────────────┐   ┌─────────────┐   ┌───────────────┐
│ Trigger  │──►│ Read       │──►│ Split Job   │──►│ Run Python    │
│ (Manual/ │   │ Config.json│   │ Titles      │   │ Scraper       │
│  9AM)    │   └────────────┘   └─────────────┘   └───────┬───────┘
└──────────┘                                              │
                                                          ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                         FOR EACH JOB (Loop)                                │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌───────────────┐  │
│  │ Process One │──►│ Ollama:     │──►│ Parse       │──►│ Filter:       │  │
│  │ at a Time   │   │ Analyze Job │   │ Response    │   │ Relevant?     │  │
│  └──────▲──────┘   └─────────────┘   └─────────────┘   └───────┬───────┘  │
│         │                                                 YES │ │ NO      │
│         │                                                     ▼ ▼         │
│         │         ┌─────────────────────────────────────────────────────┐ │
│         │         │   ┌─────────────┐   ┌─────────────┐                 │ │
│         │         │   │ Ollama:     │──►│ Save to     │                 │ │
│         │         │   │ Cover Letter│   │ results.csv │                 │ │
│         │         │   └─────────────┘   └──────┬──────┘                 │ │
│         │         │                            │                        │ │
│         │         │   ┌─────────────────────────────────────────────┐   │ │
│         │         │   │ Log to rejected.csv                          │   │ │
│         │         │   └──────────────┬──────────────────────────────┘   │ │
│         │         └──────────────────┼──────────────────────────────────┘ │
│         │                            │                                    │
│         └────────────────────────────┘                                    │
│                    (loop back for next job)                               │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## Configuration

Edit `C:\automations\n8n_linkedin\config.json`:

```json
{
  "job_titles": [
    "Engineering Manager",
    "Senior Engineering Manager",
    "Head of Engineering",
    "Head of QA",
    "Director of Engineering",
    "Director of Quality",
    "VP Engineering",
    "Test Manager",
    "QA Manager"
  ],
  "location": "London, UK",
  "time_range": "48h",
  "exclude_keywords": [
    "hands-on coding",
    "electrical engineer",
    "hardware",
    "embedded"
  ],
  "must_have": [
    "team lead",
    "people management",
    "software quality"
  ],
  "min_score": 6,
  "max_jobs_per_title": 20,
  "ollama_model": "Qwen2.5:latest",
  "ollama_url": "http://host.docker.internal:11434"
}
```

### Settings Explained

| Setting | Description | Example |
|---------|-------------|---------|
| `job_titles` | List of job titles to search | `["Engineering Manager", "QA Manager"]` |
| `location` | Search location | `"London, UK"` |
| `time_range` | How far back to search | `"24h"`, `"48h"`, `"7d"` |
| `exclude_keywords` | Auto-reject jobs containing these | `["hardware", "electrical"]` |
| `must_have` | Preferred keywords (for scoring) | `["people management"]` |
| `min_score` | Minimum AI score to save (1-10) | `6` |
| `max_jobs_per_title` | Max jobs to fetch per title | `20` |
| `ollama_model` | Which Ollama model to use | `"Qwen2.5:latest"` |
| `ollama_url` | Ollama server URL | `"http://host.docker.internal:11434"` |

---

## Output Files

Output is saved to `C:\automations\n8n_linkedin\output\` with timestamped filenames.

### matches_YYYY-MM-DDTHH-MM-SS.json
Good job matches with cover letters:
```json
[
  {
    "job": {
      "title": "Engineering Manager",
      "company": "Tech Corp",
      "location": "London, UK",
      "job_link": "https://linkedin.com/jobs/view/123",
      "posted_date": "2 days ago",
      "description": "Full job description..."
    },
    "analysis": {
      "relevant": true,
      "score": 8,
      "company_size": "500-1000 employees",
      "company_industry": "Software/SaaS",
      "company_about": "Cloud platform company...",
      "role_summary": "Lead 3 engineering teams...",
      "match_reasons": ["People management", "Software quality"],
      "concerns": ["Travel required"],
      "seniority_level": "Senior Manager"
    },
    "cover_letter": "Dear Hiring Manager...",
    "metadata": {
      "source": "LinkedIn (via Python scraper)",
      "aiProvider": "Ollama (local)",
      "aiModel": "Qwen2.5:latest",
      "candidateName": "Joao Lourenco",
      "searchTitle": "Engineering Manager",
      "processedAt": "2024-12-03T09:15:30.000Z",
      "status": "matched"
    }
  }
]
```

### rejected_YYYY-MM-DDTHH-MM-SS.json
Filtered out jobs (no cover letter):
```json
[
  {
    "job": {
      "title": "Hardware Engineer",
      "company": "Chip Corp",
      "location": "London",
      "job_link": "https://linkedin.com/jobs/view/456"
    },
    "analysis": {
      "relevant": false,
      "rejection_reason": "Hardware/embedded role - not software",
      "score": 2,
      "company_industry": "Semiconductors"
    },
    "metadata": {
      "source": "LinkedIn (via Python scraper)",
      "aiProvider": "Ollama (local)",
      "aiModel": "Qwen2.5:latest",
      "status": "rejected"
    }
  }
]
```

---

## Troubleshooting

### Ollama not using GPU
```powershell
# Check GPU is detected
nvidia-smi

# Set GPU environment variable
setx OLLAMA_NUM_GPU 999

# Restart Ollama
taskkill /IM ollama.exe /F
ollama serve
```

### Docker container won't start
```powershell
# Rebuild the container
cd C:\automations\n8n_linkedin
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### n8n can't connect to Ollama
The workflow uses `http://host.docker.internal:11434` which lets Docker containers access host services.
- Make sure Ollama is running on Windows (not in Docker)
- Check Ollama is listening: `curl http://localhost:11434/api/tags`

### Python scraper fails
```powershell
# Check Python is in Docker container
docker exec -it n8n-python python3 --version

# Test scraper manually
docker exec -it n8n-python sh -c "cd /data/n8n_linkedin/python && python3 jobs_scraper.py -k 'Test' -l 'London' -n 1 --dry-run"
```

### Workflow timeout
- Increase timeout in HTTP Request nodes (currently 300000ms = 5 min)
- Use a faster Ollama model (e.g., `gemma3:4b` instead of `Qwen2.5:latest`)

---

## Stopping Everything

```powershell
# Stop Docker
cd C:\automations\n8n_linkedin
docker-compose down

# Stop Ollama
taskkill /IM ollama.exe /F
```

---

## File Structure

```
C:\automations\n8n_linkedin\
├── config.json                    # Configuration settings
├── docker-compose.yml             # Docker setup for n8n
├── Dockerfile                     # Custom n8n image with Python
├── linkedin_job_search_local.json # Main workflow (import to n8n)
├── README_linkedin_job_search.md  # This file
├── output/                        # Generated output files
│   ├── matches_2024-12-03T09-00-00.json
│   └── rejected_2024-12-03T09-00-00.json
└── python/
    ├── jobs_scraper.py            # LinkedIn scraper
    ├── server.py                  # Optional: web viewer
    └── jobs_viewer.html           # Optional: web UI
```

---

## AI Scoring Criteria

Jobs are scored 1-10 based on Joao's CV:

| Score | Meaning |
|-------|---------|
| 10 | Perfect - EM/Director, safety-critical industry, team scaling |
| 8-9 | Strong - EM role, software, people management, quality focus |
| 6-7 | Good - Management role, software industry, skill overlap |
| 4-5 | Partial - Some relevant aspects |
| 1-3 | Poor - Mostly misaligned |
| 0 | Auto-rejected (hardware, electrical, IC coding) |

### Auto-Rejection Rules
- Electrical engineering / hardware / embedded
- Mechanical or civil engineering
- Hands-on individual contributor coding roles
- Junior or mid-level positions
- Non-software industries

---

## Alternative Approaches (Reference)

This folder also contains example workflows for other approaches:

| File | Method | Cost |
|------|--------|------|
| `example1.json` | RSS feeds + OpenAI | RSS.app + OpenAI API |
| `example2.json` | Bright Data API | Bright Data subscription |

See sections below for details on these alternatives.

---

## Appendix: RSS Feed + OpenAI Approach (example1.json)

### How It Works
1. Schedule Trigger - Runs daily
2. RSS Feeds - Reads from RSS.app feeds monitoring LinkedIn
3. HTTP Request - Fetches full job page
4. OpenAI - Extracts data, scores job, generates cover letter
5. Google Sheets - Saves results

### Requirements
- RSS.app account
- OpenAI API key
- Google Sheets OAuth

---

## Appendix: Bright Data API Approach (example2.json)

### How It Works
1. Form Trigger - User submits search criteria
2. Bright Data API - Scrapes LinkedIn data
3. Google Sheets - Saves results

### Requirements
- Bright Data account + API token
- Google Sheets OAuth

---

## Appendix: Python Scraper Direct Usage

```bash
# Run scraper directly (not through n8n)
cd C:\automations\n8n_linkedin\python

# Basic usage
python jobs_scraper.py -k "Engineering Manager" -l "London, UK" -n 20 -t 48h

# Fast mode (no descriptions)
python jobs_scraper.py -k "Product Manager" -l "Remote" --no-description

# View results in browser
python server.py
# Open http://localhost:5000
```

---

*Last updated: December 2024*
