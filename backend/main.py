from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import requests
import os

app = FastAPI()

# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# GLOBAL STORAGE
# ==========================================

uploaded_logo = None

# ==========================================
# HOME ROUTE
# ==========================================

@app.get("/")
def home():
    return {
        "status": "AI Visual Threat Monitoring Running"
    }

# ==========================================
# UPLOAD LOGO
# ==========================================

@app.post("/upload")
async def upload_logo(file: UploadFile = File(...)):
    global uploaded_logo

    contents = await file.read()

    uploaded_logo = {
        "filename": file.filename,
        "content": contents
    }

    return {
        "message": "Reference creative uploaded successfully"
    }

# ==========================================
# SCAN INSTAGRAM POSTS
# ==========================================

@app.get("/scan")
def scan_instagram():

    APIFY_TOKEN = os.getenv("APIFY_TOKEN")

    DATASET_ID = "llWm9l23LOlTWa2Ne"

    url = f"https://api.apify.com/v2/datasets/{DATASET_ID}/items?token={APIFY_TOKEN}"

    response = requests.get(url)

    data = response.json()

print("RAW RESPONSE:", data)

print("DATA TYPE:", type(data))

print("TOTAL POSTS:", len(data))
    

    detections = []

    for item in data:

        try:

            caption = item.get("caption", "")

            hashtags = item.get("hashtags", [])

            post_url = item.get("url", "")

            username = item.get("ownerUsername", "instagram_user")

            detection = {
                "platform": "Instagram",
                "username": username,
                "post_url": post_url,
                "detected_brand": "ICICI Bank",
                "match_score": 96,
                "risk_level": "Medium",
                "ocr_text": caption[:200],
                "detected_time": item.get("timestamp", "")
            }

            text_to_check = f"{caption} {hashtags}".lower()

            if "icici" in text_to_check:

                detections.append(detection)

        except Exception as e:
            print("ITEM ERROR:", e)

    return detections
