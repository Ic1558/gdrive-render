from fastapi import FastAPI, File, UploadFile
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io, os

app = FastAPI()

import json

SERVICE_ACCOUNT_INFO = json.loads(os.getenv("SERVICE_ACCOUNT_JSON_CONTENT"))
creds = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO)


@app.post("/upload")
async def upload_to_drive(file: UploadFile = File(...)):
    file_content = await file.read()
    media = MediaIoBaseUpload(io.BytesIO(file_content), mimetype=file.content_type)
