import requests
from common.base_session import BaseSession
from livekit.agents import AgentSession, JobContext, RoomInputOptions
from livekit.plugins import google, noise_cancellation
from livekit.plugins.openai import realtime
from livekit.plugins.openai import realtime
from openai.types.beta.realtime.session import TurnDetection
from callforinterview_corp.assistant_callforinterview_Corp import Assistant_CallforInterview_Corp
from common.apiclient import ApiClient
from datetime import datetime
import os, json
from common.helper import Helper
from livekit import api
from livekit.api import TrackEgressRequest, EncodedFileOutput, S3Upload
#from test import upload_transcript

class CallForInterviewCorpSession(BaseSession):
    def __init__(self):
        self.client = ApiClient(
            client_id=os.environ.get("COGNITO_CLIENT_ID", ""),
            client_secret=os.environ.get("COGNITO_CLIENT_SECRET", ""),
            token_url=os.environ.get("COGNITO_TOKEN_URL", ""),
            api_base_url=os.environ.get("CFI_CORP_BASE_URL", "")
        )

    @staticmethod
    def parse_reference_string(interview_str: str):
        """
        Parse an interview string in the format "organization_id-jobrequisition_id-candidate_id"
        
        Args:
            interview_str: String in format "7-8-21"
            
        Returns:
            dict: Dictionary with keys 'organization_id', 'jobrequisition_id', 'candidate_id'
            
        Raises:
            ValueError: If the string doesn't contain exactly 3 parts separated by '-'
        """
        parts = interview_str.split('-')
        if len(parts) != 3:
            raise ValueError(f"Invalid interview string format: {interview_str}. Expected format: 'organization_id-jobrequisition_id-candidate_id'")
        
        try:
            return {
                'organization_id': int(parts[0]),
                'jobrequisition_id': int(parts[1]),
                'candidate_id': int(parts[2])
            }
        except ValueError as e:
            raise ValueError(f"Invalid interview string: {interview_str}. All parts must be integers: {e}")

    async def start_recording(self, ctx: JobContext, recording_path: str):
        """
        Start recording the room audio to S3
        """
        try:
            room_name = ctx.room.name
            
            # Get S3 configuration from environment
            bucket_name = os.environ.get("CORP_AGENT_BUCKET_NAME")
            aws_access_key = os.environ.get("AWS_CORP_CLIENT_KEY")
            aws_secret_key = os.environ.get("AWS_CORP_CLIENT_SECRET")
            aws_region = os.environ.get("AWS_CORP_S3_REGION")
            
            if not bucket_name or not aws_access_key or not aws_secret_key:
                print("Warning: AWS credentials not configured. Recording disabled.")
                return
            
            print(f"Starting recording for room: {room_name}")
            print(f"Recording will be saved to: s3://{bucket_name}/{recording_path}")
            
            # Initialize LiveKit API
            livekit_api = api.LiveKitAPI()
            
            # Start room composite recording
            egress_info = await livekit_api.egress.start_room_composite_egress(
                api.RoomCompositeEgressRequest(
                    room_name=room_name,
                    layout="speaker",
                    audio_only=False,  # Record both audio and video
                    file_outputs=[
                        EncodedFileOutput(
                            file_type=api.EncodedFileType.MP4,
                            filepath=recording_path,
                            s3=S3Upload(
                                access_key=aws_access_key,
                                secret=aws_secret_key,
                                region=aws_region,
                                bucket=bucket_name
                            )
                        )
                    ]
                )
            )
            
            print(f"Recording started successfully. Egress ID: {egress_info.egress_id}")
            
            # Store egress ID in context for later reference
            ctx.room.metadata = json.dumps({"egress_id": egress_info.egress_id})
            
        except Exception as e:
            print(f"Failed to start recording: {e}")
            import traceback
            traceback.print_exc()

    async def create_agent_session(self) -> AgentSession:
        return AgentSession(
            llm=realtime.RealtimeModel(
                
                model="gpt-realtime-mini",
                voice="cedar",
                temperature=0.8,
                turn_detection=TurnDetection(
                    type="semantic_vad",
                    eagerness="auto",
                )
            ),
            user_away_timeout=12
        )

    async def start_session(self, ctx: JobContext, session: AgentSession, session_param, startdatetime):
        if isinstance(session_param, dict):
            session_id = session_param['SessionReference']
        else:
            raise ValueError(f"Invalid session_param: {session_param}")
        
        customer_reference = self.parse_reference_string(session_param['CustomerReference'])
        if not customer_reference:
            raise ValueError(f"Invalid CustomerReference: {session_param['CustomerReference']}")
        else:
            organization_id = customer_reference['organization_id']
            jobrequisition_id = customer_reference['jobrequisition_id']
            candidate_id = customer_reference['candidate_id']
        response = await self.client.call_api_unified(method="GET", path_or_url=f"/api/organizations/{organization_id}/jobrequisitions/{jobrequisition_id}/candidates/{candidate_id}/sessions/{session_id}" )
        instructions = response.json()['instructions']
        candidate_acknowlege_recording_flag = response.json().get('candidateacknowlegerecordingflag', False)
        record_session_flag = response.json().get('recordsessionflag', False)

        recording_path = "disabled"
        if candidate_acknowlege_recording_flag and record_session_flag:
            # Define the S3 path for the recording
            recording_path = f"organizations/{organization_id}/jobrequisitions/{jobrequisition_id}/candidates/{candidate_id}/sessions/{session_id}/recording.mp4"
            # Start recording for the session
            await self.start_recording(ctx, recording_path)
        
        print(f"Recording path: {recording_path}")
        
        await session.start(
            room=ctx.room,
            agent=Assistant_CallforInterview_Corp(instructions=instructions),
            room_input_options=RoomInputOptions(audio_enabled=True, text_enabled=True)
        )
        await self.client.call_api_unified(method="PATCH", path_or_url=f"/api/organizations/{organization_id}/jobrequisitions/{jobrequisition_id}/candidates/{candidate_id}/sessions/{session_id}", json={ 
            "recordingpath": recording_path,                                                                                                                                                                                                
            "startdatetime": f'{startdatetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            "status": 2 #session started
        })  

    async def manage_shutdown(self, ctx: JobContext, session: AgentSession,session_param, participant, startdatetime, reference):
        # Implement shutdown logic specific to CallForInterview Corp
        print(f"Shutting down CallForInterview Corp session for {participant}, {session_param}")
        if isinstance(session_param, dict):
            session_id = session_param['SessionReference']
        else:
            raise ValueError(f"Invalid session_param: {session_param}")
        
        customer_reference = self.parse_reference_string(session_param['CustomerReference'])
        if not customer_reference:
            raise ValueError(f"Invalid CustomerReference: {session_param['CustomerReference']}")
        else:
            organization_id = customer_reference['organization_id']
            jobrequisition_id = customer_reference['jobrequisition_id']
            candidate_id = customer_reference['candidate_id']
            
        # Add any specific cleanup here
        # Implement shutdown logic specific to CallForInterview
        enddatetime = datetime.now()
        secondsconsumed = (enddatetime - startdatetime).total_seconds()
        print(f"secondsconsumed: {secondsconsumed} ")
        print(f"shutting session for room: {session_id} and participant: {participant.identity}")
        # Upload interview transcript to S3
        transcript = json.dumps(session.history.to_dict(), indent=2) # Convert dict to JSON string
        transcript_object_key = await self.upload_transcript(organization_id, jobrequisition_id, candidate_id, session_id, transcript)
        try:
            response = await self.client.call_api_unified(method="PATCH", path_or_url=f"/api/organizations/{organization_id}/jobrequisitions/{jobrequisition_id}/candidates/{candidate_id}/sessions/{session_id}", json={ 
                        "Transcriptpath": transcript_object_key,
                        "enddatetime": f'{enddatetime.strftime("%Y-%m-%d %H:%M:%S")}',
                        "SecondsConsumed": secondsconsumed,#in Seconds
                        "Status": 3 #session end
                    })
        except Exception as e:
            print(f"error occured: {e}") 

    async def upload_transcript(self, organization_id: str, jobrequisition_id: str, candidate_id: str, session_id: str, trsnascript:str):
        bucket_name = os.environ.get("CORP_AGENT_BUCKET_NAME")
        object_key = f"organizations/{organization_id}/jobrequisitions/{jobrequisition_id}/candidates/{candidate_id}/sessions/{session_id}/transcript.json"
        response = await self.client.call_api_unified(method="POST", path_or_url=f"/api/organizations/{organization_id}/jobrequisitions/{jobrequisition_id}/candidates/{candidate_id}/sessions/{session_id}/presignedurl", json={ 
                "object_key": f"organizations/{organization_id}/jobrequisitions/{jobrequisition_id}/candidates/{candidate_id}/sessions/{session_id}/transcript.json"
        })
        if response.status_code != 200:
            print(f"Failed to get presigned url: {response.status_code} - {response.text}")   
        presigned_data = response.json()
        print(f"Presigned URL data: {presigned_data}")
        upload_url = presigned_data.get("presigned_url")
        if not upload_url:
            print(f"Failed to get upload URL from presigned data: {presigned_data}")
        # Upload the transcript to the presigned URL

        upload_response = requests.put(upload_url, data=trsnascript.encode("utf-8"), headers={"Content-Type": "application/json"})
        if upload_response.status_code != 200:
            print(f"Failed to upload transcript: {upload_response.status_code} - {upload_response.text}")

        return object_key