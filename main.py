import os
import aiohttp
import asyncio
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

app = FastAPI()

# === CONFIG ===
GDRIVE_FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID")  # ดึง Folder ID จาก ENV
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # ดึง Telegram Token จาก ENV
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # ดึง Telegram Chat ID จาก ENV
GDRIVE_CREDENTIAL_PATH = "/etc/secrets/gdrive_sa.json"  # โหลดไฟล์ Secret
GDRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]
SHEET_ID = os.getenv("SHEET_ID")  # Google Sheets ID สำหรับดึงข้อมูล

# === Helper Functions ===

def get_drive_service():
    credentials = service_account.Credentials.from_service_account_file(
        GDRIVE_CREDENTIAL_PATH, scopes=GDRIVE_SCOPES
    )
    return build("drive", "v3", credentials=credentials)

def get_sheets_service():
    credentials = service_account.Credentials.from_service_account_file(
        GDRIVE_CREDENTIAL_PATH, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    return build('sheets', 'v4', credentials=credentials)

async def send_telegram_message(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    async with aiohttp.ClientSession() as session:
        await session.post(url, data=payload)

async def upload_file_to_gdrive(file: UploadFile) -> str:
    service = get_drive_service()
    file_metadata = {
        "name": file.filename,
        "parents": [GDRIVE_FOLDER_ID] if GDRIVE_FOLDER_ID else []
    }
    media = MediaIoBaseUpload(io.BytesIO(await file.read()), mimetype=file.content_type)
    uploaded_file = service.files().create(body=file_metadata, media_body=media, fields="id,webViewLink").execute()
    file_id = uploaded_file.get("id")
    return f"https://drive.google.com/uc?id={file_id}&export=download"

def get_google_sheets_data():
    service = get_sheets_service()
    result = service.spreadsheets().values().get(spreadsheetId=SHEET_ID, range="Sheet1!A1:C10").execute()
    return result.get('values', [])

# === API Models ===

class UploadResponse(BaseModel):
    files: List[str]

# === Main Endpoints ===

@app.post("/upload/gdrive", response_model=UploadResponse)
async def upload_gdrive(files: List[UploadFile] = File(...)):
    try:
        links = []
        for file in files:
            link = await upload_file_to_gdrive(file)
            links.append(link)

        # ดึงข้อมูลจาก Google Sheets
        sheet_data = get_google_sheets_data()
        print(f"Data from Google Sheets: {sheet_data}")

        # Compose Telegram Message
        if len(links) == 1:
            message = f"อัปโหลดสำเร็จ: {links[0]}"
        else:
            message = "ไฟล์ที่อัปโหลดสำเร็จ:\n" + "\n".join(f"- {link}" for link in links)

        await send_telegram_message(message)
        return UploadResponse(files=links)

    except Exception as e:
        await send_telegram_message(f"❗ Upload or Push Failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"status": "online"}
