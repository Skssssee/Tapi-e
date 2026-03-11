from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import requests
import random
import re
import time
import urllib.parse

# Initialize App
app = FastAPI(title="Koyeb Video API")

# Enable CORS for your website
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 20 PROXY LIST (Account 1 & Account 2) ---
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

# Simple Cache to prevent duplicate proxy requests
CACHE = {}

def get_video_id(url: str):
    """Extracts 11-char YouTube ID."""
    match = re.search(r"(?:v=|\/|be\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

@app.get("/")
def health_check():
    return {"status": "API is online", "proxies": len(PROXIES)}

@app.get("/download/{url:path}")
async def fetch_video_info(url: str, request: Request):
    vid = get_video_id(url)
    if not vid:
        return {"success": False, "error": "Invalid YouTube URL"}
    
    # 1. Check Cache (15 min)
    if vid in CACHE and time.time() < CACHE[vid]["exp"]:
        return CACHE[vid]["data"]

    # 2. Get the current domain automatically (e.g., your-app.koyeb.app)
    # This ensures the /stream links always point to the right place
    base_url = str(request.base_url).rstrip('/')
    target_yt_link = f"https://www.youtube.com/watch?v={vid}"
    
    # 3. Attempt extraction using Proxies
    for _ in range(3):
        selected_proxy = random.choice(PROXIES)
        try:
            payload = {
                "auth": "20250901majwlqo",
                "domain": "api-ak.vidssave.com",
                "origin": "cache",
                "link": target_yt_link
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://vidssave.com/"
            }
            
            response = requests.post(
                "https://api.vidssave.com/api/contentsite_api/media/parse", 
                data=payload, 
                headers=headers,
                proxies={"http": selected_proxy, "https": selected_proxy}, 
                timeout=12
            )
            
            json_data = response.json()
            if json_data.get("status") == 1 and "data" in json_data:
                video_data = json_data["data"]
                
                formats = []
                for res in video_data.get("resources", []):
                    if res.get("download_mode") == "direct":
                        # Tunnel the Forbidden link through our /stream endpoint
                        raw_url = res.get("download_url")
                        encoded_url = urllib.parse.quote(raw_url)
                        proxied_url = f"{base_url}/stream?url={encoded_url}"
                        
                        formats.append({
                            "quality": res.get("quality"),
                            "format": res.get("format"),
                            "size_mb": round(res.get("size", 0) / 1048576, 1),
                            "url": proxied_url
                        })
                
                final_response = {
                    "success": True,
                    "title": video_data.get("title"),
                    "thumbnail": video_data.get("thumbnail"),
                    "formats": formats
                }
                
                # Update Cache
                CACHE[vid] = {"data": final_response, "exp": time.time() + 900}
                return final_response
        except:
            continue

    return {"success": False, "error": "API or Proxies are currently busy."}

@app.get("/stream")
async def tunnel_video(url: str = Query(...)):
    """
    Acts as a bridge between the blocked Vidssave link and the user.
    """
    stream_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://vidssave.com/"
    }
    
    def stream_generator():
        with requests.get(url, headers=stream_headers, stream=True) as r:
            # Using 512KB chunks for Koyeb high-speed streaming
            for chunk in r.iter_content(chunk_size=524288):
                yield chunk

    # Pre-fetch headers to help browser progress bar
    try:
        head_req = requests.head(url, headers=stream_headers, timeout=10)
        content_length = head_req.headers.get("Content-Length", "")
        content_type = head_req.headers.get("Content-Type", "video/mp4")
    except:
        content_length = ""
        content_type = "video/mp4"
    
    return StreamingResponse(
        stream_generator(),
        media_type=content_type,
        headers={
            "Content-Disposition": 'attachment; filename="video.mp4"',
            "Content-Length": content_length,
            "Access-Control-Allow-Origin": "*"
        }
    )
