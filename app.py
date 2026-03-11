from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 11)",
    "Referer": "https://vidssave.com/"
}


@app.get("/")
def home():
    return {"status": "API running"}


@app.get("/stream")
def stream_video(request: Request, url: str = Query(...)):

    range_header = request.headers.get("range")

    headers = HEADERS.copy()
    if range_header:
        headers["Range"] = range_header

    r = requests.get(
        url,
        headers=headers,
        stream=True,
        allow_redirects=True,
        timeout=60
    )

    response_headers = {
        "Content-Type": r.headers.get("Content-Type", "video/mp4"),
        "Accept-Ranges": "bytes",
        "Access-Control-Allow-Origin": "*"
    }

    if "Content-Length" in r.headers:
        response_headers["Content-Length"] = r.headers["Content-Length"]

    if "Content-Range" in r.headers:
        response_headers["Content-Range"] = r.headers["Content-Range"]

    return StreamingResponse(
        r.iter_content(chunk_size=8192),
        status_code=r.status_code,
        headers=response_headers
    )
