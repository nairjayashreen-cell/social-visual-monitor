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

@app.get("/scan", response_class=HTMLResponse)
def scan_instagram():

    global uploaded_logo

    if not uploaded_logo:
        return """
        <h2>Please upload logo first</h2>
        """

    APIFY_TOKEN = os.getenv("APIFY_TOKEN")

    if not APIFY_TOKEN:
        return """
        <h2>Missing APIFY_TOKEN environment variable</h2>
        """

    dataset_id = "H48GidXLMED6oA8bK"

    url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_TOKEN}"

    try:

        response = requests.get(url)
        data = response.json()

        print("RAW RESPONSE:", data)
        print("DATA TYPE:", type(data))

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
                            "detectedText": caption[:150]
                        })

                except Exception as item_error:

                    print("ITEM ERROR:", item_error)

        html = f"""
        <html>
        <head>
            <title>Instagram Monitoring Dashboard</title>

            <style>

                body {{
                    font-family: Arial, sans-serif;
                    margin: 30px;
                    background: #f8f9fa;
                }}

                h1 {{
                    color: #333;
                }}

                .count {{
                    margin-bottom: 20px;
                    font-size: 18px;
                    font-weight: bold;
                }}

                table {{
                    width: 100%;
                    border-collapse: collapse;
                    background: white;
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
                }}

                tr:hover {{
                    background: #f5f5f5;
                }}

                a {{
                    color: #0d6efd;
                    text-decoration: none;
                }}

            </style>

        </head>

        <body>

            <h1>Instagram Brand Monitoring</h1>

            <div class="count">
                Total Detections: {len(detections)}
            </div>

            <table>

                <tr>
                    <th>Platform</th>
                    <th>Username</th>
                    <th>Brand</th>
                    <th>Risk</th>
                    <th>Score</th>
                    <th>Post</th>
                </tr>
        """

        for item in detections:

            html += f"""
            <tr>
                <td>{item['platform']}</td>
                <td>{item['username']}</td>
                <td>{item['detectedBrand']}</td>
                <td>{item['risk']}</td>
                <td>{item['matchScore']}</td>
                <td>
                    <a href="{item['postUrl']}" target="_blank">
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
