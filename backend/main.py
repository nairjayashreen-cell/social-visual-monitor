from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil

app = FastAPI()

UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():

    return {
        "status":"AI Visual Threat Monitoring API Running"
    }

@app.post("/upload")

async def upload_logo(
    file: UploadFile = File(...)
):

    file_path = f"{UPLOAD_DIR}/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "message":"Logo uploaded successfully",
        "filename":file.filename,
        "path":file_path
    }

@app.get("/scan")

def scan():

    uploaded_files = os.listdir(UPLOAD_DIR)

    results = []

    for file in uploaded_files:

        results.append({

            "platform":"Instagram",

            "username":"detected_account",

            "url":"https://www.instagram.com/p/DXXA7x3GfUw/",

            "brand":file,

            "score":"96%",

            "risk":"Critical",

            "ocr":"Unauthorized Brand Promotion",

            "time":"2 hours ago"

        })

    return results
