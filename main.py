import httpx
import requests
from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, AnyHttpUrl, field_validator
from dotenv import load_dotenv

import os
import re
import posixpath
from typing import Optional, AsyncIterator, Iterator
from pprint import pprint
from urllib.parse import urlparse, quote


app = FastAPI()


# load_dotenv()

APIFY_TOKEN = os.environ.get("APIFY_TOKEN")
ACTOR_ID = "shu8hvrXbJbY3Eb9W"
url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/run-sync-get-dataset-items"

testLink = "https://www.instagram.com/reel/DHDuRyztxwm/"


def require_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> bool:
    if not APIFY_TOKEN or x_api_key != APIFY_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


class InPayload(BaseModel):
    url: AnyHttpUrl

    # @field_validator("url")
    # @classmethod
    # def ensure_instagram(cls, v: AnyHttpUrl):
    #     host = v.host.lower()
    #     if not (host.endswith("instagram.com") or host.endswith("cdninstagram.com")):
    #         raise ValueError("URL должен указывать на домен Instagram")
    #     return v


@app.post("/in/instagram", status_code=202, dependencies=[Depends(require_api_key)])
async def ingest(payload: InPayload):
    video_url = str(payload.url)

    payload = {
        "addParentData": False,
        "directUrls": [video_url],
        "enhanceUserSearchWithFacebookPage": False,
        "isUserReelFeedURL": False,
        "isUserTaggedFeedURL": False,
        "resultsLimit": 1,
        "resultsType": "posts",
        "searchLimit": 1,
        "searchType": "hashtag"
    }

    headers = {
        "Authorization": f"Bearer {APIFY_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    resp = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=310
    )
    resp.raise_for_status()

    items = resp.json()[0]


    print()
    pprint(items)
    print()

    return {"accepted": True, "videoUrl": items.get("videoUrl")}


@app.post("/in/instagram/download", dependencies=[Depends(require_api_key)])
def download_instagram_video(
    payload: InPayload,
    range_header: Optional[str] = Header(None, alias="Range"),
):
    src_url = str(payload.url)

    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "*/*"}
    if range_header:
        headers["Range"] = range_header  # поддержка частичных запросов

    r = session.get(src_url, headers=headers, stream=True, allow_redirects=True, timeout=60)
    if r.status_code not in (200, 206):
        text = r.text
        r.close(); session.close()
        raise HTTPException(status_code=r.status_code, detail=text)

    content_type  = r.headers.get("Content-Type", "video/mp4")
    content_len   = r.headers.get("Content-Length")
    content_range = r.headers.get("Content-Range")
    accept_ranges = r.headers.get("Accept-Ranges")

    parsed = urlparse(src_url)
    filename = posixpath.basename(parsed.path) or "instagram_video.mp4"
    filename = re.sub(r'[\\/:*?"<>|]+', "_", filename)
    if not filename.lower().endswith(".mp4"):
        filename += ".mp4"

    def iter_bytes() -> Iterator[bytes]:
        try:
            for chunk in r.iter_content(chunk_size=64 * 1024):
                if chunk:
                    yield chunk
        finally:
            r.close()
            session.close()

    resp = StreamingResponse(iter_bytes(), media_type=content_type, status_code=r.status_code)
    if content_len:
        resp.headers["Content-Length"] = content_len  # может отсутствовать при chunked
    if content_range:
        resp.headers["Content-Range"] = content_range
    if accept_ranges:
        resp.headers["Accept-Ranges"] = accept_ranges
    resp.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{quote(filename)}"
    return resp
