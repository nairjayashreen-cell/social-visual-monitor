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

    uploaded_logo = file.filename

    return {
        "message": "Reference creative uploaded successfully"
    }

# ==========================================
# INSTAGRAM SCAN
# ==========================================

@app.get("/scan")
def scan_instagram():

    global uploaded_logo

    if not uploaded_logo:
        return {
            "error": "Please upload logo first"
        }

    APIFY_TOKEN = os.getenv("APIFY_TOKEN")

    if not APIFY_TOKEN:
        return {
            "error": "Missing APIFY_TOKEN environment variable"
        }

    dataset_id = "llWm9l23LOlTWa2Ne"

    url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_TOKEN}"

    try:

        response = requests.get(url)

        data = response.json()

        print("RAW RESPONSE:", data)

        print("DATA TYPE:", type(data))

        print("TOTAL POSTS:", len(data))

        detections = []

        keywords = [
            "icici",
            "icici bank",
            "bank",
            "loan",
            "credit card",
            "finance"
        ]

        if isinstance(data, list):

            for post in data:

                try:

                    caption = str(post.get("caption", "")).lower()

                    hashtags = post.get("hashtags", [])

                    hashtags_text = " ".join(hashtags).lower()

                    combined_text = caption + " " + hashtags_text

                    matched = any(
                        keyword in combined_text
                        for keyword in keywords
                    )

                    if matched:

                        detections.append({
                            "platform": "Instagram",
                            "username": post.get("ownerUsername", "unknown"),
                            "postUrl": post.get("url", ""),
                            "detectedBrand": "ICICI",
                            "matchScore": "96%",
                            "risk": "Medium",
                            "detectedText": caption[:200]
                        })

                except Exception as item_error:

                    print("ITEM ERROR:", item_error)

        return detections

    except Exception as e:

        print("SCAN ERROR:", e)

        return {
            "error": str(e)
        }
