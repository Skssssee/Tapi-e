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

# YOUR 20 PROXIES
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

@app.get("/download/{url:path}")
async def get_vidssave_data(url: str, request: Request):
    # 1. Clean URL
    match = re.search(r"(?:v=|\/|be\/)([0-9A-Za-z_-]{11})", url)
    if not match: return {"success": False, "error": "Invalid Link"}
    target = f"https://www.youtube.com/watch?v={match.group(1)}"
    
    base_url = str(request.base_url).rstrip('/')
    
    # 2. Loop through proxies until one works
    # We try up to 10 different proxies from your list
    random.shuffle(PROXIES) 
    
    for i in range(10):
        proxy = PROXIES[i]
        try:
            payload = {
                "auth": "20250901majwlqo",
                "domain": "api-ak.vidssave.com",
                "origin": "cache",
                "link": target
            }
            # Enhanced Headers to look like a real mobile browser
            headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
                "Referer": "https://vidssave.com/",
                "Accept": "application/json, text/plain, */*",
                "X-Requested-With": "XMLHttpRequest"
            }
            
            r = requests.post(
                "https://api.vidssave.com/api/contentsite_api/media/parse", 
                data=payload, 
                headers=headers, 
                proxies={"http": proxy, "https": proxy}, 
                timeout=8
            )
            
            res_json = r.json()
            
            if res_json.get("status") == 1:
                data = res_json["data"]
                formats = []
                for f in data.get("resources", []):
                    if f.get("download_mode") == "direct":
                        # Tunneling the link to fix the 403 Forbidden
                        dl_url = f.get("download_url")
                        encoded = urllib.parse.quote(dl_url)
                        formats.append({
                            "q": f.get("quality"),
                            "f": f.get("format"),
                            "s": round(f.get("size", 0)/1048576, 1),
                            "u": f"{base_url}/stream?url={encoded}"
                        })
                
                return {
                    "success": True,
                    "title": data.get("title"),
                    "thumbnail": data.get("thumbnail"),
                    "formats": formats
                }
        except Exception as e:
            print(f"Proxy {i} failed: {e}")
            continue # Try next proxy

    return {"success": False, "error": "All 10 proxy attempts failed. Check Webshare balance."}

@app.get("/stream")
async def stream_video(url: str = Query(...)):
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://vidssave.com/"}
    def generate():
        # Large chunks for Koyeb (256KB)
        with requests.get(url, headers=headers, stream=True) as r:
            for chunk in r.iter_content(chunk_size=262144):
                yield chunk
    
    # Get file info for browser
    head = requests.head(url, headers=headers)
    return StreamingResponse(
        generate(),
        media_type="video/mp4",
        headers={
            "Content-Disposition": 'attachment; filename="video.mp4"',
            "Content-Length": head.headers.get("Content-Length", "")
        }
                        )
