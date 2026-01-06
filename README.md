# LinkedIn Job Search Automation

An intelligent job search automation that scrapes LinkedIn job listings, analyzes them using a local LLM against your CV, and produces Excel reports with match scores.

![Uploading image.png…]()

## Features

- **Automated LinkedIn Scraping** - Searches multiple job titles and locations
- **Three-Tier Filtering System**:
  1. Title keyword rejection (instant filter)
  2. Description keyword rejection (content filter)
  3. AI-powered CV matching with scoring (1-10)
- **Local LLM Analysis** - Uses Ollama (no cloud API costs)
- **Excel Reports** - Color-coded results with clickable links
- **Deduplication** - Tracks processed jobs across runs
- **Configurable** - Customize job titles, filters, and scoring thresholds

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LINKEDIN JOB SEARCH AUTOMATION                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐     ┌────────────────────────────────────────┐    │
│  │   WINDOWS    │     │         DOCKER CONTAINER               │    │
│  │    HOST      │     │         (n8n-python)                   │    │
│  │              │     │                                        │    │
│  │ ┌──────────┐ │     │  ┌─────────┐    ┌─────────────────┐   │    │
│  │ │  Ollama  │◄├─────┼──┤   n8n   │───►│ Python Scraper  │   │    │
│  │ │  (GPU)   │ │     │  │Workflow │    │ + Excel Writer  │   │    │
│  │ └──────────┘ │     │  └─────────┘    └─────────────────┘   │    │
│  │   :11434    │     │                                        │    │
│  └──────────────┘     └────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- **Docker Desktop** - For running n8n container
- **Ollama** - Local LLM inference ([ollama.ai](https://ollama.ai))
- **NVIDIA GPU** (optional) - For faster LLM inference

## Quick Start

### 1. Clone and Configure

```bash
git clone https://github.com/yourusername/linkedin-job-search.git
cd linkedin-job-search

# Copy example config and customize
cp config.example.json config.json

# Add your CV
cp /path/to/your/cv.txt data/your_cv.txt
```

### 2. Edit Configuration

Edit `config.json`:
```json
{
  "cv_file": "/data/n8n_linkedin/data/your_cv.txt",
  "job_titles": ["Engineering Manager", "Head of Engineering"],
  "location": "London, UK",
  "time_range": "48h",
  "min_score": 7,
  "ollama_model": "qwen3:8b",
  "ollama_url": "http://host.docker.internal:11434"
}
```

> **Note**: The `ollama_url` uses `host.docker.internal` to allow the Docker container to connect to Ollama running on your host machine.

### 3. Start Services

```bash
# Start Ollama (in separate terminal)
ollama serve

# Pull required model
ollama pull qwen3:8b

# Start n8n container
docker-compose up -d
```

### 4. Run Workflow

1. Open http://localhost:5678
2. Create account (local only)
3. Import `linkedin_job_search.json`
4. Click "Execute Workflow"

### 5. View Results

Results are saved to `output/`:
- `analysis_*.xlsx` - Per-title results
- `ALL_JOBS_*.xlsx` - Merged results with summary

## Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| `cv_file` | Path to your CV (inside container) | Required |
| `job_titles` | List of job titles to search | Required |
| `location` | Search location | `"London, UK"` |
| `time_range` | How recent (`24h`, `48h`, `7d`) | `"48h"` |
| `exclude_in_title` | Auto-reject titles containing these | `[]` |
| `exclude_in_description` | Auto-reject descriptions containing these | `[]` |
| `must_have` | Preferred keywords | `[]` |
| `min_score` | Minimum AI score (1-10) | `7` |
| `max_jobs_per_title` | Limit per job title | `3` |
| `ollama_model` | Ollama model to use | `"qwen3:8b"` |
| `ollama_url` | Ollama server URL (use `host.docker.internal` for Docker) | `"http://host.docker.internal:11434"` |
| `debug_mode` | Verbose logging | `false` |

## Filtering System

### Tier 1: Title Rejection
Instantly rejects jobs with excluded keywords in the title.
```json
"exclude_in_title": ["junior", "intern", "Developer"]
```

### Tier 2: Description Rejection
Rejects jobs with excluded keywords in the description.
```json
"exclude_in_description": ["construction", "hardware", "embedded"]
```

### Tier 3: AI Analysis
Remaining jobs are analyzed by Ollama against your CV:
- **9-10**: Perfect match
- **7-8**: Good match (saved)
- **5-6**: Partial match
- **1-4**: Poor match (rejected)

## Output Format

Excel files include:
- **TIMESTAMP** - When processed
- **SEARCH TITLE** - Original search query
- **JOB TITLE** - Actual job title
- **COMPANY** - Company name
- **LINK** - Clickable link to job posting
- **DECISION** - MATCHED / REJECTED_TITLE / REJECTED_DESC / REJECTED_AI
- **REASON** - Why matched or rejected
- **SCORE** - AI score (1-10)

Color coding:
- 🟢 Green: Matched
- 🔴 Pink: Rejected (title/description)
- 🟠 Orange: Rejected (AI)
- ⚪ Gray: Skipped (duplicate)

## Project Structure

```
linkedin-job-search/
├── config.example.json      # Template configuration
├── config.json              # Your configuration (git-ignored)
├── docker-compose.yml       # Docker setup
├── Dockerfile               # Custom n8n image with Python
├── linkedin_job_search.json # n8n workflow
├── data/
│   ├── cv_example.txt       # CV template
│   └── your_cv.txt          # Your CV (git-ignored)
├── output/                  # Generated reports (git-ignored)
└── python/
    ├── jobs_scraper.py      # LinkedIn scraper
    └── excel_writer.py      # Excel report generator
```

## Manual Scraper Usage

Run the scraper directly without n8n:

```bash
cd python

# Basic usage
python jobs_scraper.py -k "Engineering Manager" -l "London, UK" -n 20 -t 48h

# Dry run (no requests)
python jobs_scraper.py -k "Test" -l "London" -n 1 --dry-run
```

## Troubleshooting

### Ollama Connection Refused
```bash
# Ensure Ollama is running
ollama serve

# Verify
curl http://localhost:11434/api/tags
```

### Docker Container Issues
```bash
# Rebuild container
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# View logs
docker logs n8n-python
```

### Ollama Not Using GPU
```bash
# Windows: Set GPU environment variable
setx OLLAMA_NUM_GPU 999

# Restart Ollama
taskkill /IM ollama.exe /F
ollama serve

# Verify GPU usage
nvidia-smi
```

### n8n Can't Connect to Ollama
The workflow uses `http://host.docker.internal:11434` which lets Docker containers access host services.
- Ensure Ollama is running on the host (not in Docker)
- Verify Ollama is listening: `curl http://localhost:11434/api/tags`
- Check `ollama_url` in config.json uses `host.docker.internal` (not `localhost`)

### Python Scraper Fails in n8n
```bash
# Check Python is available in Docker container
docker exec -it n8n-python python3 --version

# Test scraper manually inside container
docker exec -it n8n-python sh -c "cd /data/n8n_linkedin/python && python3 jobs_scraper.py -k 'Test' -l 'London' -n 1 --dry-run"
```

### Workflow Timeout
- Increase timeout in HTTP Request nodes (default 300000ms = 5 min)
- Use a faster Ollama model (e.g., `gemma2:2b` instead of `qwen3:8b`)

## Quick Reference Commands

```bash
# Start everything (run in order):
# 1. Docker Desktop (from Start Menu)
# 2. Ollama (from system tray or: ollama serve)
# 3. n8n container:
docker-compose up -d

# Stop everything:
docker-compose down
taskkill /IM ollama.exe /F      # Windows
# pkill ollama                  # Linux/Mac

# Check what's running:
docker ps                              # Shows n8n container
curl http://localhost:11434/api/tags   # Shows Ollama models
nvidia-smi                             # Shows GPU usage

# View logs:
docker logs n8n-python
```

## Docker Volume Mapping

The project directory is mounted into the container:
- **Host**: `./` (project root)
- **Container**: `/data/n8n_linkedin`

This means:
- Config paths use `/data/n8n_linkedin/...` (container path)
- Output files appear in your local `output/` folder
- Python scripts run from `/data/n8n_linkedin/python/`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Disclaimer

This tool is for personal job search automation only. Please:
- Respect LinkedIn's Terms of Service
- Use reasonable rate limits
- Don't use for commercial scraping

## License

MIT License - see [LICENSE](LICENSE) file.
