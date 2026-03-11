from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import requests
import uvicorn
import urllib.parse
import random
import re

app = FastAPI(title="My Private Vidssave API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- YOUR 20 PROXIES (2 ACCOUNTS) ---
PROXIES = [
    "http://uppezuyk:c2bfaa6diuyf@31.59.20.176:6754", "http://uppezuyk:c2bfaa6diuyf@23.95.150.145:6114",
    "http://uppezuyk:c2bfaa6diuyf@198.23.239.134:6540", "http://uppezuyk:c2bfaa6diuyf@45.38.107.97:6014",
    "http://uppezuyk:c2bfaa6diuyf@107.172.163.27:6543", "http://uppezuyk:c2bfaa6diuyf@198.105.121.200:6462",
    "http://uppezuyk:c2bfaa6diuyf@64.137.96.74:6641", "http://uppezuyk:c2bfaa6diuyf@216.10.27.159:6837",
    "http://uppezuyk:c2bfaa6diuyf@142.111.67.146:5611", "http://uppezuyk:c2bfaa6diuyf@191.96.254.138:6185",
    "http://fqxzwtzv:c65sasel8qr8@31.59.20.176:6754", "http://fqxzwtzv:c65sasel8qr8@23.95.150.145:6114",
    "http://fqxzwtzv:c65sasel8qr8@198.23.239.134:6540", "http://fqxzwtzv:c65sasel8qr8@45.38.107.97:6014",
    "http://fqxzwtzv:c65sasel8qr8@107.172.163.27:6543", "http://fqxzwtzv:c65sasel8qr8@198.105.121.200:6462",
    "http://fqxzwtzv:c65sasel8qr8@64.137.96.74:6641", "http://fqxzwtzv:c65sasel8qr8@216.10.27.159:6837",
    "http://fqxzwtzv:c65sasel8qr8@142.111.67.146:5611", "http://fqxzwtzv:c65sasel8qr8@191.96.254.138:6185"
]

# Use your exact original headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 16; RMX3870 Build/BP2A.250605.015) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.7632.120 Mobile Safari/537.36",
    "Accept": "*/*",
    "Origin": "https://vidssave.com",
    "Referer": "https://vidssave.com/",
    "X-Requested-With": "mark.via.gp",
    "Content-Type": "application/x-www-form-urlencoded"
}

# Change this to your live domain (e.g. https://your-app.onrender.com)
# For local testing, use http://127.0.0.1:8000
MY_DOMAIN = "http://127.0.0.1:8000"

@app.get("/download/{url:path}")
def get_video_data(url: str):
    session = requests.Session()
    parse_url = "https://api.vidssave.com/api/contentsite_api/media/parse"
    
    # Pick a random proxy to save bandwidth
    proxy = random.choice(PROXIES)
    proxies_dict = {"http": proxy, "https": proxy}

    payload = {
        "auth": "20250901majwlqo",
        "domain": "api-ak.vidssave.com",
        "origin": "cache",
        "link": url
    }
    
    try:
        resp_raw = session.post(parse_url, data=payload, headers=HEADERS, proxies=proxies_dict, timeout=10)
        resp = resp_raw.json()
        
        if "data" not in resp:
            return {"success": False, "error": "API Blocked"}
        
        video_info = resp["data"]
        clean_formats = []
        
        for res in video_info.get("resources", []):
            raw_dl_url = res.get("download_url", "")
            if not raw_dl_url: continue

            # --- THE FIX: Instead of raw URL, we point to our /stream endpoint ---
            encoded_target = urllib.parse.quote(raw_dl_url)
            proxied_url = f"{MY_DOMAIN}/stream?url={encoded_target}"

            clean_formats.append({
                "type": str(res.get("type")).upper(),
                "format": str(res.get("format")).upper(),
                "quality": str(res.get("quality")).upper(),
                "size_mb": round(res.get("size", 0) / 1048576, 2),
                "url": proxied_url # This link will now work on websites
            })
            
        return {
            "success": True,
            "title": video_info.get("title"),
            "thumbnail": video_info.get("thumbnail"),
            "formats": clean_formats
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/stream")
def stream_video(url: str = Query(...)):
    """
    This tunnels the video through your server so the 
    IP matches the one that requested the link.
    """
    # Use headers to mimic the original request
    stream_headers = {"User-Agent": HEADERS["User-Agent"], "Referer": "https://vidssave.com/"}
    
    def generate():
        with requests.get(url, headers=stream_headers, stream=True) as r:
            for chunk in r.iter_content(chunk_size=128*1024): # 128KB chunks
                yield chunk

    # Get file size for the browser progress bar
    r_head = requests.head(url, headers=stream_headers)
    
    return StreamingResponse(
        generate(),
        media_type="video/mp4",
        headers={
            "Content-Disposition": 'attachment; filename="video.mp4"',
            "Content-Length": r_head.headers.get("Content-Length", "")
        }
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

