from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import requests, random, re, time, urllib.parse

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# YOUR PROXIES (Update with your verified fqxzwtzv credentials)
PROXIES = [
    "http://fqxzwtzv:c65sasel8qr8@31.59.20.176:6754",
    "http://fqxzwtzv:c65sasel8qr8@23.95.150.145:6114",
    "http://fqxzwtzv:c65sasel8qr8@198.23.239.134:6540"
]

@app.get("/download/{url:path}")
async def get_data(url: str, request: Request):
    # Extract Video ID
    match = re.search(r"(?:v=|\/|be\/)([0-9A-Za-z_-]{11})", url)
    if not match: return {"success": False, "error": "Invalid Link"}
    vid = match.group(1)
    base_url = str(request.base_url).rstrip('/')

    # --- SOURCE 1: Optimized Vidssave Scraper ---
    for _ in range(2):
        try:
            p = random.choice(PROXIES)
            payload = {"auth": "20250901majwlqo", "domain": "api-ak.vidssave.com", "origin": "cache", "link": url}
            headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
                "Referer": "https://vidssave.com/",
                "X-Requested-With": "mark.via.gp"
            }
            r = requests.post("https://api.vidssave.com/api/contentsite_api/media/parse", 
                             data=payload, headers=headers, proxies={"http": p, "https": p}, timeout=6)
            j = r.json()
            if j.get("status") == 1:
                data = j["data"]
                formats = [{"q": f.get("quality"), "f": f.get("format"), "s": round(f.get("size",0)/1048576, 1), 
                            "u": f"{base_url}/stream?url={urllib.parse.quote(f.get('download_url'))}"} 
                           for f in data.get("resources", []) if f.get("download_mode") == "direct"]
                return {"success": True, "title": data.get("title"), "thumbnail": data.get("thumbnail"), "formats": formats}
        except: continue

    # --- SOURCE 2: Fast Fallback (API.SOCIAL) ---
    # This uses almost ZERO ram compared to yt-dlp
    try:
        r2 = requests.get(f"https://api.socialdownloader.info/info?url={url}", timeout=5)
        j2 = r2.json()
        if j2.get("success"):
            formats = [{"q": "720p", "f": "MP4", "s": "N/A", "u": f"{base_url}/stream?url={urllib.parse.quote(j2['links'][0]['url'])}"}]
            return {"success": True, "title": j2.get("title"), "thumbnail": j2.get("thumbnail"), "formats": formats}
    except: pass

    return {"success": False, "error": "All sources busy. Vidssave blocked these proxies."}

@app.get("/stream")
async def stream_video(url: str = Query(...)):
    # Memory efficient streaming: 64KB chunks
    def generate():
        with requests.get(url, stream=True, timeout=15) as r:
            for chunk in r.iter_content(chunk_size=65536):
                yield chunk
    return StreamingResponse(generate(), media_type="video/mp4")
