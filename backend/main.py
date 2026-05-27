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
# FASTAPI SETUP
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
# DIRECTORIES
# =========================

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# =========================
# GOOGLE VISION CLIENT
# =========================

vision_client = vision.ImageAnnotatorClient()

# =========================
# APIFY CONFIG
# =========================

APIFY_TOKEN = os.getenv("APIFY_TOKEN")

# YOUR DATASET ID
DATASET_ID = "xYIBUaWUK5ie0sxpg"

# =========================
# IMAGE COMPARISON
# =========================

def compare_images(img1_path, img2_path):

    try:

        img1 = cv2.imread(img1_path)
        img2 = cv2.imread(img2_path)

        if img1 is None or img2 is None:
            return 0

        img1 = cv2.resize(img1, (300, 300))
        img2 = cv2.resize(img2, (300, 300))

        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        score, _ = ssim(gray1, gray2, full=True)

        return score

    except Exception as e:
        print("COMPARE ERROR:", e)
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
# UPLOAD REFERENCE IMAGE
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
# SCAN INSTAGRAM POSTS
# =========================

@app.get("/scan")
def scan():

    url = f"https://api.apify.com/v2/datasets/{DATASET_ID}/items?token={APIFY_TOKEN}"

    response = requests.get(url)

    try:
        data = response.json()
    except:
        return {
            "error": "Failed to fetch dataset data"
        }

    results = []

    reference_image = f"{UPLOAD_DIR}/reference_logo.png"

    if not os.path.exists(reference_image):

        return {
            "error": "Please upload a reference image first using /upload"
        }

    for item in data:

        image_url = item.get("displayUrl", "")

        if not image_url:
            continue

        temp_image_path = f"{UPLOAD_DIR}/temp.jpg"

        try:

            img_data = requests.get(image_url).content

            with open(temp_image_path, "wb") as handler:
                handler.write(img_data)

        except Exception as e:
            print("DOWNLOAD ERROR:", e)
            continue

        similarity = compare_images(
            reference_image,
            temp_image_path
        )

        # MATCH THRESHOLD
        if similarity > 0.45:

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

                "brand": "Creative Match Found",

                "score": f"{round(similarity * 100)}%",

                "risk": "Critical",

                "ocr": item.get(
                    "caption",
                    ""
                )[:200],

                "time": item.get(
                    "timestamp",
                    "recent"
                ),

                "image": image_url

            })

    return results
