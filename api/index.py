from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import requests
import random
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

# --- 20 PROXY ROTATION (Dual Accounts) ---
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

# Simple Memory Cache
CACHE = {}
# Change this to your actual Vercel or Render domain
DOMAIN = "https://tapi-e.vercel.app" 

def get_vid(u):
    m = re.search(r"(?:v=|\/|be\/)([0-9A-Za-z_-]{11})", u)
    return m.group(1) if m else None

@app.get("/download/{url:path}")
async def get_data(url: str):
    vid = get_vid(url)
    if not vid: return {"success": False, "error": "Invalid URL"}
    
    # 1. Return from Cache (Bandwidth Saver)
    if vid in CACHE and time.time() < CACHE[vid]["exp"]:
        return CACHE[vid]["data"]

    target = f"https://www.youtube.com/watch?v={vid}"
    
    # 2. Try random proxy to fetch from Vidssave
    for _ in range(3):
        p = random.choice(PROXIES)
        try:
            r = requests.post("https://api.vidssave.com/api/contentsite_api/media/parse", 
                data={"auth": "20250901majwlqo", "domain": "api-ak.vidssave.com", "origin": "cache", "link": target},
                headers={"User-Agent": "Mozilla/5.0", "Referer": "https://vidssave.com/"},
                proxies={"http": p, "https": p}, timeout=7)
            
            j = r.json()
            if j.get("status") == 1:
                data = j["data"]
                formats = []
                for f in data.get("resources", []):
                    if f.get("download_mode") == "direct":
                        # ENCODE the URL for our /stream tunnel
                        encoded_url = urllib.parse.quote(f.get("download_url"))
                        stream_link = f"{DOMAIN}/stream?url={encoded_url}"
                        
                        formats.append({
                            "q": f.get("quality"),
                            "f": f.get("format"),
                            "s": round(f.get("size", 0)/1048576, 1),
                            "u": stream_link
                        })
                
                res = {
                    "success": True,
                    "title": data.get("title"),
                    "thumbnail": data.get("thumbnail"),
                    "formats": formats
                }
                CACHE[vid] = {"data": res, "exp": time.time() + 900}
                return res
        except: continue

    return {"success": False, "error": "API Busy"}

@app.get("/stream")
async def stream_video(url: str = Query(...)):
    """
    FIX: Tunnels the download so Vidssave doesn't give a 403 Forbidden error.
    """
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://vidssave.com/"}
    
    def generate():
        with requests.get(url, headers=headers, stream=True, timeout=20) as r:
            for chunk in r.iter_content(chunk_size=128*1024):
                yield chunk

    # Get file headers
    r_head = requests.head(url, headers=headers, timeout=10)
    
    return StreamingResponse(
        generate(),
        media_type="video/mp4",
        headers={
            "Content-Disposition": 'attachment; filename="video.mp4"',
            "Content-Length": r_head.headers.get("Content-Length", ""),
            "Access-Control-Allow-Origin": "*"
        }
    )
