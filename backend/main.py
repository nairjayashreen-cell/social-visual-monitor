from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
import os
import json
import pandas as pd

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
# LOGO STATE — persisted to disk so it
# survives worker restarts and multi-worker
# ==========================================

LOGO_STATE_FILE = "/tmp/logo_state.json"
UPLOAD_DIR = "/tmp/uploads"

def get_logo_path():
    """Read the current logo path from disk."""
    try:
        with open(LOGO_STATE_FILE, "r") as f:
            state = json.load(f)
            path = state.get("logo_path")
            if path and os.path.exists(path):
                return path
    except Exception:
        pass
    return None

def set_logo_path(path):
    """Write the current logo path to disk."""
    with open(LOGO_STATE_FILE, "w") as f:
        json.dump({"logo_path": path}, f)

# ==========================================
# HELPERS
# ==========================================

def compare_logo(logo_path, image_path):
    try:
        logo = cv2.imread(logo_path)
        image = cv2.imread(image_path)

        if logo is None or image is None:
            return 0

        logo_gray = cv2.cvtColor(logo, cv2.COLOR_BGR2GRAY)
        image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        image_gray = cv2.resize(
            image_gray,
            (logo_gray.shape[1], logo_gray.shape[0])
        )

        score, _ = ssim(logo_gray, image_gray, full=True)
        return round(score * 100, 2)

    except Exception:
        return 0

def download_image(url, filename):
    response = requests.get(url, timeout=15)
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
    return {"status": "AI Visual Threat Monitoring Running"}

# ==========================================
# UPLOAD LOGO
# ==========================================

@app.post("/upload")
async def upload_logo(file: UploadFile = File(...)):

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filepath = os.path.join(UPLOAD_DIR, file.filename)

    with open(filepath, "wb") as buffer:
        buffer.write(await file.read())

    set_logo_path(filepath)

    return {
        "message": "Logo uploaded successfully",
        "file": filepath,
        "status": "ready_to_scan"
    }

# ==========================================
# LOGO STATUS
# ==========================================

@app.get("/logo-status")
def logo_status():
    path = get_logo_path()
    if path:
        return {
            "uploaded": True,
            "filename": os.path.basename(path),
            "path": path
        }
    return {"uploaded": False}

# ==========================================
# DASHBOARD
# ==========================================

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():

    logo_path = get_logo_path()
    logo_filename = os.path.basename(logo_path) if logo_path else None

    logo_status_html = (
        f'<div class="logo-ok">✅ Logo loaded: <strong>{logo_filename}</strong> — ready to scan</div>'
        if logo_path else
        '<div class="logo-warn">⚠️ No logo uploaded yet. Upload one below before scanning.</div>'
    )

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
                background: #f5f6fa;
                padding: 40px;
                max-width: 800px;
                margin: 0 auto;
            }}
            h1 {{ color: #222; margin-bottom: 8px; }}
            h2 {{ color: #444; margin-top: 32px; }}

            .logo-ok {{
                background: #d1fae5;
                border: 1px solid #6ee7b7;
                color: #065f46;
                padding: 12px 16px;
                border-radius: 6px;
                margin-bottom: 24px;
                font-size: 15px;
            }}
            .logo-warn {{
                background: #fef3c7;
                border: 1px solid #fcd34d;
                color: #92400e;
                padding: 12px 16px;
                border-radius: 6px;
                margin-bottom: 24px;
                font-size: 15px;
            }}

            .card {{
                background: white;
                border-radius: 8px;
                padding: 24px;
                margin-bottom: 24px;
                box-shadow: 0 1px 4px rgba(0,0,0,0.08);
            }}

            input[type=file] {{
                display: block;
                margin: 12px 0;
                font-size: 15px;
            }}

            select {{
                padding: 10px;
                width: 280px;
                font-size: 15px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }}

            button {{
                padding: 10px 20px;
                background: #0d6efd;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 15px;
                margin-left: 10px;
            }}
            button:hover {{ background: #0b5ed7; }}

            .upload-btn {{
                margin-left: 0;
                background: #198754;
            }}
            .upload-btn:hover {{ background: #157347; }}

            #upload-result {{
                margin-top: 10px;
                font-size: 14px;
                color: #333;
            }}
        </style>
    </head>
    <body>

        <h1>🛡️ Instagram Brand Monitoring</h1>

        {logo_status_html}

        <!-- STEP 1: Upload Logo -->
        <div class="card">
            <h2>Step 1 — Upload Brand Logo</h2>
            <p>Upload the logo image you want to compare against Instagram posts.</p>
            <input type="file" id="logoFile" accept="image/*">
            <button class="upload-btn" onclick="uploadLogo()">Upload Logo</button>
            <div id="upload-result"></div>
        </div>

        <!-- STEP 2: Scan -->
        <div class="card">
            <h2>Step 2 — Scan a Brand</h2>
            <form action="/scan" method="get">
                <select name="brand">
                    {options}
                </select>
                <button type="submit">Scan Brand</button>
            </form>
        </div>

        <script>
            async function uploadLogo() {{
                const fileInput = document.getElementById('logoFile');
                const resultDiv = document.getElementById('upload-result');

                if (!fileInput.files.length) {{
                    resultDiv.innerHTML = '⚠️ Please select a file first.';
                    return;
                }}

                resultDiv.innerHTML = 'Uploading...';

                const formData = new FormData();
                formData.append('file', fileInput.files[0]);

                try {{
                    const response = await fetch('/upload', {{
                        method: 'POST',
                        body: formData
                    }});
                    const data = await response.json();
                    if (data.status === 'ready_to_scan') {{
                        resultDiv.innerHTML = '✅ Logo uploaded: <strong>' + fileInput.files[0].name + '</strong>. You can now scan.';
                        // Refresh to update the status banner
                        setTimeout(() => location.reload(), 1200);
                    }} else {{
                        resultDiv.innerHTML = '❌ Upload failed: ' + JSON.stringify(data);
                    }}
                }} catch (err) {{
                    resultDiv.innerHTML = '❌ Error: ' + err.message;
                }}
            }}
        </script>

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
        return "<h2>Missing APIFY_TOKEN environment variable</h2>"

    if brand not in BRANDS:
        return f"<h2>Unknown Brand: {brand}</h2>"

    logo_path = get_logo_path()

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
        print("LOGO PATH:", logo_path)
        print("DATASET:", dataset_id)

        detections = []

        if isinstance(data, list):

            for post in data:

                try:

                    caption = str(
                        post.get("caption", "")
                    ).replace("\n", " ")

                    published_date = post.get("timestamp", "")
                    image_url = post.get("displayUrl", "")

                    score = 0

                    if logo_path and image_url:
                        downloaded_image = download_image(
                            image_url,
                            "/tmp/temp_image.jpg"
                        )
                        score = compare_logo(logo_path, downloaded_image)

                    if score >= 70:
                        risk = "High"
                    elif score >= 40:
                        risk = "Medium"
                    else:
                        risk = "Low"

                    detections.append({
                        "platform": "Instagram",
                        "username": post.get("ownerUsername", "unknown"),
                        "publishedDate": published_date,
                        "postUrl": post.get("url", "#"),
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
                    print("ITEM ERROR:", item_error)

        detections.sort(
            key=lambda x: float(str(x["matchScore"]).replace("%", "")),
            reverse=True
        )

        logo_banner = (
            f'<div class="logo-ok">✅ Logo used: <strong>{os.path.basename(logo_path)}</strong></div>'
            if logo_path else
            '<div class="logo-warn">⚠️ No logo was uploaded — all scores are 0%. <a href="/dashboard">Go upload a logo</a> first.</div>'
        )

        rows = ""
        for item in detections:
            risk_color = {
                "High": "#dc3545",
                "Medium": "#fd7e14",
                "Low": "#198754"
            }.get(item["risk"], "#333")

            rows += f"""
            <tr>
                <td>{item['platform']}</td>
                <td><strong>{item['username']}</strong></td>
                <td>{item['publishedDate']}</td>
                <td><span style="color:#0d6efd;font-weight:bold">{item['detectedBrand']}</span></td>
                <td>{item['description']}</td>
                <td style="color:{risk_color};font-weight:bold">{item['risk']}</td>
                <td>{item['matchScore']}</td>
                <td><a href="{item['postUrl']}" target="_blank">View Post</a></td>
            </tr>
            """

        html = f"""
        <html>
        <head>
            <title>{brand} Monitoring</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background: #f8f9fa;
                    margin: 30px;
                }}
                h1 {{ color: #333; }}
                .meta {{
                    margin-bottom: 20px;
                    font-size: 15px;
                    color: #555;
                    line-height: 1.8;
                }}
                .logo-ok {{
                    background: #d1fae5;
                    border: 1px solid #6ee7b7;
                    color: #065f46;
                    padding: 10px 14px;
                    border-radius: 6px;
                    margin-bottom: 16px;
                    font-size: 14px;
                }}
                .logo-warn {{
                    background: #fef3c7;
                    border: 1px solid #fcd34d;
                    color: #92400e;
                    padding: 10px 14px;
                    border-radius: 6px;
                    margin-bottom: 16px;
                    font-size: 14px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    background: white;
                    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
                }}
                th {{
                    background: #0d6efd;
                    color: white;
                    padding: 12px;
                    text-align: left;
                }}
                td {{
                    padding: 10px;
                    border-bottom: 1px solid #ddd;
                    vertical-align: top;
                    font-size: 14px;
                }}
                tr:hover {{ background: #f5f5f5; }}
                a {{ color: #0d6efd; text-decoration: none; }}
                .actions {{
                    margin-bottom: 16px;
                    display: flex;
                    gap: 12px;
                    align-items: center;
                }}
                .btn {{
                    padding: 8px 16px;
                    border-radius: 4px;
                    border: none;
                    cursor: pointer;
                    font-size: 14px;
                    text-decoration: none;
                    display: inline-block;
                }}
                .btn-secondary {{ background: #6c757d; color: white; }}
                .btn-success {{ background: #198754; color: white; }}
            </style>
        </head>
        <body>
            <h1>🛡️ {brand} Brand Monitoring</h1>

            {logo_banner}

            <div class="meta">
                <strong>Brand:</strong> {brand} &nbsp;|&nbsp;
                <strong>Dataset Records:</strong> {total_records} &nbsp;|&nbsp;
                <strong>Posts Displayed:</strong> {len(detections)} &nbsp;|&nbsp;
                <strong>Last Updated:</strong> {datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d %b %Y %I:%M %p IST")}
            </div>

            <div class="actions">
                <a class="btn btn-secondary" href="/dashboard">← Back to Dashboard</a>
                <a class="btn btn-success" href="/export?brand={brand}">⬇️ Export to Excel</a>
            </div>

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
                {rows}
            </table>
        </body>
        </html>
        """

        return html

    except Exception as e:
        print("SCAN ERROR:", e)
        return f"<h2>Error</h2><p>{str(e)}</p>"

# ==========================================
# EXPORT EXCEL
# ==========================================

@app.get("/export")
def export_excel(brand: str):

    APIFY_TOKEN = os.getenv("APIFY_TOKEN")

    if not APIFY_TOKEN:
        return {"error": "Missing APIFY_TOKEN environment variable"}

    if brand not in BRANDS:
        return {"error": f"Unknown brand: {brand}"}

    logo_path = get_logo_path()

    dataset_id = BRANDS[brand]["dataset_id"]
    url = (
        f"https://api.apify.com/v2/datasets/"
        f"{dataset_id}/items?token={APIFY_TOKEN}"
    )

    try:

        response = requests.get(url)
        data = response.json()

        detections = []

        if isinstance(data, list):

            for post in data:

                try:

                    caption = str(
                        post.get("caption", "")
                    ).replace("\n", " ")

                    published_date = post.get("timestamp", "")
                    image_url = post.get("displayUrl", "")

                    score = 0

                    if logo_path and image_url:
                        downloaded_image = download_image(
                            image_url,
                            "/tmp/temp_image.jpg"
                        )
                        score = compare_logo(logo_path, downloaded_image)

                    if score >= 70:
                        risk = "High"
                    elif score >= 40:
                        risk = "Medium"
                    else:
                        risk = "Low"

                    detections.append({
                        "Platform": "Instagram",
                        "Username": post.get("ownerUsername", "unknown"),
                        "Published Date": published_date,
                        "Post URL": post.get("url", ""),
                        "Detected Brand": brand,
                        "Match Score": f"{score}%",
                        "Risk": risk,
                        "Description": (
                            caption[:120] + "..."
                            if len(caption) > 120
                            else caption
                        )
                    })

                except Exception as item_error:
                    print("ITEM ERROR:", item_error)

        detections.sort(
            key=lambda x: float(str(x["Match Score"]).replace("%", "")),
            reverse=True
        )

        df = pd.DataFrame(detections)

        os.makedirs("/tmp/exports", exist_ok=True)

        timestamp = datetime.now(
            ZoneInfo("Asia/Kolkata")
        ).strftime("%Y%m%d_%H%M%S")

        filename = f"/tmp/exports/{brand}_monitoring_{timestamp}.xlsx"

        with pd.ExcelWriter(filename, engine="openpyxl") as writer:

            df.to_excel(writer, index=False, sheet_name="Detections")

            worksheet = writer.sheets["Detections"]

            for col in worksheet.columns:
                max_length = max(
                    len(str(cell.value)) if cell.value else 0
                    for cell in col
                )
                col_letter = col[0].column_letter
                worksheet.column_dimensions[col_letter].width = min(
                    max_length + 4, 60
                )

        return FileResponse(
            path=filename,
            filename=f"{brand}_monitoring_{timestamp}.xlsx",
            media_type=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            )
        )

    except Exception as e:
        print("EXPORT ERROR:", e)
        return {"error": str(e)}
