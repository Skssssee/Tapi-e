from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import urllib.parse

# 1. Initialize FastAPI App
app = FastAPI(
    title="My Private Vidssave API",
    description="A fully automated API to extract YouTube download links.",
    version="2.0"
)

# 2. Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 16; RMX3870 Build/BP2A.250605.015) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.7632.120 Mobile Safari/537.36",
    "Accept": "*/*",
    "Origin": "https://vidssave.com",
    "Referer": "https://vidssave.com/",
    "X-Requested-With": "mark.via.gp",
    "Content-Type": "application/x-www-form-urlencoded"
}

@app.get("/")
def home():
    return {"status": "API is running", "message": "Use /download/{url} to get video data"}

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
    
    try:
        resp_raw = session.post(parse_url, data=payload, headers=HEADERS)
        resp = resp_raw.json()
        
        if "data" not in resp or "resources" not in resp["data"]:
            return {"success": False, "error": "Invalid URL or Server Blocked", "raw_response": resp}
        
        video_info = resp["data"]
        resources = video_info.get("resources", [])
        
        clean_formats = []
        for res in resources:
            r_type = str(res.get("type")).upper()
            r_format = str(res.get("format")).upper()
            r_quality = str(res.get("quality")).upper()
            
            is_mute = True if r_quality in ["1080P", "1440P", "4K", "2160P"] and r_type == "VIDEO" else False
            
            raw_dl_url = res.get("download_url", "")
            parsed_url = urllib.parse.urlparse(raw_dl_url)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            req_token = query_params.get("request", [None])[0]
            
            clean_formats.append({
                "type": r_type,
                "format": r_format,
                "quality": r_quality,
                "size_mb": round(res.get("size", 0) / (1024 * 1024), 2),
                "is_mute": is_mute,
                "download_mode": res.get("download_mode"),
                "resource_id": res.get("resource_id"),
                "request_token": req_token,
                "direct_url": raw_dl_url if res.get("download_mode") == "direct" else None
            })
            
        return {
            "success": True,
            "title": video_info.get("title", "Unknown Title"),
            "duration_seconds": video_info.get("duration", 0),
            "thumbnail": video_info.get("thumbnail", ""),
            "total_formats_found": len(clean_formats),
            "formats": clean_formats
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}
