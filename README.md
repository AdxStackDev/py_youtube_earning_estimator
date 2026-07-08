# YouTube Earnings Estimator

A Python backend service and Streamlit dashboard that estimates YouTube channel monthly earnings using publicly available data and a configurable RPM (Revenue Per Mille) model.

## Features

- **Channel resolution** — Accepts YouTube handles (`@channel`), full URLs, or plain-text search queries
- **Earnings estimation** — Calculates low, medium, and high monthly earnings based on recent video performance and configurable RPM range
- **Caching** — Multi-tier TTL cache (channel IDs, stats, videos) with LRU eviction to reduce API calls
- **REST API** — FastAPI endpoint for programmatic access with full validation and error handling
- **Streamlit dashboard** — Interactive web UI to look up any channel and view estimated earnings

## Prerequisites

- Python 3.12+
- [YouTube Data API v3](https://console.cloud.google.com/apis/library/youtube.googleapis.com) key

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `YOUTUBE_API_KEY` | Yes | — | Your YouTube Data API v3 key |
| `RPM_LOW` | No | `0.50` | Low-end RPM estimate (USD per 1,000 views) |
| `RPM_HIGH` | No | `4.00` | High-end RPM estimate (USD per 1,000 views) |
| `CACHE_TTL_SECONDS` | No | `3600` | General cache TTL in seconds |
| `API_TIMEOUT_SECONDS` | No | `10` | HTTP timeout for YouTube API requests |
| `CACHE_CHANNEL_TTL` | No | `86400` | Channel ID cache TTL (24 hours) |
| `CACHE_STATS_TTL` | No | `3600` | Channel stats cache TTL (1 hour) |
| `CACHE_VIDEOS_TTL` | No | `1800` | Recent videos cache TTL (30 minutes) |
| `CACHE_MAX_SIZE` | No | `1000` | Maximum number of cache entries (LRU eviction) |

## Local Setup

1. **Install dependencies**

```bash
pip install -r requirements.txt
```

2. **Configure environment**

```bash
cp .env.example .env
# Edit .env and add your YOUTUBE_API_KEY
```

3. **Run the API**

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

4. **Run the Streamlit dashboard**

```bash
streamlit run streamlit_app.py
```

The dashboard will open at `http://localhost:8501` by default.

## Docker Usage

**Build the image:**

```bash
docker build -t youtube-earnings-estimator .
```

**Run the container:**

```bash
docker run -p 8000:8000 --env-file .env youtube-earnings-estimator
```

The API will be available at `http://localhost:8000`.

## API Endpoint Reference

### Health Check

```
GET /health
```

**Response** `200 OK`

```json
{
  "status": "ok"
}
```

### Estimate Earnings

```
GET /estimate?q=<channel_query>
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Channel handle, URL, or search query (1–256 chars) |
| `rpm_low` | float | No | Override low RPM (0.01–100.0) |
| `rpm_high` | float | No | Override high RPM (0.01–100.0) |

**Response** `200 OK`

```json
{
  "channel_title": "Example Channel",
  "subscriber_count": 1500000,
  "total_views": 500000000,
  "video_count": 320,
  "estimated_monthly_views": 2400000.0,
  "earnings_low": 1200.00,
  "earnings_medium": 5400.00,
  "earnings_high": 9600.00,
  "rpm_low": 0.5,
  "rpm_high": 4.0,
  "recent_videos": [
    {
      "video_id": "abc123",
      "title": "Latest Video Title",
      "view_count": 600000
    }
  ]
}
```

### Error Responses

| Status | Condition | Body |
|--------|-----------|------|
| `404` | Channel not found | `{"detail": "Channel not found for query: ..."}` |
| `422` | Invalid input (empty query, bad RPM values) | `{"detail": "..."}` |
| `502` | YouTube API error or timeout | `{"detail": "..."}` |
| `500` | Unexpected server error | `{"detail": "Internal server error"}` |

## Tech Stack

- **[FastAPI](https://fastapi.tiangolo.com/)** — Web framework and API layer
- **[httpx](https://www.python-httpx.org/)** — Async HTTP client for YouTube API calls
- **[cachetools](https://cachetools.readthedocs.io/)** — In-memory TTL + LRU caching
- **[Pydantic](https://docs.pydantic.dev/)** — Data validation and settings management
- **[Streamlit](https://streamlit.io/)** — Interactive dashboard UI
- **[pytest](https://docs.pytest.org/)** — Test framework
- **[Hypothesis](https://hypothesis.readthedocs.io/)** — Property-based testing
- **[respx](https://lundberg.github.io/respx/)** — Mock httpx requests in tests

## Running Tests

```bash
pytest
```

To run with verbose output:

```bash
pytest -v
```
