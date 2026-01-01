import os
import re
import json
import boto3
import random
from datetime import datetime
from dotenv import load_dotenv
import requests
from livekit import agents
import livekit.api as api
from livekit.agents import AgentSession, RoomInputOptions, llm
# from livekit.plugins.turn_detector.english import EnglishModel
from livekit.plugins import google
from livekit.plugins import (noise_cancellation)
from livekit.plugins.openai import realtime
from openai.types.beta.realtime.session import TurnDetection
from openai import OpenAI

from prompts import WELCOME_MESSAGE, ANALYZER_INSTRUCTIONS
from common.apiclient import ApiClient

load_dotenv(override=True)

client = ApiClient(
client_id=os.environ.get("COGNITO_CLIENT_ID"),
client_secret=os.environ.get("COGNITO_CLIENT_SECRET"),
token_url=os.environ.get("COGNITO_TOKEN_URL"),
api_base_url=os.environ.get("CFI_BASE_URL")
)

class Helper:
    @staticmethod
    async def upload_transcript(identity: str, session_id:str, trsnascript:str):
        bucket_name = os.environ.get("AGENT_BUCKET_NAME")
        transcript_object_key = f"livekit/{identity}/{int(session_id)}/transcript.json"
        response = await client.call_api_unified(method="POST", path_or_url=f"/api/sessions/{int(session_id)}/report-presignedurls", json={ 
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
        
    @staticmethod
    async def generate_report(transcript: str):
        print(f"Generating Interview report...")
        openai_endpoint = os.environ['DEEPSEEK_URL']
        openai_key = os.environ['DEEPSEEK_KEY']
        openai_client = OpenAI(
            api_key=openai_key,
            base_url=openai_endpoint
        )
        analyze_report = openai_client.chat.completions.create(
            model = os.environ['DEEPSEEK_MODEL'],
            messages = [
                {"role": "system", "content": ANALYZER_INSTRUCTIONS},
                {"role": "user", "content": transcript}
            ],
            # response_format={"type":"json_object"}
            # tools="",
            temperature=0
        )
        print(f"Report created.")
        return await Helper.extract_json_object(analyze_report.choices[0].message.content)
    
    @staticmethod
    async def s3upload(bucket_name: str, key: str, body: str):
        try:
            
            s3_client = boto3.client(
                's3',
                aws_access_key_id=os.environ['S3_CLIENT_KEY'],
                aws_secret_access_key=os.environ['S3_CLIENT_SECRET'],
                region_name=os.environ['S3_REGION']
            )
            s3_client.put_object(Bucket=bucket_name, Key=key, Body=body, ContentType='application/json')
        except Exception as e:
            print(f"error occured while uploading s3 object {key}: {e}")
        else:
            print(f"no error occur error occured while uploading s3 object {key}")
        finally:
            print(f"s3upload function completed.")
            
    @staticmethod
    async def extract_json_object(text: str):
        # Extract JSON-like content from the string
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in the string.")

        json_str = match.group()

        # Fix improperly escaped quotes inside values
        # This targets quotes inside strings that are not escaped
        def fix_quotes(s):
            def replacer(match):
                content = match.group(1)
                # Escape internal quotes
                fixed = re.sub(r'(?<!\\)"', r'\\"', content)
                return f'"{fixed}"'
            return re.sub(r'"([^"]*?)"', replacer, s)

        fixed_json_str = fix_quotes(json_str)        
        try:
            return json.loads(fixed_json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Still invalid JSON after fix: {e}")
    
    @staticmethod
    async def enable_recording(session_id: str, identity: str):
        recording_path = f"livekit/{identity}/{session_id}/recording.ogg"
        req = api.RoomCompositeEgressRequest( 
            room_name=session_id,
            audio_only=True,
            file_outputs=[api.EncodedFileOutput(
                file_type=api.EncodedFileType.OGG,
                filepath=recording_path,                
                s3=api.S3Upload(
                    bucket= os.environ.get("AGENT_BUCKET_NAME"),
                    region=os.environ['S3_REGION'],
                    access_key=os.environ['S3_CLIENT_KEY'],
                    secret=os.environ['S3_CLIENT_SECRET'],
                ),
            )],
        )
        
        lkapi = api.LiveKitAPI()
        res = await lkapi.egress.start_room_composite_egress(req)
        await lkapi.aclose()
        return recording_path
    
    
    
    @staticmethod
    def parse_session(s: str):
        """
        Parse a string of the format:
        ApplicationName_CustomerReference_SessionReference

        Returns:
            dict with parsed values if format matches,
            otherwise the original string.
        """
        parts = s.split("_")
        
        if len(parts) == 3:
            return {
                "ApplicationName": parts[0],
                "CustomerReference": parts[1],
                "SessionReference": parts[2]
            }
        elif len(parts) == 4:
            return {
                "ApplicationName": parts[0],
                "CustomerReference": parts[1],
                "PhoneNumber": parts[2],
                "SessionReference": parts[3]
            }
        else:
            return s

    @staticmethod
    def generate_otp(length: int = 4) -> str:
        """
        Generate a random OTP (One-Time Password) of specified length.
        
        Args:
            length: Length of OTP to generate (default: 4)
            
        Returns:
            str: Random OTP as a string of digits
            
        Example:
            otp = Helper.generate_otp()  # Returns something like "1234"
            otp = Helper.generate_otp(6)  # Returns something like "987654"
        """
        otp = ''.join([str(random.randint(0, 9)) for _ in range(length)])
        return otp

    @staticmethod
    async def send_sms_via_sns(phone_number: str, message: str):
        """
        Send SMS message using AWS SNS service.
        
        Args:
            phone_number: Phone number in E.164 format (e.g., "+1234567890")
            message: Message content to send
            
        Returns:
            dict: Response from SNS with MessageId if successful
            
        Raises:
            Exception: If SNS send fails
        """
        try:
            sns_client = boto3.client(
                'sns',
                region_name=os.environ.get('SNS_REGION', 'us-west-2'),
                aws_access_key_id=os.environ.get('SNS_CLIENT_KEY'),
                aws_secret_access_key=os.environ.get('SNS_CLIENT_SECRET')
            )
            
            response = sns_client.publish(
                PhoneNumber=phone_number,
                Message=message
            )
            
            print(f"SMS sent successfully to {phone_number}. Message ID: {response['MessageId']}")
            return response
            
        except Exception as e:
            print(f"Failed to send SMS to {phone_number}: {e}")
            raise
    
    @staticmethod
    async def send_email_via_sns(email_address: str, subject: str, message: str, topic_arn: str = None):
        """
        Send email using AWS SNS service via Topic subscription.
        
        Args:
            email_address: Email address (optional if using topic_arn)
            subject: Email subject line
            message: Email message content
            topic_arn: Optional SNS Topic ARN. If provided, message is published to topic
                      instead of sending directly to email
            
        Returns:
            dict: Response from SNS with MessageId if successful
            
        Raises:
            Exception: If SNS send fails
        """
        try:
            sns_client = boto3.client(
                'sns',
                region_name=os.environ.get('SNS_REGION', 'us-west-2'),
                aws_access_key_id=os.environ.get('SNS_CLIENT_KEY'),
                aws_secret_access_key=os.environ.get('SNS_CLIENT_SECRET')
            )
            
            if topic_arn:
                # Publish to SNS Topic
                response = sns_client.publish(
                    TopicArn=topic_arn,
                    Subject=subject,
                    Message=message
                )
                print(f"Message published to topic {topic_arn}. Message ID: {response['MessageId']}")
            else:
                # Send directly to email (requires subscription)
                response = sns_client.publish(
                    Message=message,
                    Subject=subject,
                    TargetArn=f"arn:aws:sns:us-west-2:123456789012:email-endpoint"  # This needs actual endpoint
                )
                print(f"Email sent to {email_address}. Message ID: {response['MessageId']}")
            
            return response
            
        except Exception as e:
            print(f"Failed to send email: {e}")
            raise