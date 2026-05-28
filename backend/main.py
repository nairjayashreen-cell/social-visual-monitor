from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import vision
import requests
import os
import json
import shutil
from PIL import Image
import imagehash

# =========================================
# GOOGLE VISION CREDENTIALS
# =========================================

if os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON"):

    credentials_data = json.loads(
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    )

    with open("google-vision.json", "w") as f:
        json.dump(credentials_data, f)

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google-vision.json"

# =========================================
# FASTAPI INIT
# =========================================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================
# UPLOAD FOLDER
# =========================================

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# =========================================
# GOOGLE VISION CLIENT
# =========================================

vision_client = vision.ImageAnnotatorClient()

# =========================================
# APIFY CONFIG
# =========================================

APIFY_TOKEN = os.getenv("APIFY_TOKEN")

# YOUR APIFY DATASET ID
DATASET_ID = "xYIBUaWUK5ie0sxpg"

# =========================================
# IMAGE HASH COMPARISON
# =========================================

def compare_images(img1_path, img2_path):

    try:

        hash1 = imagehash.phash(Image.open(img1_path))
        hash2 = imagehash.phash(Image.open(img2_path))

        difference = hash1 - hash2

        similarity = 1 - (difference / 64)

        return similarity

    except Exception as e:

        print("HASH ERROR:", e)

        return 0

# =========================================
# HOME ROUTE
# =========================================

@app.get("/")
def home():

    return {
        "status": "AI Visual Threat Monitoring Running"
    }

# =========================================
# UPLOAD REFERENCE CREATIVE
# =========================================

@app.post("/upload")
async def upload_logo(file: UploadFile = File(...)):

    try:

        file_path = f"{UPLOAD_DIR}/reference_logo.png"

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {
            "message": "Reference creative uploaded successfully"
        }

    except Exception as e:

        return {
            "error": str(e)
        }

# =========================================
# SCAN INSTAGRAM POSTS
# =========================================

@app.get("/scan")
def scan():

    try:

        # =========================================
        # CHECK IF REFERENCE IMAGE EXISTS
        # =========================================

        reference_image = "uploads/reference_logo.png"

        if not os.path.exists(reference_image):

            return {
                "error": "Please upload reference creative first using /upload"
            }

        # =========================================
        # APIFY DATASET API
        # =========================================

        url = f"https://api.apify.com/v2/datasets/{DATASET_ID}/items?token={APIFY_TOKEN}"

        response = requests.get(url)

        print("STATUS CODE:", response.status_code)

        data = response.json()

        print("DATA TYPE:", type(data))

        # =========================================
        # HANDLE DIFFERENT JSON FORMATS
        # =========================================

        if isinstance(data, dict):

            if "items" in data:
                data = data["items"]

            else:
                data = []

        # =========================================
        # RESULTS
        # =========================================

        results = []

        # =========================================
        # LOOP THROUGH POSTS
        # =========================================

        for item in data:

            try:

                if not isinstance(item, dict):
                    continue

                image_url = item.get("displayUrl", "")

                if not image_url:
                    continue

                temp_image_path = "uploads/temp.jpg"

                # =========================================
                # DOWNLOAD IMAGE
                # =========================================

                try:

                    img_response = requests.get(image_url)

                    if img_response.status_code != 200:
                        continue

                    with open(temp_image_path, "wb") as handler:
                        handler.write(img_response.content)

                except Exception as e:

                    print("DOWNLOAD ERROR:", e)

                    continue

                # =========================================
                # IMAGE MATCHING
                # =========================================

                similarity = compare_images(
                    reference_image,
                    temp_image_path
                )

                print("SIMILARITY:", similarity)

                # =========================================
                # MATCH FOUND
                # =========================================

                if similarity > 0.30:

                    results.append({

                        "platform": "Instagram",

                        "username": item.get(
                            "ownerUsername",
                            "unknown"
                        ),

                        "url": item.get(
                            "url",
                            ""
                        ),

                        "image": image_url,

                        "brand": "Logo Match Found",

                        "score": f"{round(similarity * 100)}%",

                        "risk": "Critical",

                        "ocr": item.get(
                            "caption",
                            ""
                        )[:200],

                        "time": item.get(
                            "timestamp",
                            "recent"
                        )

                    })

            except Exception as item_error:

                print("ITEM ERROR:", item_error)

                continue

        # =========================================
        # RETURN RESULTS
        # =========================================

        return results

    except Exception as e:

        return {
            "error": str(e)
        }
