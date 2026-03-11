from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import requests
import random
import re
import urllib.parse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# YOUR 20 PROXIES (Essential to stop "Status 0" on Koyeb)
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

# EXACT HEADERS FROM YOUR PYDROID CODE
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 16; RMX3870 Build/BP2A.250605.015) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.7632.120 Mobile Safari/537.36",
    "Accept": "*/*",
    "Origin": "https://vidssave.com",
    "Referer": "https://vidssave.com/",
    "X-Requested-With": "mark.via.gp",
    "Content-Type": "application/x-www-form-urlencoded"
}

@app.get("/download/{url:path}")
async def get_video_data(url: str, request: Request):
    base_url = str(request.base_url).rstrip('/')
    
    # We try up to 5 proxies until one works
    for _ in range(5):
        proxy = random.choice(PROXIES)
        proxies_dict = {"http": proxy, "https": proxy}
        
        payload = {
            "auth": "20250901majwlqo",
            "domain": "api-ak.vidssave.com",
            "origin": "cache",
            "link": url
        }

        try:
            resp = requests.post(
                "https://api.vidssave.com/api/contentsite_api/media/parse", 
                data=payload, 
                headers=HEADERS, 
                proxies=proxies_dict, 
                timeout=10
            )
            data = resp.json()

            if data.get("status") == 1:
                video_info = data["data"]
                clean_formats = []
                
                for res in video_info.get("resources", []):
                    if res.get("download_mode") == "direct":
                        raw_dl_url = res.get("download_url")
                        encoded_url = urllib.parse.quote(raw_dl_url)
                        
                        clean_formats.append({
                            "q": res.get("quality"),
                            "f": res.get("format"),
                            "s": round(res.get("size", 0) / 1048576, 2),
                            "u": f"{base_url}/stream?url={encoded_url}"
                        })
                
                return {
                    "success": True,
                    "title": video_info.get("title"),
                    "thumbnail": video_info.get("thumbnail"),
                    "formats": clean_formats
                }
        except:
            continue
            
    return {"success": False, "error": "Proxies blocked by Vidssave. Check Webshare."}

@app.get("/stream")
async def stream_video(url: str = Query(...)):
    # Mimic the Pydroid header for the actual video stream
    s_headers = {"User-Agent": HEADERS["User-Agent"], "Referer": "https://vidssave.com/"}
    
    def generate():
        with requests.get(url, headers=s_headers, stream=True) as r:
            for chunk in r.iter_content(chunk_size=256*1024):
                yield chunk

    # Get file headers
    h = requests.head(url, headers=s_headers)
    
    return StreamingResponse(
        generate(),
        media_type="video/mp4",
        headers={
            "Content-Disposition": 'attachment; filename="video.mp4"',
            "Content-Length": h.headers.get("Content-Length", ""),
            "Access-Control-Allow-Origin": "*"
        }
    )
