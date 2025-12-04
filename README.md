# DraftSensei Mobile Legends Draft Assistant Backend

🎮 **AI-Powered Mobile Legends Draft Assistant** - Smart hero recommendations for optimal team compositions

## Features

- 🧠 **AI Draft Engine** - Intelligent hero pick suggestions based on synergy, counters, and meta analysis
- 📊 **Team Analysis** - Comprehensive team composition evaluation with strengths and weaknesses
- 🎯 **Counter Strategy** - Smart ban suggestions and counter pick recommendations
- 📈 **Performance Tracking** - Match result recording and hero performance analytics
- 🔄 **Meta Updates** - Easy patch data integration and hero statistics updates
- 🚀 **Production Ready** - Scalable FastAPI backend with PostgreSQL database

## API Endpoints

### Draft Suggestions

```bash
# Get hero pick recommendations
POST /draft/suggest
{
  "ally_picks": ["Lolita", "Yin"],
  "enemy_picks": ["Valentina", "Esmeralda"],
  "role_preference": "Tank"
}

# Get ban suggestions
POST /draft/ban-suggest
{
  "ally_picks": ["Lolita", "Yin"],
  "enemy_picks": ["Valentina"],
  "ban_phase": "first"
}

# Analyze team composition
POST /draft/analyze
{
  "ally_picks": ["Lolita", "Yin", "Chang'e", "Hanabi", "Estes"]
}
```

### Hero Management

```bash
# List all heroes
GET /heroes/list?role=Tank&search=Khufra

# Get hero details
GET /heroes/Khufra

# Get hero counters
GET /heroes/Khufra/counters

# Update hero data
PUT /heroes/Khufra
{
  "stats": {...},
  "counters": {...}
}
```

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd DraftSensei-Backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Set environment variables
set DATABASE_URL=postgresql://username:password@localhost:5432/draftsensei
set DEBUG=true

# Or create .env file
echo "DATABASE_URL=postgresql://username:password@localhost:5432/draftsensei" > .env
echo "DEBUG=true" >> .env
```

### 3. Initialize Database

```bash
# Load sample hero data
python -m app.utils.patch_updater load-sample

# Or create from template
python -m app.utils.patch_updater create-template
python -m app.utils.patch_updater update-from-file --file patch_template.json
```

### 4. Run Development Server

```bash
# Start FastAPI server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Alternative: Run directly
python app/main.py
```

### 5. Test the API

```bash
# Check API health
curl http://localhost:8000/health

# Get hero list
curl http://localhost:8000/heroes/list

# Test draft suggestion
curl -X POST http://localhost:8000/draft/suggest \
  -H "Content-Type: application/json" \
  -d '{"ally_picks": ["Lolita", "Yin"], "enemy_picks": ["Valentina"]}'
```

## Project Structure

```
app/
├── main.py                 # FastAPI application setup
├── routers/
│   ├── draft.py           # Draft suggestion endpoints
│   └── heroes.py          # Hero management endpoints
├── schemas/
│   ├── draft_schema.py    # Request/response models for draft
│   └── hero_schema.py     # Request/response models for heroes
├── db/
│   ├── database.py        # Database connection & session management
│   └── models.py          # SQLAlchemy models (Hero, MatchHistory, etc.)
├── services/
│   ├── draft_engine.py    # AI recommendation engine
│   └── synergy.py         # Hero synergy & counter system
└── utils/
    ├── patch_updater.py   # Hero data import/update utilities
    └── analytics.py       # Performance analytics & insights
```

## AI Algorithm

The draft engine uses a multi-factor scoring system:

- **Synergy Score (25%)** - Team composition harmony and role balance
- **Counter Score (30%)** - Advantage against enemy picks
- **Role Balance (20%)** - Team composition completeness
- **Meta Performance (15%)** - Recent match performance statistics
- **Player Preference (10%)** - Personal hero experience and win rates

## Database Schema

### Heroes Table

- `id` - Primary key
- `name` - Hero name (unique)
- `role` - Tank, Fighter, Assassin, Mage, Marksman, Support
- `stats_json` - Hero statistics (HP, damage, etc.)
- `counters_json` - Counter relationships with other heroes
- `synergy_json` - Synergy scores with other heroes

### Match History Table

- `id` - Primary key
- `hero_id` - Foreign key to heroes
- `performance_score` - Match performance (0-100)
- `ally_composition` - JSON array of ally heroes
- `enemy_composition` - JSON array of enemy heroes
- `timestamp` - Match date/time

### Player Preferences Table

- `id` - Primary key
- `player_id` - Player identifier
- `hero_id` - Foreign key to heroes
- `weight` - Preference weight (0.0-2.0)
- `win_rate` - Personal win rate with hero
- `play_count` - Number of games played

## Deployment

### Environment Variables

```bash
DATABASE_URL=postgresql://user:pass@host:port/db
PORT=8000
HOST=0.0.0.0
DEBUG=false
ENV=production
```

### Render.com Deployment

1. Connect GitHub repository
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables in Render dashboard
5. Connect PostgreSQL database

### Railway.app Deployment

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### Docker Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## API Documentation

Once running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Usage Examples

### Python Client

```python
import requests

# Initialize client
base_url = "http://localhost:8000"

# Get draft suggestions
response = requests.post(f"{base_url}/draft/suggest", json={
    "ally_picks": ["Lolita", "Yin"],
    "enemy_picks": ["Valentina", "Esmeralda"],
    "role_preference": "Support"
})

suggestions = response.json()
for pick in suggestions["best_picks"]:
    print(f"Recommended: {pick['hero']} (Score: {pick['score']}) - {pick['reasons'][0]}")

# Record match result
requests.post(f"{base_url}/draft/record-match", json={
    "hero_name": "Khufra",
    "ally_team": ["Khufra", "Yin", "Chang'e", "Granger", "Estes"],
    "enemy_team": ["Valentina", "Fanny", "Pharsa", "Hanabi", "Angela"],
    "performance_score": 85.5,
    "won": True
})
```

### JavaScript/Frontend Integration

```javascript
// Get hero suggestions
const getDraftSuggestion = async (allyPicks, enemyPicks) => {
  const response = await fetch("/draft/suggest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ally_picks: allyPicks,
      enemy_picks: enemyPicks,
    }),
  });

  const data = await response.json();
  return data.best_picks;
};

// Usage
const suggestions = await getDraftSuggestion(
  ["Lolita", "Yin"],
  ["Valentina", "Esmeralda"]
);
console.log("Top pick:", suggestions[0].hero);
```

## Data Management

### Update Hero Data

```bash
# Create patch file
python -m app.utils.patch_updater create-template

# Update from patch file
python -m app.utils.patch_updater update-from-file --file patch_1.7.34.json

# Load sample data for development
python -m app.utils.patch_updater load-sample
```

### Analytics

```python
from app.utils.analytics import DraftAnalytics
from app.db.database import SessionLocal

db = SessionLocal()
analytics = DraftAnalytics(db)

# Get hero performance stats
stats = analytics.get_hero_performance_stats(days=30)

# Analyze hero counters
counters = analytics.get_counter_effectiveness("Khufra", days=30)

# Generate meta report
report = analytics.get_meta_trends(days=30)
```

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Create Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- 📧 Email: support@draftsensei.com
- 🐛 Issues: [GitHub Issues](https://github.com/username/draftsensei/issues)
- 📖 Documentation: [API Docs](http://localhost:8000/docs)

---

🎮 **Happy drafting with DraftSensei!**
