from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

load_dotenv()

app = FastAPI()

# === Google Drive Upload ===

def get_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        "token.json",
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    service = build("drive", "v3", credentials=creds)
    return service

async def upload_file_to_gdrive(file: UploadFile) -> str:
    folder_id = os.getenv("GDRIVE_FOLDER_ID")
    service = get_drive_service()

    file_metadata = {
        "name": file.filename,
        "parents": [folder_id]
    }
    media = MediaIoBaseUpload(io.BytesIO(await file.read()), mimetype=file.content_type)
    uploaded_file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    file_id = uploaded_file.get("id")
    return f"https://drive.google.com/uc?id={file_id}&export=download"

# === Google Sheets Read ===

def get_sheets_service():
    creds = service_account.Credentials.from_service_account_file(
        "token.json",
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    service = build("sheets", "v4", credentials=creds)
    return service

def get_google_sheets_data():
    service = get_sheets_service()
    sheet_id = os.getenv("SHEET_ID")
    result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range="Sheet1!A1:C10").execute()
    return result.get('values', [])

# === API Models ===

class UploadResponse(BaseModel):
    links: List[str]
    sheet_data: List[List[str]]

@app.get("/")
def root():
    return {"status": "FastAPI is running"}

@app.get("/ping")
def ping():
    return {"status": "pong"}

@app.get("/time")
def time_now():
    from datetime import datetime
    return {"time": datetime.utcnow().isoformat()}

@app.get("/sheets")
def read_sheet():
    data = get_google_sheets_data()
    return {"data": data}

@app.post("/upload", response_model=UploadResponse)
async def upload_gdrive(files: List[UploadFile] = File(...)):
    links = []
    for file in files:
        link = await upload_file_to_gdrive(file)
        links.append(link)

    sheet_data = get_google_sheets_data()
    return UploadResponse(links=links, sheet_data=sheet_data)
