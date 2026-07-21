# Eyes on the Middle East

## Project Idea

Al Jazeera publishes a constant stream of Arabic political news, but there's no easy way to see what topics dominate coverage over time or who's writing about what. This project scrapes that coverage, uses topic modeling (BERTopic) to automatically discover recurring themes, and surfaces the results in an interactive dashboard — so instead of reading headlines one by one, you can see topic trends, distribution, and top contributors at a glance.

The pipeline has three stages:

1. **Scrape** — a Selenium-based scraper collects articles from Al Jazeera's Arabic politics section.
2. **Model** — a BERTopic pipeline clusters the articles into topics and labels new articles as they come in.
3. **Serve** — labeled articles are stored in Postgres, exposed via a FastAPI backend, and visualized in a React dashboard.

## Project Structure

```
.
├── api/                     FastAPI backend (routers, models, schemas, services)
├── frontend/                React + Vite dashboard
├── scripts/                 Scraper, topic modeling, and data processing scripts
├── notebooks/                Exploratory notebooks the scripts were derived from
├── news/                     Scraped/processed article JSON (git-ignored)
├── Aljazeera_topics_model/   Saved BERTopic model artifacts (git-ignored)
├── graphs/                   Topic modeling visualizations (git-ignored)
├── docker-compose.yml        db + api + frontend stack
└── requirements.txt          Python deps for the scraping/modeling scripts
```

## Get Started

### Prerequisites

- Docker and Docker Compose
- For local (non-Docker) development: Python 3.11+ and Node.js 20+

### Quick Start (Docker)

```sh
cp .env.example .env   # fill in real values, especially POSTGRES_PASSWORD
docker compose up --build
```

| Service  | URL |
|----------|-----|
| frontend | http://localhost:8080 |
| api      | http://localhost:8000 (docs at `/docs`) |
| db       | localhost:5432 (Postgres) |

The database starts empty. To populate it, run the pipeline scripts below in order:

```sh
python scripts/scraper.py                    # scrape articles into news/aljazeera_articles.json
python scripts/topic_modeling.py             # train BERTopic and save it to Aljazeera_topics_model/
python scripts/process_dashboard_data.py     # label new articles + upsert directly into Postgres
```

The scraper supports `--dry-run` to preview what would be scraped without saving anything.

### Local Development (without Docker)

```sh
# Backend
pip install -r api/requirements.txt
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm install
npm run dev

# Scraping / modeling scripts (heavier ML deps, kept separate from the API)
pip install -r requirements.txt
```

## License

Distributed under the [MIT License](LICENSE).
