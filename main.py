from fastapi import FastAPI, File, UploadFile
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io, os

app = FastAPI()

SERVICE_ACCOUNT_JSON = "service_account.json"
FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID")

creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_JSON)
drive_service = build('drive', 'v3', credentials=creds)

@app.post("/upload")
async def upload_to_drive(file: UploadFile = File(...)):
    file_content = await file.read()
    media = MediaIoBaseUpload(io.BytesIO(file_content), mim_
