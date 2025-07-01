import os, json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as f:
            f.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def upload_json(service, filename, data_dict):
    from googleapiclient.http import MediaInMemoryUpload
    body = {'name': filename, 'mimeType': 'application/json'}
    media = MediaInMemoryUpload(json.dumps(data_dict).encode(), mimetype='application/json')
    return service.files().create(body=body, media_body=media, fields='id').execute()

def download_json(service, file_name):
    files = service.files().list(q=f"name='{file_name}'", fields="files(id, name)").execute().get("files", [])
    if not files: return None
    file_id = files[0]['id']
    content = service.files().get_media(fileId=file_id).execute()
    return json.loads(content.decode())
