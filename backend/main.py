from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import vision
import requests
import os
import json
import shutil
import cv2
from skimage.metrics import structural_similarity as ssim

# =========================
# GOOGLE VISION SETUP
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
# FOLDERS
# =========================

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# =========================
# GOOGLE CLIENT
# =========================

vision_client = vision.ImageAnnotatorClient()

# =========================
# APIFY
# =========================

APIFY_TOKEN = os.getenv("APIFY_TOKEN")
DATASET_ID = "xYIBUaWUK5ie0sxpg"

# =========================
# IMAGE COMPARISON
# =========================

def compare_images(img1_path, img2_path):

    try:

        img1 = cv2.imread(img1_path)
        img2 = cv2.imread(img2_path)

        img1 = cv2.resize(img1, (300, 300))
        img2 = cv2.resize(img2, (300, 300))

        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        score, _ = ssim(gray1, gray2, full=True)

        return score

    except:
        return 0

# =========================
# HOME
# =========================

@app.get("/")
def home():

    return {
        "status": "AI Visual Threat Monitoring Running"
    }

# =========================
# UPLOAD LOGO
# =========================

@app.post("/upload")
async def upload_logo(file: UploadFile = File(...)):

    file_path = f"{UPLOAD_DIR}/reference_logo.png"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "message": "Reference creative uploaded successfully"
    }

# =========================
# SCAN
# =========================

@app.get("/scan")
def scan():

    try:

        url = f"https://api.apify.com/v2/datasets/{DATASET_ID}/items?token={APIFY_TOKEN}"

        response = requests.get(url)

        data = response.json()

        results = []

        for item in data:

            image_url = item.get("displayUrl", "")

            if not image_url:
                continue

            temp_image_path = "uploads/temp.jpg"

            try:

                img_data = requests.get(image_url).content

                with open(temp_image_path, 'wb') as handler:
                    handler.write(img_data)

            except Exception as e:
                print("IMAGE DOWNLOAD ERROR:", e)
                continue

            similarity = compare_images(
                "uploads/reference_logo.png",
                temp_image_path
            )

            if similarity > 0.45:

                results.append({

                    "platform": "Instagram",
                    "username": item.get("ownerUsername", "unknown"),
                    "url": item.get("url", ""),
                    "brand": "Logo Match Found",
                    "score": f"{round(similarity * 100)}%",
                    "risk": "Critical",
                    "ocr": item.get("caption", "")[:120],
                    "time": item.get("timestamp", "recent")

                })

        return results

    except Exception as e:

        return {
            "error": str(e)
        }
