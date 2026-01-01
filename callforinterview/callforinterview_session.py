from common.base_session import BaseSession
from livekit.agents import AgentSession, JobContext, RoomInputOptions
from livekit.plugins import google, noise_cancellation
from livekit.plugins.openai import realtime
from livekit.plugins.openai import realtime
from openai.types.beta.realtime.session import TurnDetection
from callforinterview.assistant_callforinterview import Assistant_CallforInterview
from common.apiclient import ApiClient
from datetime import datetime
import os, json
from common.helper import Helper

class CallForInterviewSession(BaseSession):
    def __init__(self):
        self.client = ApiClient(
            client_id=os.environ.get("COGNITO_CLIENT_ID", ""),
            client_secret=os.environ.get("COGNITO_CLIENT_SECRET", ""),
            token_url=os.environ.get("COGNITO_TOKEN_URL", ""),
            api_base_url=os.environ.get("CFI_BASE_URL", "")
        )

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

    async def start_session(self, ctx: JobContext, session: AgentSession, session_info, startdatetime):
        session_id = None
        if isinstance(session_info, dict):
            session_id = session_info['SessionReference']
        else:
            session_id = session_info  # session_id from ctx.room.name
        response = await self.client.call_api_unified(method="GET", path_or_url=f"/api/sessions/{int(session_id)}")
        instructions = response.json()['Instructions']
    
        await session.start(
            room=ctx.room,
            agent=Assistant_CallforInterview(instructions=instructions),
            room_input_options=RoomInputOptions(audio_enabled=True, text_enabled=True)
        )
        await self.client.call_api_unified(method="PATCH", path_or_url=f"/api/sessions/{int(session_id)}", json={ 
                "startdatetime": f'{startdatetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                "status": 2 #session started
            })       

    async def manage_shutdown(self, ctx: JobContext, session: AgentSession,session_param, participant, startdatetime, reference):
        # Implement shutdown logic specific to CallForInterview
        enddatetime = datetime.now()
        secondsconsumed = (enddatetime - startdatetime).total_seconds()
        session_id = ctx.room.name #UI set session id in room name attribute and email in participant 
        identity = participant.identity
        print(f"shutting session for room: {session_id} and participant: {identity}")
        # Upload interview transcript to S3
        json_str = json.dumps(session.history.to_dict(), indent=2) # Convert dict to JSON string
        transcript_object_key = await Helper.upload_transcript(identity=identity, session_id=session_id, trsnascript= json_str)
        try:
            response = await self.client.call_api_unified(method="PATCH", path_or_url=f"/api/sessions/{int(session_id)}", json={ 
                        "Transcriptpath": transcript_object_key,
                        "RecordingPath": reference,
                        "enddatetime": f'{enddatetime.strftime("%Y-%m-%d %H:%M:%S")}',
                        "MinutesConsumed": secondsconsumed,#in Seconds
                        "Status": 3 #session end
                    })
        except Exception as e:
            print(f"error occured: {e}") 