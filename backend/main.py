from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# APIFY SETTINGS
# =========================

APIFY_TOKEN = "apify_api_T71OkLS49xPSybQkNM64wnnatP0Z521Scn6Z"

# Replace with your Dataset ID
DATASET_ID = "xYIBUaWUK5ie0sxpg"

# =========================
# HOME
# =========================

@app.get("/")
def home():
    return {
        "status": "AI Visual Threat Monitoring API Running"
    }

# =========================
# LIVE SCAN
# =========================

@app.get("/scan")
def scan():

    url = f"https://api.apify.com/v2/datasets/{DATASET_ID}/items?token={APIFY_TOKEN}"

    response = requests.get(url)

    data = response.json()

    results = []

    for item in data:

        try:

            results.append({
                "platform": "Instagram",
                "username": item.get("ownerUsername", "unknown"),
                "url": item.get("url", ""),
                "brand": "Detected Brand",
                "score": "96%",
                "risk": "Critical",
                "ocr": item.get("caption", "")[:120],
                "time": item.get("timestamp", "recent")
            })

        except:
            pass

    return results
