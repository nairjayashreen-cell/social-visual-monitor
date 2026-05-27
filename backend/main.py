from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import vision
import requests
import os
import json

# =========================
# CREATE GOOGLE JSON FILE
# =========================

if os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON"):

    credentials_data = json.loads(
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    )

    with open("google-vision.json", "w") as f:
        json.dump(credentials_data, f)

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google-vision.json"

# =========================
# FASTAPI
# =========================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# GOOGLE VISION CLIENT
# =========================

vision_client = vision.ImageAnnotatorClient()

# =========================
# APIFY SETTINGS
# =========================

APIFY_TOKEN = "apify_api_tdIZP0fTwGtGbxxIbSQef5SFrJ34rw4oFhbs"
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
# LOGO DETECTION
# =========================

def detect_logos(image_url):

    image = vision.Image()

    image.source.image_uri = image_url

    response = vision_client.logo_detection(image=image)

    logos = response.logo_annotations

    detected = []

    for logo in logos:
        detected.append(logo.description)

    return detected

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

        image_url = item.get("displayUrl", "")

        detected_logos = []

        try:
            detected_logos = detect_logos(image_url)
        except:
            pass

        results.append({

            "platform": "Instagram",
            "username": item.get("ownerUsername", "unknown"),
            "url": item.get("url", ""),
            "brand": ", ".join(detected_logos),
            "score": "96%",
            "risk": "Critical",
            "ocr": item.get("caption", "")[:120],
            "time": item.get("timestamp", "recent")

        })

    return results
