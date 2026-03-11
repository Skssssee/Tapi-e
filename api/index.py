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
    "Accept": "*/*",
    "Origin": "https://vidssave.com",
    "Referer": "https://vidssave.com/",
    "Content-Type": "application/x-www-form-urlencoded"
}

@app.get("/")
def home():
    return {"status": "API running"}

@app.get("/download/{url:path}")
def get_video_data(url: str):

    session = requests.Session()

    parse_url = "https://api.vidssave.com/api/contentsite_api/media/parse"

    payload = {
        "auth": "20250901majwlqo",
        "domain": "api-ak.vidssave.com",
        "origin": "cache",
        "link": url
    }

    resp_raw = session.post(parse_url, data=payload, headers=HEADERS)
    resp = resp_raw.json()

    if "data" not in resp:
        return {"success": False}

    video_info = resp["data"]
    resources = video_info.get("resources", [])

    clean_formats = []

    for res in resources:
        raw_dl_url = res.get("download_url", "")

        parsed_url = urllib.parse.urlparse(raw_dl_url)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        clean_formats.append({
            "type": res.get("type"),
            "format": res.get("format"),
            "quality": res.get("quality"),
            "size": res.get("size"),
            "request_token": query_params.get("request",[None])[0],
            "direct_url": raw_dl_url
        })

    return {
        "success": True,
        "title": video_info.get("title"),
        "thumbnail": video_info.get("thumbnail"),
        "formats": clean_formats
      }
