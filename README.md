# Trade Challenges Research Agent (FastAPI + OpenAI)

This service researches global trade challenges relevant to the UK and EU, extracts structured challenges, deduplicates them, and outputs JSON and Markdown reports.

## Features
- FastAPI service with async BackgroundTasks job runner
- Search providers: Bing Web Search or SerpAPI (select via env var)
- Fetching with robots.txt checks, rate limiting, retries, and caching
- Main text extraction via trafilatura with readability and BeautifulSoup fallback
- OpenAI Responses API for extraction and synthesis
- Embedding-based dedupe + rule-based dedupe
- Postgres persistence via SQLAlchemy
- JSON output and Markdown report per run

## Setup

1) Create a virtual environment and install deps:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Copy and fill env vars:

```bash
cp .env.example .env
```

Set `OPENAI_API_KEY` as an environment variable (recommended for key safety). See OpenAI guidance on using environment variables for API keys. You can load `.env` in your shell or export directly.

3) Ensure Postgres is running and run the API:

```bash
uvicorn app.main:app --reload
```

## Docker

```bash
docker-compose up --build
```

## Production Docker Deploy

1) Create a production `.env` on the server (do not commit it):

```bash
cat <<'EOF' > .env
OPENAI_API_KEY=your_key
SEARCH_PROVIDER=bing
AZURE_BING_KEY=your_bing_key
AZURE_BING_ENDPOINT=https://api.bing.microsoft.com/v7.0/search
SERPAPI_KEY=
OPENAI_MODEL=gpt-4.1-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
DATABASE_URL=postgresql+psycopg2://trade:trade@db:5432/trade_challenges
EOF
```

2) Build and run in detached mode:

```bash
docker compose --env-file .env up --build -d
```

3) Verify health:

```bash
curl http://localhost:8000/health
```

4) Tail logs (optional):

```bash
docker compose logs -f app
```

Notes:
- Consider placing a reverse proxy (nginx/Caddy) in front of the app for TLS.
- Use a managed Postgres in production and update `DATABASE_URL` accordingly.

## API Endpoints

- `POST /runs` start a run
- `GET /runs/{run_id}` status and stats
- `GET /runs/{run_id}/challenges` final JSON
- `GET /health` health check

Example request:

```bash
curl -X POST http://localhost:8000/runs \
  -H 'Content-Type: application/json' \
  -d '{"max_items": 20, "recency_days": 30, "top_n_per_query": 5, "dry_run": false}'
```

## Output Files

Each run writes to `./data/<run_id>/`:
- `output.json` final JSON
- `report.md` human-readable summary
- `html/` cached HTML
- `text/` extracted text

## Configuration

Key env vars (see `.env.example`):
- `SEARCH_PROVIDER` = `bing` or `serpapi`
- `AZURE_BING_KEY`, `AZURE_BING_ENDPOINT`
- `SERPAPI_KEY`
- `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_EMBEDDING_MODEL`
- `TOP_N_PER_QUERY`, `MAX_ITEMS`, `RECENCY_DAYS`, `DRY_RUN`

## Tests

```bash
pytest
```

## Example Output (Mocked)

See `examples/sample_output.json`.
