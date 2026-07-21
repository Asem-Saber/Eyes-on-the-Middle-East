.PHONY: scrape model process pipeline pipeline-full migrate dev-api dev-frontend test test-api test-frontend

scrape:
	python scripts/scraper.py

scrape-dry:
	python scripts/scraper.py --dry-run

model:
	python scripts/topic_modeling.py

process:
	python scripts/process_dashboard_data.py

pipeline: scrape process

pipeline-full: scrape model process

migrate:
	alembic upgrade head

dev-api:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

test: test-api test-frontend

test-api:
	python -m pytest tests/ -v

test-frontend:
	cd frontend && npx vitest run
