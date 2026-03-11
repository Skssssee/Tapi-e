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

# --- FULL 20 PROXY LIST ---
PROXIES = [
    "http://fqxzwtzv:c65sasel8qr8@31.59.20.176:6754", "http://fqxzwtzv:c65sasel8qr8@23.95.150.145:6114",
    "http://fqxzwtzv:c65sasel8qr8@198.23.239.134:6540", "http://fqxzwtzv:c65sasel8qr8@45.38.107.97:6014",
    "http://fqxzwtzv:c65sasel8qr8@107.172.163.27:6543", "http://fqxzwtzv:c65sasel8qr8@198.105.121.200:6462",
    "http://fqxzwtzv:c65sasel8qr8@64.137.96.74:6641", "http://fqxzwtzv:c65sasel8qr8@216.10.27.159:6837",
    "http://fqxzwtzv:c65sasel8qr8@142.111.67.146:5611", "http://fqxzwtzv:c65sasel8qr8@191.96.254.138:6185",
    "http://uppezuyk:c2bfaa6diuyf@31.59.20.176:6754", "http://uppezuyk:c2bfaa6diuyf@23.95.150.145:6114",
    "http://uppezuyk:c2bfaa6diuyf@198.23.239.134:6540", "http://uppezuyk:c2bfaa6diuyf@45.38.107.97:6014",
    "http://uppezuyk:c2bfaa6diuyf@107.172.163.27:6543", "http://uppezuyk:c2bfaa6diuyf@198.105.121.200:6462",
    "http://uppezuyk:c2bfaa6diuyf@64.137.96.74:6641", "http://uppezuyk:c2bfaa6diuyf@216.10.27.159:6837",
    "http://uppezuyk:c2bfaa6diuyf@142.111.67.146:5611", "http://uppezuyk:c2bfaa6diuyf@191.96.254.138:6185"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 11; RMX3870) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Referer": "https://vidssave.com/",
    "X-Requested-With": "mark.via.gp"
}

@app.get("/")
def root():
    return {"status": "Koyeb API Active", "proxies": len(PROXIES)}

@app.get("/download/{url:path}")
async def get_video(url: str, request: Request):
    # FORCE HTTPS to fix the 0.01kb / mixed content error
    base_url = str(request.base_url).replace("http://", "https://").rstrip('/')
    
    match = re.search(r"(?:v=|\/|be\/)([0-9A-Za-z_-]{11})", url)
    if not match: return {"success": False, "error": "Invalid URL"}
    target = f"https://www.youtube.com/watch?v={match.group(1)}"

    random.shuffle(PROXIES)
    for proxy in PROXIES:
        try:
            r = requests.post("https://api.vidssave.com/api/contentsite_api/media/parse", 
                data={"auth": "20250901majwlqo", "domain": "api-ak.vidssave.com", "origin": "cache", "link": target},
                headers=HEADERS, proxies={"http": proxy, "https": proxy}, timeout=7)
            
            res = r.json()
            if res.get("status") == 1:
                data = res["data"]
                formats = []
                for f in data.get("resources", []):
                    if f.get("download_mode") == "direct":
                        encoded = urllib.parse.quote(f.get("download_url"))
                        formats.append({
                            "q": f.get("quality"),
                            "f": f.get("format"),
                            "s": round(f.get("size", 0)/1048576, 1),
                            "u": f"{base_url}/stream?url={encoded}"
                        })
                return {"success": True, "title": data.get("title"), "thumbnail": data.get("thumbnail"), "formats": formats}
        except: continue
    return {"success": False, "error": "All proxies failed. Status 0."}

@app.get("/stream")
async def stream_video(url: str = Query(...)):
    # Stream with headers to fix Forbidden and 0.01kb errors
    def generate():
        with requests.get(url, headers=HEADERS, stream=True, timeout=30) as r:
            for chunk in r.iter_content(chunk_size=131072): # 128KB chunks
                if chunk: yield chunk

    try:
        head = requests.head(url, headers=HEADERS, timeout=10)
        size = head.headers.get("Content-Length")
    except: size = None

    headers = {
        "Content-Disposition": 'attachment; filename="video.mp4"',
        "Accept-Ranges": "bytes",
        "Access-Control-Allow-Origin": "*"
    }
    if size: headers["Content-Length"] = size

    return StreamingResponse(generate(), media_type="video/mp4", headers=headers)
