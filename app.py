from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import requests, random, re, time, urllib.parse, yt_dlp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# YOUR ACTUAL PROXIES FROM THE IMAGE
# I updated the credentials to match fqxzwtzv:c65sasel8qr8
PROXIES = [
    "http://fqxzwtzv:c65sasel8qr8@31.59.20.176:6754",
    "http://fqxzwtzv:c65sasel8qr8@23.95.150.145:6114",
    "http://fqxzwtzv:c65sasel8qr8@198.23.239.134:6540",
    "http://fqxzwtzv:c65sasel8qr8@45.38.107.97:6014",
    "http://fqxzwtzv:c65sasel8qr8@107.172.163.27:6543",
    "http://fqxzwtzv:c65sasel8qr8@198.105.121.200:6462",
    "http://fqxzwtzv:c65sasel8qr8@64.137.96.74:6641",
    "http://fqxzwtzv:c65sasel8qr8@216.10.27.159:6837",
    "http://fqxzwtzv:c65sasel8qr8@142.111.67.146:5611",
    "http://fqxzwtzv:c65sasel8qr8@191.96.254.138:6185"
]

@app.get("/download/{url:path}")
async def get_video(url: str, request: Request):
    base_url = str(request.base_url).rstrip('/')
    
    # Try Vidssave with your proxies first
    for _ in range(2):
        try:
            p = random.choice(PROXIES)
            r = requests.post("https://api.vidssave.com/api/contentsite_api/media/parse", 
                data={"auth": "20250901majwlqo", "domain": "api-ak.vidssave.com", "origin": "cache", "link": url},
                headers={"User-Agent": "Mozilla/5.0 (Linux; Android 10; K)"},
                proxies={"http": p, "https": p}, timeout=5)
            
            j = r.json()
            if j.get("status") == 1:
                data = j["data"]
                formats = [{"q": f.get("quality"), "f": f.get("format"), "s": round(f.get("size",0)/1048576, 1), 
                            "u": f"{base_url}/stream?url={urllib.parse.quote(f.get('download_url'))}"} 
                           for f in data.get("resources", []) if f.get("download_mode") == "direct"]
                return {"success": True, "title": data.get("title"), "formats": formats, "engine": "vidssave"}
        except: continue

    # FALLBACK: If proxies fail, use yt-dlp (This is your safety net)
    try:
        ydl_opts = {'quiet': True, 'format': 'best'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = [{"q": f.get('format_note','HD'), "f": f.get('ext','mp4').upper(), "s": "N/A", 
                        "u": f"{base_url}/stream?url={urllib.parse.quote(f.get('url'))}"} 
                       for f in info.get('formats', []) if f.get('acodec')!='none' and f.get('vcodec')!='none'][:5]
            return {"success": True, "title": info.get('title'), "thumbnail": info.get('thumbnail'), "formats": formats, "engine": "yt-dlp"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/stream")
async def stream_video(url: str = Query(...)):
    def generate():
        with requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, stream=True) as r:
            for chunk in r.iter_content(chunk_size=256*1024): yield chunk
    return StreamingResponse(generate(), media_type="video/mp4")
