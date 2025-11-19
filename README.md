# AI News Bot - Intelligent News Aggregation System

AI-powered news monitoring that aggregates RSS feeds and Telegram channels, classifies content relevance using AI, and delivers filtered results via Telegram bot and web interface.

## 🚀 Features

- **Multi-Source Aggregation**: RSS feeds and Telegram channels
- **AI Classification**: OpenAI-compatible APIs for relevance evaluation  
- **Custom Tasks**: Personalized news monitoring with custom criteria
- **Telegram Integration**: Filtered news notifications via bot
- **Web Dashboard**: React interface for task management
- **Translation**: DeepL API integration for translation. In current implementation — from English to Russian.
- **Real-time updates (WIP)**: WebSocket notifications and Redis caching — work in progress, not yet implemented.

## � Usage Guide

### 0. Setup
1. Open web interface at http://localhost:8050
2. Go to Setiings. 
3. Add AI API code and Deepl code.

### 1. Creating News Tasks
1. Open web interface at http://localhost:8050
2. Click "Create New Task" 
3. Define monitoring criteria:
   - **Title**: Task name
   - **Description**: Relevance criteria
   - **Examples**: Add relevant/non-relevant samples
   - **Test**: Run relevance criteria against samples to see how it works.

### 2. Managing Sources
1. Go to Settings page
2. Add RSS feeds or Telegram channels
3. Sources are validated automatically

### 3. AI Processing
- News fetched automatically every minute
- AI evaluates against your tasks
- Relevant news sent to Telegram
- Accuracy improves with feedback

## 🚀 Quick Start
Create .env
### Docker
```bash
git clone <repository-url>
cd media-watcher
docker-compose up -d --build
```

### Local Development
```bash
# Install dependencies
make install && make install-frontend

# Configure environment  
cp .env.example .env

# Run migrations and start
make migrate
make dev
```

**Access:**
- Web Interface: http://localhost:8050
- API Docs: http://localhost:8050/api/docs

## ⚙️ Configuration

Create `.env` file with required settings:

```bash
# Core Services
MEDIA_WATCHER_TG_BOT_TOKEN=your_telegram_bot_token
MEDIA_WATCHER_DEEPSEEK=your_deepseek_api_key
MEDIA_WATCHER_DEEPL=your_deepl_api_key

# Authentication
MEDIA_WATCHER_USERS_SECRET=your_jwt_secret_key
MEDIA_WATCHER_ADMIN_EMAIL=admin@example.com
MEDIA_WATCHER_ADMIN_PASSWORD=secure_password

# Database & Cache
MEDIA_WATCHER_DB_FILE=./media_watcher.db
MEDIA_WATCHER_REDIS_HOST=localhost
MEDIA_WATCHER_REDIS_PORT=6379

# Logging (Optional - Grafana Cloud)
MEDIA_WATCHER_LOKI_URL=https://logs-prod-XXX.grafana.net
MEDIA_WATCHER_LOKI_USER=123456
MEDIA_WATCHER_LOKI_API_KEY=glc_xxxxxxxxxxxxx

# Application  
MEDIA_WATCHER_HOST=0.0.0.0
MEDIA_WATCHER_PORT=8050
MEDIA_WATCHER_CORS_ORIGINS=["http://localhost:3000"]
```


## 🔧 Technical Stack

- **Backend**: FastAPI, SQLAlchemy, Redis, OpenAI API
- **Frontend**: React, TypeScript, Chakra UI
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **AI**: DeepSeek API for classification, DeepL for translation
- **Logging**: Grafana Cloud Loki (optional, for centralized log management)
- **Deployment**: Docker, Docker Compose

## 🐛 Notes

As for now, it's a one-user system, user is created on startup with .env login details. 

Redis isn't implemented. 


## 📄 License

MIT License - Built with FastAPI, React, and AI technologies