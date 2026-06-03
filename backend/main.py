from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
import os
import pandas as pd
from fastapi.responses import FileResponse

import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
from PIL import Image

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

def compare_logo(logo_path, image_path):

    try:

        logo = cv2.imread(logo_path)
        image = cv2.imread(image_path)

        if logo is None or image is None:
            return 0

        logo_gray = cv2.cvtColor(
            logo,
            cv2.COLOR_BGR2GRAY
        )

        image_gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )

        image_gray = cv2.resize(
            image_gray,
            (
                logo_gray.shape[1],
                logo_gray.shape[0]
            )
        )

        score, _ = ssim(
            logo_gray,
            image_gray,
            full=True
        )

        return round(score * 100, 2)

    except:
        return 0

def download_image(url, filename):

    response = requests.get(url)

    with open(filename, "wb") as f:
        f.write(response.content)

    return filename

# ==========================================
# BRAND CONFIGURATION
# ==========================================

BRANDS = {
    "ICICI": {
        "dataset_id": "kEaw2FDvOje5FYEH8"
    },
    "Groww": {
        "dataset_id": "UXNdHqAR3NV84I4yK"
    },
    "Motilal Oswal": {
        "dataset_id": "jxqI2FhmwKxANA7ID"
    },
    "Tata Capital": {
        "dataset_id": "0lPf4mavgwrO3Htde"
    },
    "Zerodha": {
        "dataset_id": "nHeWy0j1RLe9eyKVD"
    },
    "Upstox": {
        "dataset_id": "s2xel18LTiGzunXjS"
    },
    "SBI": {
        "dataset_id": "bwXcVBwdWc6OvnSmU"
    },
    "Anand Rathi": {
        "dataset_id": "WaccQaOU5HTHAgRAr"
    }
}

# ==========================================
# HOME
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

    os.makedirs("uploads", exist_ok=True)

    filepath = f"uploads/{file.filename}"

    with open(filepath, "wb") as buffer:
        buffer.write(await file.read())

    uploaded_logo = filepath

    return {
        "message": "Logo uploaded successfully",
        "file": filepath
    }

# ==========================================
# DASHBOARD
# ==========================================

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():

    options = ""

    for brand in BRANDS.keys():
        options += f'<option value="{brand}">{brand}</option>'

    return f"""
    <html>

    <head>

        <title>AI Visual Threat Monitoring</title>

        <style>

            body {{
                font-family: Arial, sans-serif;
                background:#f5f6fa;
                padding:40px;
            }}

            h1 {{
                color:#222;
            }}

            select {{
                padding:12px;
                width:300px;
                font-size:16px;
            }}

            button {{
                padding:12px 20px;
                background:#0d6efd;
                color:white;
                border:none;
                cursor:pointer;
                margin-left:10px;
            }}

        </style>

    </head>

    <body>

        <h1>Instagram Brand Monitoring Dashboard</h1>

        <form action="/scan" method="get">

            <select name="brand">
                {options}
            </select>

            <button type="submit">
                Scan Brand
            </button>

        </form>

    </body>

    </html>
    """

# ==========================================
# SCAN INSTAGRAM
# ==========================================

@app.get("/scan", response_class=HTMLResponse)
def scan_instagram(brand: str):

    APIFY_TOKEN = os.getenv("APIFY_TOKEN")

    if not APIFY_TOKEN:
        return """
        <h2>Missing APIFY_TOKEN environment variable</h2>
        """

    if brand not in BRANDS:
        return f"""
        <h2>Unknown Brand: {brand}</h2>
        """

    dataset_id = BRANDS[brand]["dataset_id"]

    url = (
        f"https://api.apify.com/v2/datasets/"
        f"{dataset_id}/items?token={APIFY_TOKEN}"
    )

    try:

        response = requests.get(url)
        data = response.json()
        total_records = len(data) if isinstance(data, list) else 0

        print("BRAND:", brand)
        print("UPLOADED LOGO:", uploaded_logo)
        print("DATASET:", dataset_id)
        print("DATA TYPE:", type(data))

        detections = []

        if isinstance(data, list):

            for post in data:

                                try:

                    caption = str(
                        post.get("caption", "")
                    ).replace("\n", " ")

                    published_date = post.get(
                        "timestamp",
                        ""
                    )

                    print("POST DATE:", published_date)

                    image_url = post.get(
                        "displayUrl",
                        ""
                    )

                    score = 0

                    if uploaded_logo and image_url:

                        downloaded_image = download_image(
                            image_url,
                            "temp_image.jpg"
                        )

                        score = compare_logo(
                            uploaded_logo,
                            downloaded_image
                        )
                    if score >= 70:
                        risk = "High"
                    elif score >= 40:
                        risk = "Medium"
                    else:
                        risk = "Low"

                    detections.append({

                        "platform": "Instagram",

                        "username": post.get(
                            "ownerUsername",
                            "unknown"
                        ),

                        "publishedDate": published_date,

                        "postUrl": post.get(
                            "url",
                            "#"
                        ),

                        "detectedBrand": brand,

                        "matchScore": f"{score}%",

                        "risk": risk,

                        "description": (
                            caption[:120] + "..."
                            if len(caption) > 120
                            else caption
                        )

                    })
                    
                    
                except Exception as item_error:

                    print(
                        "ITEM ERROR:",
                        item_error
                    )

       

        html = f"""
        
        

        <html>

        <head>

            <title>{brand} Monitoring</title>

            <style>

                body {{
                    font-family: Arial, sans-serif;
                    background:#f8f9fa;
                    margin:30px;
                }}

                h1 {{
                    color:#333;
                }}

                .count {{
                    margin-bottom:20px;
                    font-size:20px;
                    font-weight:bold;
                }}

                table {{
                    width:100%;
                    border-collapse:collapse;
                    background:white;
                }}

                th {{
                    background:#0d6efd;
                    color:white;
                    padding:12px;
                    text-align:left;
                }}

                td {{
                    padding:10px;
                    border-bottom:1px solid #ddd;
                    vertical-align:top;
                }}

                tr:hover {{
                    background:#f5f5f5;
                }}

                a {{
                    color:#0d6efd;
                    text-decoration:none;
                }}

                .brand {{
                    color:#0d6efd;
                    font-weight:bold;
                }}

            </style>

        </head>

        <body>

            <h1>{brand} Brand Monitoring</h1>

        <div class="count">
    Brand: {brand}<br>
    Dataset Records: {total_records}<br>
    Posts Displayed: {len(detections)}<br>
    Last Updated: {datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d %b %Y %I:%M %p IST")}
</div>

            <p>
                <a href="/dashboard">
                    ← Back to Dashboard
                </a>
            </p>

            <table>

                <tr>
                    <th>Platform</th>
                    <th>Username</th>
                    <th>Published Date</th>
                    <th>Brand</th>
                    <th>Description</th>
                    <th>Risk</th>
                    <th>Score</th>
                    <th>Post</th>
                </tr>

        """
        
        detections.sort(
            key=lambda x: float(
                str(x["matchScore"]).replace("%", "")
            ),
            reverse=True
        )
      
        for item in detections:

            html += f"""

            <tr>

                <td>{item['platform']}</td>

                <td>{item['username']}</td>
                
                <td>{item['publishedDate']}</td>

                <td>
                    <span class="brand">
                        {item['detectedBrand']}
                    </span>
                </td>

                <td>{item['description']}</td>

                <td>{item['risk']}</td>

                <td>{item['matchScore']}</td>

                <td>

                    <a
                        href="{item['postUrl']}"
                        target="_blank"
                    >
                        View Post
                    </a>

                </td>

            </tr>

            """

        html += """

            </table>

        </body>

        </html>

        """

        return html

    except Exception as e:

        print("SCAN ERROR:", e)

        return f"""
        <h2>Error</h2>
        <p>{str(e)}</p>
        """
# ==========================================
# EXPORT EXCEL
# ==========================================

@app.get("/export")
def export_excel(brand: str):

    return {
        "message": f"Export endpoint working for {brand}"
    }
