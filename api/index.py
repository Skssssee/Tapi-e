from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import random
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PROXY_LIST = [
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

def clean_youtube_url(url: str):
    """
    Converts any YT link to a standard format: https://www.youtube.com/watch?v=VIDEO_ID
    Removes tracking parameters like ?si= or &t=
    """
    video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    if video_id_match:
        video_id = video_id_match.group(1)
        return f"https://www.youtube.com/watch?v={video_id}"
    return url

@app.get("/download/{url:path}")
def get_video_data(url: str):
    # 1. Normalize the URL
    target_url = clean_youtube_url(url)
    
    # 2. Try with random proxies
    for _ in range(3): # Increased to 3 attempts
        proxy = random.choice(PROXY_LIST)
        proxies = {"http": proxy, "https": proxy}
        
        try:
            payload = {
                "auth": "20250901majwlqo",
                "domain": "api-ak.vidssave.com",
                "origin": "cache",
                "link": target_url # Use the cleaned URL
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Origin": "https://vidssave.com",
                "Referer": "https://vidssave.com/",
                "Content-Type": "application/x-www-form-urlencoded"
            }

            response = requests.post(
                "https://api.vidssave.com/api/contentsite_api/media/parse",
                data=payload,
                headers=headers,
                proxies=proxies,
                timeout=8
            )
            
            data = response.json()
            
            # Check if the API actually succeeded
            if data.get("status") == 1 and data.get("data"):
                res = data["data"]
                return {
                    "success": True,
                    "title": res.get("title"),
                    "thumbnail": res.get("thumbnail"),
                    "formats": [
                        {
                            "quality": f.get("quality"),
                            "type": f.get("type"),
                            "format": f.get("format"),
                            "size_mb": round(f.get("size", 0) / 1048576, 2),
                            "direct_url": f.get("download_url")
                        } for f in res.get("resources", [])
                    ]
                }
            else:
                # Log the specific reason for failure
                print(f"Proxy {proxy} failed with: {data.get('msg')}")
                continue 

        except Exception as e:
            continue
            
    return {
        "success": False, 
        "error": "Link not supported by provider or all proxies blocked.",
        "cleaned_url_attempted": target_url
    }
