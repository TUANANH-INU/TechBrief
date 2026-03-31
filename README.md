# TechBrief - Research Technical System

**TechBrief** is an autonomous research and information synthesis system designed for AI backend engineers. It aggregates tech news daily, synthesizes insights using local AI models, and provides a REST API for accessing research findings.

## 🎯 Features

✨ **Daily Automated Research with Skill Rotation**
- Automatically runs at scheduled times (default: 09:00 AM)
- Rotates through 15+ technical skills (FastAPI, Kubernetes, Docker, etc.)
- Each day focuses on one skill for targeted research
- Aggregates tech news from multiple sources (Hacker News, Medium, Dev.to)
- Stores findings in PostgreSQL database

📨 **Slack Notifications**
- Daily skill-focused reports sent directly to Slack
- Beautiful formatted messages with top articles
- Configure with your Slack webhook URL
- Automatic report delivery each morning

🤖 **Local AI Synthesis** 
- Uses Ollama with Mistral/Llama2 for local model inference
- Generates intelligent summaries from articles
- Extracts key technical keywords
- No external API calls - fully private

🐳 **Docker-based Self-Serve**
- Everything containerized and ready to deploy
- Single command startup with docker-compose
- Pre-configured PostgreSQL + Ollama + FastAPI backend
- Hot-reload development mode

📊 **REST API**
- Browse aggregated articles
- View AI-generated summaries
- Get research statistics
- Trigger research manually
- Health check endpoints

## ⚡ Quick Start (5 minutes)

See [QUICKSTART.md](QUICKSTART.md) for fastest setup!

```bash
# Clone and setup
cp .env.example .env

# Start all services
docker-compose up -d

# Pull AI model (5-10 min)
docker exec techbrief_ollama ollama pull mistral

# Check health
curl http://localhost:8000/api/research/health

# Access API
open http://localhost:8000/docs
```

Or use the CLI tool:
```bash
./cli.py init
./cli.py health
./cli.py articles
```

## 🏗️ Architecture

```
┌─────────────────┐
│   Hacker News   │
│     Medium      │  → Aggregated daily
│     Dev.to      │
└────────┬────────┘
         │
    ┌────▼────────────────┐
    │  FastAPI Backend    │
    │  (src/main.py)      │
    └────┬─────────┬──────┘
         │         │
    ┌────▼──┐ ┌───▼────────┐
    │Ollama │ │ PostgreSQL │
    │(Local)│ │ (Database) │
    └───────┘ └────────────┘
         │
    ┌────▼──────────┐
    │  REST API     │
    │  (localhost:  │
    │   8000)       │
    └───────────────┘
```

## 📡 API Endpoints

### Research Operations
```bash
# Get latest articles
GET /api/research/articles?limit=20

# Get processed articles with AI summaries
GET /api/research/articles/processed

# Get today's articles
GET /api/research/articles/today

# Get specific article
GET /api/research/articles/{id}

# Get research statistics
GET /api/research/stats

# Trigger research manually
POST /api/research/run-research

# Send test Slack report
POST /api/research/send-slack?skill=FastAPI

# Get research sessions/logs
GET /api/research/sessions
```

### System
```bash
# Health check
GET /api/research/health

# Application status
GET /status

# Root info
GET /
```

**Full API documentation:** http://localhost:8000/docs (Swagger UI)

## ⚙️ Configuration

Edit `.env` to customize:

```env
# Database
DB_NAME=techbrief_db
DB_USER=postgres
DB_PASSWORD=postgres123

# AI Model  
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=mistral        # Change to: llama2, neural-chat, tinyllama, etc.

# Daily Schedule (24-hour format)
RESEARCH_SCHEDULE_HOUR=09
RESEARCH_SCHEDULE_MINUTE=00

# Slack Configuration
SLACK_ENABLED=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
SLACK_CHANNEL=#techbrief

# Logging
LOG_LEVEL=INFO
DEBUG=False
```

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `DB_NAME` | techbrief_db | Database name |
| `DB_USER` | postgres | DB username |
| `DB_PASSWORD` | postgres123 | DB password |
| `OLLAMA_BASE_URL` | http://ollama:11434 | Ollama server address |
| `OLLAMA_MODEL` | mistral | AI model to use |
| `RESEARCH_SCHEDULE_HOUR` | 09 | Daily run hour |
| `RESEARCH_SCHEDULE_MINUTE` | 00 | Daily run minute |
| `SLACK_ENABLED` | false | Enable/disable Slack notifications |
| `SLACK_WEBHOOK_URL` | - | Slack webhook URL for sending messages |
| `SLACK_CHANNEL` | #techbrief | Slack channel for reports |
| `LOG_LEVEL` | INFO | Logging verbosity |

### 📨 Slack Configuration

To enable daily Slack reports for skill-focused research:

**1. Create a Slack App:**
- Go to [api.slack.com/apps](https://api.slack.com/apps)
- Click "Create New App" → "From scratch"
- Give your app a name (e.g., "TechBrief")
- Select your workspace

**2. Enable Incoming Webhooks:**
- In your app settings, go to "Incoming Webhooks"
- Toggle "Activate Incoming Webhooks" to ON
- Click "Add New Webhook to Workspace"
- Select the channel where you want reports (e.g., #techbrief)
- Click "Allow"

**3. Configure in `.env`:**
```env
SLACK_ENABLED=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_CHANNEL=#techbrief
```

**4. Test the integration:**
```bash
# Via API
curl -X POST "http://localhost:8000/api/research/send-slack?skill=FastAPI"

# Via CLI
./cli.py test-slack Kubernetes
```

## 📊 How It Works

### 1. Daily Skill Rotation
Every day, the system selects one technical skill to focus on:
- **15+ Skills**: FastAPI, Kubernetes, Docker, PostgreSQL, Redis, GraphQL, Microservices, AWS, GCP, Azure, Terraform, CI/CD, Monitoring, Optimization, Security
- **Rotation**: Daily schedule cycles through skills (same day = same skill each year)
- **Focus**: Articles are filtered for relevance to today's skill

### 2. Daily Aggregation (Automated)
Every day at configured time:
- **Fetches** RSS feeds from HackerNews, Medium, Dev.to
- **Filters** articles by today's skill
- **Stores** new articles in PostgreSQL 
- **Deduplicates** to avoid re-processing
- Collects ~15-25 articles daily

### 3. AI Processing (Automated)
- **Fetches** article content via web scraping
- **Generates** 2-3 sentence summaries using Ollama
- **Extracts** 3-5 technical keywords
- **Stores** results in database
- One article processing: 2-5 seconds (depends on model)

### 4. Slack Notification (Automated)
If Slack is enabled:
- **Formats** top articles with summaries
- **Includes** today's skill focus
- **Sends** beautiful message to configured Slack channel
- **Happens** immediately after article processing completes

### 5. API Access (On-Demand)
- Query articles by date, source, keywords
- View full summaries and metadata
- Get aggregate statistics
- Manual research trigger

## 🔍 Usage Examples

### Get Today's Articles with Summaries
```bash
curl http://localhost:8000/api/research/articles/today | jq '.[] | {title, summary: .ai_summary_short, keywords}'
```

### Example Response:
```json
{
  "id": 1,
  "source": "hacker_news",
  "title": "Building Production-Ready Technical Systems",
  "url": "https://news.ycombinator.com/item?id=39123456",
  "ai_summary_short": "Article discusses best practices for deploying ML models in production, covering containerization, monitoring, and scaling strategies...",
  "keywords": "backend, ML, deployment, infrastructure",
  "relevance_score": 85,
  "created_at": "2024-01-15T09:05:00Z",
  "processed_at": "2024-01-15T09:12:30Z"
}
```

### Get Research Statistics
```bash
curl http://localhost:8000/api/research/stats | jq .
```

Response:
```json
{
  "total_articles": 156,
  "summarized_count": 145,
  "average_relevance_score": 72.5,
  "top_keywords": [
    "backend",
    "distributed-systems", 
    "kubernetes",
    "microservices",
    "performance"
  ],
  "latest_session_date": "2024-01-15T09:15:30Z",
  "articles_today": 12
}
```

### Trigger Research Manually
```bash
curl -X POST http://localhost:8000/api/research/run-research

# Response:
{
  "message": "Research execution started",
  "session_id": 42,
  "status": "running"
}
```

## 🛠️ CLI Tool

Use `cli.py` for easy management:

```bash
chmod +x cli.py

# First time setup
./cli.py init

# Start/Stop services
./cli.py start
./cli.py stop

# Run research
./cli.py research

# View data
./cli.py articles
./cli.py stats
./cli.py health

# Logs
./cli.py logs backend
./cli.py logs postgres
./cli.py logs ollama

# Model management
./cli.py list-models
./cli.py pull-model llama2

# Database access
./cli.py shell-db

# Slack integration
./cli.py test-slack          # Test with default skill (FastAPI)
./cli.py test-slack Kubernetes  # Test with specific skill

# Cleanup
./cli.py clean
```

## 🔧 Development

### View Logs
```bash
# Backend
docker-compose logs -f backend

# Database
docker-compose logs -f postgres

# Model
docker-compose logs -f ollama
```

### Connect to Database
```bash
docker exec -it techbrief_db psql -U postgres -d techbrief_db

# View articles
SELECT id, title, ai_summary_short FROM research_articles LIMIT 5;

# View sessions
SELECT * FROM research_sessions ORDER BY session_date DESC;
```

### Check Ollama Status
```bash
# List models
docker exec techbrief_ollama ollama list

# View model details
docker exec techbrief_ollama ollama show mistral
```

### Stop Services
```bash
docker-compose down
```

### Full Cleanup (including data)
```bash
docker-compose down -v
```

## 🧪 Testing

### Manual Test Flow
```bash
# 1. Check health
curl http://localhost:8000/api/research/health

# 2. Get initial state
curl http://localhost:8000/api/research/stats | jq '.total_articles'

# 3. Trigger research
curl -X POST http://localhost:8000/api/research/run-research

# 4. Wait 1-2 minutes for processing...

# 5. Check results
curl http://localhost:8000/api/research/articles/today | jq 'length'

# 6. View statistics
curl http://localhost:8000/api/research/stats | jq '.summarized_count'
```

## 🔧 Troubleshooting

### Ollama not responding
```bash
# Check container status
docker ps | grep ollama

# View logs
docker logs techbrief_ollama

# Restart
docker-compose restart ollama

# Test health
curl http://localhost:11434/api/tags
```

### Database connection failed
```bash
# Check PostgreSQL
docker logs techbrief_db

# Verify connection
docker exec techbrief_db pg_isready

# Restart
docker-compose restart postgres
```

### Articles not being processed
```bash
# Check backend logs
docker-compose logs backend | tail -50

# Manually trigger research
curl -X POST http://localhost:8000/api/research/run-research

# Monitor processing
docker-compose logs -f backend

# Check session status
curl http://localhost:8000/api/research/sessions | jq '.[0]'
```

### Model too slow or out of memory
Try a smaller model:
```bash
# Remove current model
docker exec techbrief_ollama ollama rm mistral

# List available models
./cli.py list-models

# Pull smaller model
./cli.py pull-model tinyllama
```

Update `.env`:
```env
OLLAMA_MODEL=tinyllama
```

Restart backend:
```bash
docker-compose restart backend
```

### High disk usage
```bash
# Check Docker disk usage
docker system df

# Clean unused images
docker image prune -a

# Remove all containers and data
docker-compose down -v
docker system prune -a
```

## 🏗️ Project Structure

```
TechBrief/
├── src/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration management  
│   ├── models/              
│   │   ├── database_models.py   # SQLAlchemy ORM models
│   │   ├── database.py          # DB connection & session
│   │   └── schemas.py           # Pydantic API schemas
│   ├── services/
│   │   ├── ollama_service.py    # AI model integration
│   │   ├── news_aggregator.py   # News fetching & processing
│   │   ├── slack_service.py     # Slack webhook integration
│   │   └── skills.py            # Skill rotation system
│   ├── api/
│   │   └── routes.py        # FastAPI routes/endpoints
│   └── schedulers/
│       └── daily_research.py    # APScheduler jobs
│
├── docker-compose.yml       # Container orchestration
├── Dockerfile              # Backend image definition
├── requirements.txt        # Python dependencies
├── .env.example            # Configuration template
├── cli.py                  # Management CLI tool
├── QUICKSTART.md          # 5-minute setup guide
└── README.md              # This file
```

## 📝 Database Schema

### research_articles
```sql
CREATE TABLE research_articles (
  id INT PRIMARY KEY,
  source VARCHAR(50),           -- hacker_news, medium, dev_to
  title VARCHAR(500),           
  url VARCHAR(1000) UNIQUE,
  original_content TEXT,        -- Full article text
  ai_summary TEXT,              -- Full AI summary
  ai_summary_short VARCHAR(500),-- Short version for API
  keywords VARCHAR(500),        -- Comma-separated
  relevance_score INT,          -- 0-100
  is_relevant BOOLEAN,
  created_at TIMESTAMP,
  published_at TIMESTAMP,
  processed_at TIMESTAMP        -- When AI processed it
);
```

### research_sessions
```sql
CREATE TABLE research_sessions (
  id INT PRIMARY KEY,
  session_date TIMESTAMP,
  articles_collected INT,       -- How many fetched
  articles_summarized INT,      -- How many processed
  execution_time_seconds INT,   -- Total time
  status VARCHAR(20),           -- pending, running, completed, failed
  error_message TEXT,
  skill_focus VARCHAR(100)      -- Today's skill (e.g., 'FastAPI', 'Kubernetes')
);
```

## 🤝 Extending the System

### Add New News Source

Edit `src/services/news_aggregator.py`:

```python
@staticmethod
async def fetch_from_my_source(db: Session, limit: int = 10) -> List[ResearchArticle]:
    """Fetch from my custom source"""
    articles = []
    try:
        # Your aggregation logic
        response = requests.get("https://my-source.com/news")
        data = response.json()
        
        for item in data:
            existing = db.query(ResearchArticle).filter(
                ResearchArticle.url == item['url']
            ).first()
            
            if not existing:
                article = ResearchArticle(
                    source="my_source",
                    title=item['title'],
                    url=item['url'],
                )
                articles.append(article)
    except Exception as e:
        logger.error(f"Error: {e}")
    return articles

# Add to aggregate_daily()
my_articles = await NewsAggregator.fetch_from_my_source(db)
articles_to_add.extend(my_articles)
```

### Modify AI Analysis

Edit `src/services/news_aggregator.py` in `process_articles_with_ai()`:

```python
# Change summarization prompt
prompt = f"""Please provide a 1 sentence summary focusing on backend implications:
Text: {text}
Summary:"""

summary = ollama_service.summarize_sync(content, prompt=prompt)
```

Or edit `src/services/ollama_service.py` to customize prompts globally.

### Change Scheduling

Edit `.env`:
```env
RESEARCH_SCHEDULE_HOUR=22      # 10 PM
RESEARCH_SCHEDULE_MINUTE=30
```

Restart:
```bash
docker-compose restart backend
```

## 📄 License

MIT License - Free to use and modify.

## 🚀 Next Steps

1. ✅ **Setup**: `./cli.py init` or follow [QUICKSTART.md](QUICKSTART.md)
2. 📖 **Learn**: Check API docs at http://localhost:8000/docs  
3. 👀 **Browse**: View research results via API or CLI
4. ⚙️ **Customize**: Edit `.env` and sources in `src/services/`
5. 📈 **Monitor**: Check dashboard stats and logs

---

**TechBrief** - Your autonomous AI research assistant, running locally. 🧠✨

For questions or issues, check the troubleshooting section above or review the relevant source files.