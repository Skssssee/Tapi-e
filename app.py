from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import re

app = FastAPI()

# CORS
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
    return {"message": "YouTube Download API Running"}

@app.get("/download")
def download_video(url: str):

    # extract youtube video id
    match = re.search(r"(?:v=|\/|be\/)([0-9A-Za-z_-]{11})", url)
    if not match:
        return {"success": False, "error": "Invalid YouTube URL"}

    video_id = match.group(1)
    youtube_url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        r = requests.post(
            "https://api.vidssave.com/api/contentsite_api/media/parse",
            data={
                "auth": "20250901majwlqo",
                "domain": "api-ak.vidssave.com",
                "origin": "cache",
                "link": youtube_url
            },
            headers=HEADERS,
            timeout=15
        )

        res = r.json()

        if res.get("status") != 1:
            return {"success": False, "error": "Video parse failed"}

        data = res["data"]

        formats = []
        for f in data.get("resources", []):
            if f.get("download_mode") == "direct":
                formats.append({
                    "quality": f.get("quality"),
                    "format": f.get("format"),
                    "size_mb": round(f.get("size", 0) / 1048576, 2),
                    "download_url": f.get("download_url")
                })

        return {
            "success": True,
            "title": data.get("title"),
            "thumbnail": data.get("thumbnail"),
            "formats": formats
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
