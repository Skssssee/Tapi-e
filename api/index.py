from fastapi import FastAPI
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

# --- ACCOUNT-BASED PROXY GROUPS ---
ACC_1_PROXIES = [
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

ACC_2_PROXIES = [
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

VIDEO_CACHE = {}
CACHE_TIME = 900 

def extract_id(url: str):
    match = re.search(r"(?:v=|\/|be\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

def fetch_from_provider(target_url, proxy_list):
    """Helper function to try a specific proxy group"""
    for _ in range(2): # Try 2 random IPs from the group
        proxy = random.choice(proxy_list)
        try:
            payload = {
                "auth": "20250901majwlqo",
                "domain": "api-ak.vidssave.com",
                "origin": "cache",
                "link": target_url
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://vidssave.com/",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            r = requests.post(
                "https://api.vidssave.com/api/contentsite_api/media/parse",
                data=payload, headers=headers,
                proxies={"http": proxy, "https": proxy},
                timeout=5 # Short timeout for quick switching
            )
            res = r.json()
            # If provider says OK and we have data, return it
            if res.get("status") == 1 and "data" in res:
                return res["data"]
            # If bandwidth is over, the response usually isn't status 1
        except:
            continue
    return None

@app.get("/download/{url:path}")
async def get_video(url: str):
    vid = extract_id(url)
    if not vid:
        return {"success": False, "error": "Invalid Link"}

    # 1. CHECK CACHE
    now = time.time()
    if vid in VIDEO_CACHE and now < VIDEO_CACHE[vid]["expires"]:
        return {**VIDEO_CACHE[vid]["data"], "cached": True}

    target_url = f"https://www.youtube.com/watch?v={vid}"
    
    # 2. TRY ACCOUNT 1 FIRST
    result_data = fetch_from_provider(target_url, ACC_1_PROXIES)
    
    # 3. AUTO-FALLBACK: IF ACCOUNT 1 FAILED, TRY ACCOUNT 2
    if not result_data:
        print("Account 1 failed/empty. Switching to Account 2...")
        result_data = fetch_from_provider(target_url, ACC_2_PROXIES)

    # 4. PROCESS FINAL DATA
    if result_data:
        final_output = {
            "success": True,
            "title": result_data.get("title"),
            "thumbnail": result_data.get("thumbnail"),
            "formats": [
                {
                    "q": f.get("quality"),
                    "f": f.get("format"),
                    "s": round(f.get("size", 0) / 1048576, 1),
                    "u": f.get("download_url")
                } for f in result_data.get("resources", []) if f.get("download_mode") == "direct"
            ]
        }
        VIDEO_CACHE[vid] = {"data": final_output, "expires": now + CACHE_TIME}
        return {**final_output, "cached": False}

    return {"success": False, "error": "All proxy accounts are busy or out of bandwidth."}
