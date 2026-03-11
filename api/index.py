from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import urllib.parse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Origin": "https://vidssave.com",
    "Referer": "https://vidssave.com/",
    "Content-Type": "application/x-www-form-urlencoded"
}

@app.get("/")
def home():
    return {"status": "API running"}

@app.get("/download")
def get_video_data(url: str):

    session = requests.Session()

    parse_url = "https://api.vidssave.com/api/contentsite_api/media/parse"

    payload = {
        "auth": "20250901majwlqo",
        "domain": "api-ak.vidssave.com",
        "origin": "cache",
        "link": url
    }

    resp = session.post(parse_url, data=payload, headers=HEADERS).json()

    if "data" not in resp:
        return {"success": False}

    video = resp["data"]

    return {
        "success": True,
        "title": video.get("title"),
        "thumbnail": video.get("thumbnail")
    }

# THIS IS REQUIRED FOR VERCEL
handler = app
