
import os
import re
import json
import boto3
import requests
from datetime import datetime
from dotenv import load_dotenv

from apiclient import ApiClient

load_dotenv()

client = ApiClient(
client_id=os.environ.get("COGNITO_CLIENT_ID"),
client_secret=os.environ.get("COGNITO_CLIENT_SECRET"),
token_url=os.environ.get("COGNITO_TOKEN_URL"),
api_base_url=os.environ.get("CFI_BASE_URL")
)

async def upload_transcript(identity: str, session_id:str, trsnascript:str):
        bucket_name = os.environ.get("AGENT_BUCKET_NAME")
        transcript_object_key = f"livekit/{identity}/{session_id}/transcript.json"
        response = await client.call_api(method="POST",path= f"/api/sessions/{int(session_id)}/report-presignedurls", json={ 
                "object_key": transcript_object_key
        })
        if response.status_code != 200:
            print(f"Failed to get presigned url: {response.status_code} - {response.text}")   
        presigned_data = response.json()
        print(f"Presigned URL data: {presigned_data}")
        upload_url = presigned_data.get("url")
        if not upload_url:
            print(f"Failed to get upload URL from presigned data: {presigned_data}")
        # Upload the transcript to the presigned URL
        
        upload_response = requests.put(upload_url, data=trsnascript.encode("utf-8"), headers={"Content-Type": "application/json"})
        if upload_response.status_code != 200:
            print(f"Failed to upload transcript: {upload_response.status_code} - {upload_response.text}")
        
        return transcript_object_key
    

import asyncio

if __name__ == "__main__":
    # Test upload_transcript function
    test_identity = "fahkhan172@gmail.com"
    test_session_id = "537"
    test_transcript = json.dumps({"test": "This is a test transcript."}, indent=2)

    async def main():
        transcript_key = await upload_transcript(test_identity, test_session_id, test_transcript)
        print(f"Transcript uploaded to: {transcript_key}")

    asyncio.run(main())