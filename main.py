from fastapi import FastAPI, File, UploadFile
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io, os, json

app = FastAPI()

SERVICE_ACCOUNT_INFO = json.loads(os.getenv("SERVICE_ACCOUNT_JSON_CONTENT"))
creds = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO)
drive_service = build('drive', 'v3', credentials=creds)

FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID")

@app.post("/upload")
async def upload_to_drive(file: UploadFile = File(...)):
    file_content = await file.read()
    media = MediaIoBaseUpload(io.BytesIO(file_content), mimetype=file.content_type)
    body = {
        "name": file.filename,
        "parents": [FOLDER_ID]   # <<< สำคัญตรงนี้ เพื่อเก็บในโฟลเดอร์ที่ตั้งไว้
    }
    uploaded = drive_service.files().create(
        body=body,
        media_body=media,
        fields="id,webViewLink"  # <<< ขอ ID และลิงก์ทันที
    ).execute()
    return {"filename": file.filename, "link": uploaded.get("webViewLink")}
