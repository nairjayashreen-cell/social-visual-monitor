```python
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import requests
import shutil
import os

from ai.similarity import compare_images

app = FastAPI()

# =========================================
# CORS
# =========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================
# CONFIG
# =========================================

DATASET_ID = "llWm9l23LOlTWa2Ne"

reference_image = None

# =========================================
# HOME ROUTE
# =========================================

@app.get("/")
def home():
    return {
        "status": "AI Visual Threat Monitoring Running"
    }

# =========================================
# UPLOAD REFERENCE LOGO
# =========================================

@app.post("/upload")
async def upload_logo(file: UploadFile = File(...)):

    global reference_image

    os.makedirs("reference", exist_ok=True)

    file_path = f"reference/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    reference_image = file_path

    return {
        "message": "Reference creative uploaded successfully"
    }

# =========================================
# SCAN INSTAGRAM POSTS
# =========================================

@app.get("/scan")
def scan():

    global reference_image

    if not reference_image:
        return {"error": "Upload reference image first"}

    detections = []

    dataset_url = f"https://api.apify.com/v2/datasets/{DATASET_ID}/items?clean=true"

    response = requests.get(dataset_url)

    data = response.json()

    print("TOTAL POSTS:", len(data))

    for item in data:

        try:

            image_urls = []

            # =========================================
            # CASE 1 → MULTIPLE IMAGES
            # =========================================

            if isinstance(item.get("images"), list):
                image_urls.extend(item.get("images"))

            # =========================================
            # CASE 2 → SINGLE IMAGE
            # =========================================

            if item.get("displayUrl"):
                image_urls.append(item.get("displayUrl"))

            print("FOUND IMAGES:", len(image_urls))

            for image_url in image_urls:

                try:

                    print("CHECKING:", image_url)

                    img_response = requests.get(image_url)

                    temp_image_path = "temp_scan.jpg"

                    with open(temp_image_path, "wb") as f:
                        f.write(img_response.content)

                    # =========================================
                    # IMAGE COMPARISON
                    # =========================================

                    similarity = compare_images(
                        reference_image,
                        temp_image_path
                    )

                    print("SIMILARITY:", similarity)

                    # =========================================
                    # MATCH FOUND
                    # =========================================

                    if similarity > 25:

                        detections.append({
                            "platform": "Instagram",
                            "username": item.get("ownerUsername", "unknown"),
                            "url": item.get("url", ""),
                            "brand": "Logo Match Found",
                            "score": f"{round(similarity, 2)}%",
                            "risk": "Critical"
                        })

                        print("MATCH FOUND")

                except Exception as img_error:
                    print("IMAGE ERROR:", img_error)

        except Exception as e:
            print("ITEM ERROR:", e)

    return detections
```
