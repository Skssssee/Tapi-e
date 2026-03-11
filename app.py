from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import requests
import re
import time
import urllib.parse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Standard Mobile Headers for scraping
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Referer": "https://vidssave.com/",
    "Accept": "application/json, text/plain, */*",
    "X-Requested-With": "XMLHttpRequest"
}

@app.get("/")
def check():
    return {"status": "Direct Scraper Active", "mode": "No-Proxy"}

@app.get("/download/{url:path}")
async def get_video_data(url: str, request: Request):
    # 1. Extract Video ID
    match = re.search(r"(?:v=|\/|be\/)([0-9A-Za-z_-]{11})", url)
    if not match: 
        return {"success": False, "error": "Invalid YouTube Link"}
    
    target_link = f"https://www.youtube.com/watch?v={match.group(1)}"
    base_url = str(request.base_url).rstrip('/')

    payload = {
        "auth": "20250901majwlqo",
        "domain": "api-ak.vidssave.com",
        "origin": "cache",
        "link": target_link
    }

    try:
        # Direct request from Koyeb IP to Vidssave
        r = requests.post(
            "https://api.vidssave.com/api/contentsite_api/media/parse",
            data=payload,
            headers=HEADERS,
            timeout=10
        )
        
        res = r.json()
        
        if res.get("status") == 1:
            data = res["data"]
            formats = []
            
            for f in data.get("resources", []):
                if f.get("download_mode") == "direct":
                    # We still need the stream tunnel because the link is bound to Koyeb's IP
                    raw_dl_url = f.get("download_url")
                    encoded_url = urllib.parse.quote(raw_dl_url)
                    
                    formats.append({
                        "q": f.get("quality"),
                        "f": f.get("format"),
                        "s": round(f.get("size", 0) / 1048576, 1),
                        "u": f"{base_url}/stream?url={encoded_url}"
                    })
            
            return {
                "success": True,
                "title": data.get("title"),
                "thumbnail": data.get("thumbnail"),
                "formats": formats
            }
        
        return {"success": False, "error": "Vidssave returned status 0", "raw": res}

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/stream")
async def stream_video(url: str = Query(...)):
    """
    Tunnels the data from Vidssave through Koyeb so the IP matches.
    """
    def generate():
        # Direct stream from Vidssave to User via Koyeb
        with requests.get(url, headers={"User-Agent": HEADERS["User-Agent"]}, stream=True) as r:
            for chunk in r.iter_content(chunk_size=256*1024):
                yield chunk

    # Try to get file info for a better download experience
    try:
        h = requests.head(url, headers={"User-Agent": HEADERS["User-Agent"]}, timeout=5)
        size = h.headers.get("Content-Length", "")
    except:
        size = ""

    return StreamingResponse(
        generate(),
        media_type="video/mp4",
        headers={
            "Content-Disposition": 'attachment; filename="video.mp4"',
            "Content-Length": size,
            "Access-Control-Allow-Origin": "*"
        }
        )
