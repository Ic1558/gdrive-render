from fastapi import FastAPI, File, UploadFile, HTTPException
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io, os, json

app = FastAPI()

# Load credentials
SERVICE_ACCOUNT_JSON = os.getenv("SERVICE_ACCOUNT_JSON_CONTENT")
if not SERVICE_ACCOUNT_JSON:
    raise Exception("SERVICE_ACCOUNT_JSON_CONTENT not found in environment variables")

SERVICE_ACCOUNT_INFO = json.loads(SERVICE_ACCOUNT_JSON)
creds = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO)
drive_service = build('drive', 'v3', credentials=creds)

# Load GDrive Folder ID
FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID")
if not FOLDER_ID:
    raise Exception("GDRIVE_FOLDER_ID not found in environment variables")

@app.post("/upload")
async def upload_to_drive(file: UploadFile = File(...)):
    try:
        file_content = await file.read()
        media = MediaIoBaseUpload(io.BytesIO(file_content), mimetype=file.content_type)

        body = {
            "name": file.filename,
            "parents": [FOLDER_ID]
        }

        uploaded = drive_service.files().create(
            body=body,
            media_body=media,
            fields="id,webViewLink"
        ).execute()

        return {
            "filename": file.filename,
            "file_id": uploaded.get("id"),
            "view_link": uploaded.get("webViewLink")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
