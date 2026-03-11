from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import urllib.parse
import random

app = FastAPI()

# Enable CORS for your website
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Your Private Proxy List formatted for Requests
# Format: http://username:password@ip:port
PROXIES = [
    "http://uppezuyk:c2bfaa6diuyf@31.59.20.176:6754",
    "http://uppezuyk:c2bfaa6diuyf@23.95.150.145:6114",
    "http://uppezuyk:c2bfaa6diuyf@198.23.239.134:6540",
    "http://uppezuyk:c2bfaa6diuyf@45.38.107.97:6014",
    "http://uppezuyk:c2bfaa6diuyf@107.172.163.27:6543",
    "http://uppezuyk:c2bfaa6diuyf@198.105.121.200:6462",
    "http://uppezuyk:c2bfaa6diuyf@64.137.96.74:6641",
    "http://uppezuyk:c2bfaa6diuyf@216.10.27.159:6837",
    "http://uppezuyk:c2bfaa6diuyf@142.111.67.146:5611",
    "http://uppezuyk:c2bfaa6diuyf@191.96.254.138:6185"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Origin": "https://vidssave.com",
    "Referer": "https://vidssave.com/",
    "Content-Type": "application/x-www-form-urlencoded"
}

@app.get("/")
def home():
    return {"status": "Proxy API Active", "proxy_count": len(PROXIES)}

@app.get("/download/{url:path}")
def get_video_data(url: str):
    # Pick a random proxy from your list
    selected_proxy = random.choice(PROXIES)
    proxies_config = {
        "http": selected_proxy,
        "https": selected_proxy
    }

    session = requests.Session()
    parse_url = "https://api.vidssave.com/api/contentsite_api/media/parse"
    
    payload = {
        "auth": "20250901majwlqo",
        "domain": "api-ak.vidssave.com",
        "origin": "cache",
        "link": url
    }
    
    try:
        # Sending request via Proxy
        resp_raw = session.post(
            parse_url, 
            data=payload, 
            headers=HEADERS, 
            proxies=proxies_config, 
            timeout=12
        )
        resp = resp_raw.json()
        
        if "data" not in resp or "resources" not in resp["data"]:
            return {
                "success": False, 
                "error": "Analyze failed or Blocked", 
                "proxy_used": selected_proxy.split('@')[-1], # Show IP only for debugging
                "details": resp
            }
        
        video_info = resp["data"]
        resources = video_info.get("resources", [])
        
        clean_formats = []
        for res in resources:
            r_type = str(res.get("type")).upper()
            r_quality = str(res.get("quality")).upper()
            
            is_mute = True if r_quality in ["1080P", "1440P", "4K", "2160P"] and r_type == "VIDEO" else False
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
            "title": video_info.get("title", "Unknown Title"),
            "thumbnail": video_info.get("thumbnail", ""),
            "formats": clean_formats,
            "meta": {"proxy_node": selected_proxy.split('@')[-1]}
        }
        
    except Exception as e:
        return {"success": False, "error": str(e), "proxy_attempted": selected_proxy.split('@')[-1]}

