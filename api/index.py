from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import urllib.parse

app = FastAPI()

# Enable CORS so your website can talk to Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root route to check if API is alive
@app.get("/")
def read_root():
    return {"status": "Online", "usage": "/download/YOUTUBE_URL"}

@app.get("/download/{url:path}")
def get_video_data(url: str):
    # Fix: If the URL is just an ID, reconstruct it
    if not url.startswith("http"):
        url = f"https://www.youtube.com/watch?v={url}"

    session = requests.Session()
    parse_url = "https://api.vidssave.com/api/contentsite_api/media/parse"
    
    # Headers exactly as needed
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "*/*",
        "Origin": "https://vidssave.com",
        "Referer": "https://vidssave.com/",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    payload = {
        "auth": "20250901majwlqo",
        "domain": "api-ak.vidssave.com",
        "origin": "cache",
        "link": url
    }
    
    try:
        resp_raw = session.post(parse_url, data=payload, headers=headers, timeout=10)
        
        # Check if response is actually JSON
        try:
            resp = resp_raw.json()
        except:
            return {"success": False, "error": "Third-party API returned invalid data"}

        if "data" not in resp:
            return {"success": False, "error": "Video not found or API blocked", "details": resp}
        
        video_info = resp["data"]
        resources = video_info.get("resources", [])
        
        clean_formats = []
        for res in resources:
            r_quality = str(res.get("quality")).upper()
            r_type = str(res.get("type")).upper()
            
            # Identify muted formats
            is_mute = r_quality in ["1080P", "1440P", "4K", "2160P"] and r_type == "VIDEO"
            
            raw_dl_url = res.get("download_url", "")
            
            clean_formats.append({
                "type": r_type,
                "format": str(res.get("format")).upper(),
                "quality": r_quality,
                "size_mb": round(res.get("size", 0) / (1024 * 1024), 2),
                "is_mute": is_mute,
                "direct_url": raw_dl_url if res.get("download_mode") == "direct" else None
            })
            
        return {
            "success": True,
            "title": video_info.get("title", "Unknown"),
            "thumbnail": video_info.get("thumbnail", ""),
            "formats": clean_formats
        }
        
    except Exception as e:
        # Returning a JSON error instead of crashing the function
        return {"success": False, "error": str(e)}
