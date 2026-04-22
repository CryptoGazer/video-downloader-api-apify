# FastAPI Video Downloader

A lightweight FastAPI service that resolves Instagram reel and post URLs to direct video URLs and proxies the resulting video stream. Designed as a backend node in n8n workflows that pipe video content to Whisper for transcription.

---

## Overview

The service wraps the [Apify Instagram Scraper](https://apify.com/shu8hvrXbJbY3Eb9W) actor to extract the underlying CDN video URL from a given Instagram post or reel, then optionally fetches and streams that video as a binary download. All endpoints are protected by a static API key passed via the `X-API-Key` request header.

---

## Endpoints

### `POST /in/instagram`

Resolves an Instagram URL to a direct CDN video URL.

**Request**

```json
{
  "url": "https://www.instagram.com/reel/DHDuRyztxwm/"
}
```

**Response** `202 Accepted`

```json
{
  "accepted": true,
  "videoUrl": "https://..."
}
```

---

### `POST /in/instagram/download`

Fetches the video at the given CDN URL and streams it back to the caller as an MP4 attachment. Supports `Range` headers for partial content requests.

**Request**

```json
{
  "url": "https://cdn-video.instagram.com/..."
}
```

**Response** `200 OK` or `206 Partial Content`

Binary video stream with `Content-Disposition: attachment; filename*=UTF-8''<filename>.mp4`.

---

## Authentication

Every request must include an `X-API-Key` header whose value matches the `APIFY_TOKEN` environment variable.

```
X-API-Key: <your-apify-token>
```

Requests without a valid key receive `401 Unauthorized`.

---

## Configuration

| Variable | Description |
|---|---|
| `APIFY_TOKEN` | Apify API token. Used both for calling the Apify actor and for authenticating incoming requests. |

Copy `.env.example` (or set the variable directly in your container environment):

```
APIFY_TOKEN=your_apify_token_here
```

---

## Running locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
APIFY_TOKEN=your_token uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

---

## Running with Docker

```bash
docker build -t fastapi-video-downloader .
docker run -p 8080:8080 -e APIFY_TOKEN=your_token fastapi-video-downloader
```

The service listens on port `8080` inside the container.

---

## Dependencies

| Package | Purpose |
|---|---|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `requests` | Synchronous HTTP client for Apify and video streaming |
| `httpx` | Async HTTP client (available for future use) |
| `python-dotenv` | Loading environment variables from `.env` |

---

## Project structure

```
.
├── main.py           # Application entry point and all route handlers
├── requirements.txt  # Python dependencies
├── Dockerfile        # Container image definition
└── .env              # Local environment variables (not committed)
```
