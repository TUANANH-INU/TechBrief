# QUICK START GUIDE

Get TechBrief running in 5 minutes.

## Prerequisites
- Docker & Docker Compose installed
- ~4GB free RAM
- ~10GB free disk (for models)

## 1. Initial Setup

```bash
cd TechBrief

# Option A: Using CLI tool (recommended)
chmod +x cli.py
./cli.py init

# Option B: Manual setup
cp .env.example .env
docker-compose up -d
docker exec techbrief_ollama ollama pull mistral
```

**What happens:**
- PostgreSQL starts (database)
- Ollama starts (local AI model)
- FastAPI backend starts
- Mistral AI model downloads (5-10 min)

## 2. Verify Installation

```bash
# Using CLI
./cli.py health

# Or manually
curl http://localhost:8000/api/research/health
```

Expected response:
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T...",
  "ollama": "healthy"
}
```

## 3. Run First Research Job

```bash
# Using CLI
./cli.py research

# Or manually
curl -X POST http://localhost:8000/api/research/run-research
```

Monitor progress:
```bash
./cli.py logs backend
```

## 4. View Results

```bash
# Using CLI
./cli.py articles
./cli.py stats

# Or open in browser
http://localhost:8000/docs
```

## Daily Automatic Research

Research runs automatically every day at **09:00 AM** (configurable in `.env`).

Edit `.env` to change schedule:
```env
RESEARCH_SCHEDULE_HOUR=22
RESEARCH_SCHEDULE_MINUTE=30
```

Then restart:
```bash
docker-compose restart backend
```

## Common Commands

```bash
# View logs
./cli.py logs backend
./cli.py logs postgres
./cli.py logs ollama

# View data
./cli.py articles          # Latest articles
./cli.py stats             # Research statistics

# Database access
./cli.py shell-db          # Connect to PostgreSQL

# Model management
./cli.py list-models       # Show installed models
./cli.py pull-model llama2 # Switch to different model

# Clean everything
./cli.py clean

# Stop services
./cli.py stop
```

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /` | API info |
| `GET /api/research/health` | System health |
| `GET /api/research/articles` | All articles |
| `GET /api/research/articles/today` | Today's articles |
| `GET /api/research/articles/processed` | Articles with AI summaries |
| `GET /api/research/stats` | Statistics |
| `POST /api/research/run-research` | Trigger research manually |

**Full API docs:** http://localhost:8000/docs

## Troubleshooting

### Ollama not responding
```bash
./cli.py logs ollama
docker-compose restart ollama
```

### Models too slow
Try a faster model:
```bash
./cli.py pull-model tinyllama
```

Then edit `.env`:
```env
OLLAMA_MODEL=tinyllama
```

### Database issues
```bash
./cli.py shell-db
# OR
docker-compose restart postgres
```

### Free up disk space
```bash
# Remove old images
docker image prune -a

# View model sizes
./cli.py list-models
```

## Next Steps

1. ✅ Installation complete
2. 👀 Browse daily research results at http://localhost:8000/docs
3. 🔧 Customize in `.env` (schedule, model, sources)
4. 📚 Add more news sources in `src/services/news_aggregator.py`
5. 🤖 Modify AI analysis prompts in `src/services/ollama_service.py`

---

Questions? Check README.md for detailed documentation.
