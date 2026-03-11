from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
import random
import re
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 20 PROXY LIST
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

CACHE = {}

def get_vid(u):
    m = re.search(r"(?:v=|\/|be\/)([0-9A-Za-z_-]{11})", u)
    return m.group(1) if m else None

@app.get("/download/{url:path}")
async def get_data(url: str):
    vid = get_vid(url)
    if not vid: return {"success": False, "error": "Invalid URL"}
    
    if vid in CACHE and time.time() < CACHE[vid]["exp"]:
        return CACHE[vid]["data"]

    target = f"https://www.youtube.com/watch?v={vid}"
    
    # Try ONLY 2 times with very fast timeouts to prevent Vercel Crash
    for _ in range(2):
        p = random.choice(PROXIES)
        try:
            r = requests.post("https://api.vidssave.com/api/contentsite_api/media/parse", 
                data={"auth": "20250901majwlqo", "domain": "api-ak.vidssave.com", "origin": "cache", "link": target},
                headers={"User-Agent": "Mozilla/5.0", "Referer": "https://vidssave.com/"},
                proxies={"http": p, "https": p}, 
                timeout=4) # Strict 4s timeout
            
            j = r.json()
            if j.get("status") == 1:
                data = j["data"]
                formats = []
                for f in data.get("resources", []):
                    if f.get("download_mode") == "direct":
                        formats.append({
                            "q": f.get("quality"),
                            "f": f.get("format"),
                            "s": round(f.get("size", 0)/1048576, 1),
                            "u": f.get("download_url") # Direct link (No streaming)
                        })
                
                res = {"success": True, "title": data.get("title"), "thumbnail": data.get("thumbnail"), "formats": formats}
                CACHE[vid] = {"data": res, "exp": time.time() + 900}
                return res
        except: continue

    return {"success": False, "error": "Vercel Timeout or API Busy"}
