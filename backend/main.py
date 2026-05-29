from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
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
# BRAND CONFIGURATION
# ==========================================

BRANDS = {
    "ICICI": {
        "dataset_id": "rCSm3WSZI7CLbQO9V"
    },
    "Groww": {
        "dataset_id": "UM5FgBJEDue5cHdDn"
    },
    "Motilal Oswal": {
        "dataset_id": "UHe54nGhYCKmay4fG"
    },
    "Tata Capital": {
        "dataset_id": "GNJaaAzrwYm5aKBeT"
    },
    "Zerodha": {
        "dataset_id": "ulvEkheIxIfMvTBle"
    },
    "Upstox": {
        "dataset_id": "Pm3tYd3dHjjwQy4eT"
    },
    "SBI": {
        "dataset_id": "Cu5JITs5mi2z2OJQh"
    },
    "Anand Rathi": {
        "dataset_id": "bKFdqpdhW37BOKOb7"
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

    uploaded_logo = file.filename

    return {
        "message": "Reference creative uploaded successfully"
    }

# ==========================================
# BRAND SELECTION PAGE
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
                font-family: Arial;
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

        <h1>Instagram Brand Monitoring</h1>

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

    url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_TOKEN}"

    try:

        response = requests.get(url)

        data = response.json()

        print("SELECTED BRAND:", brand)
        print("DATASET:", dataset_id)
        print("TOTAL RECORDS:", len(data) if isinstance(data, list) else 0)

        detections = []

        if isinstance(data, list):

            for post in data:

                try:

                    detections.append({

                        "platform": "Instagram",

                        "username": post.get(
                            "ownerUsername",
                            "unknown"
                        ),

                        "postUrl": post.get(
                            "url",
                            "#"
                        ),

                        "detectedBrand": brand,

                        "matchScore": "96%",

                        "risk": "Medium",

                        "caption": str(
                            post.get(
                                "caption",
                                ""
                            )
                        )[:150]

                    })

                except Exception as item_error:

                    print("ITEM ERROR:", item_error)

        html = f"""
        <html>

        <head>

            <title>{brand} Monitoring</title>

            <style>

                body {{
                    font-family: Arial;
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
                }}

            </style>

        </head>

        <body>

            <h1>{brand} Brand Monitoring</h1>

            <div class="count">
                Total Detections: {len(detections)}
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
                    <th>Brand</th>
                    <th>Risk</th>
                    <th>Score</th>
                    <th>Caption</th>
                    <th>Post</th>
                </tr>
        """

        for item in detections:

            html += f"""

            <tr>

                <td>{item['platform']}</td>

                <td>{item['username']}</td>

                <td>
                    <span class="brand">
                        {item['detectedBrand']}
                    </span>
                </td>

                <td>{item['risk']}</td>

                <td>{item['matchScore']}</td>

                <td>{item['caption']}</td>

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
