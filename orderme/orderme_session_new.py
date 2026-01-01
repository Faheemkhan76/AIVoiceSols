from common.base_session import BaseSession
from livekit.agents import AgentSession, JobContext, RoomInputOptions
from google.genai import types
from livekit.plugins import google, noise_cancellation
from livekit.plugins.google.realtime import RealtimeModel
from orderme.assistant_orderme import Assistant_OrderMe
from orderme.helper_orderme import Helper_OrderMe, Restaurant
from livekit.plugins.openai import realtime
from openai.types.beta.realtime.session import TurnDetection
from common.helper import Helper
from common.apiclient import ApiClient
from datetime import datetime
import os, json
from dotenv import load_dotenv

load_dotenv(override=True)

class OrderMeSession(BaseSession):
    def __init__(self):
        self.client = ApiClient(
          client_id=os.environ.get("COGNITO_CLIENT_ID", ""),
            client_secret=os.environ.get("COGNITO_CLIENT_SECRET", ""),
            token_url=os.environ.get("COGNITO_TOKEN_URL", ""),
            api_base_url=os.environ.get("ORDERME_BASE_URL", "")
        )
        print(f"OrderMeSession initialized with API base URL: {os.environ.get('ORDERME_BASE_URL', '')}")
    
    async def create_agent_session(self) -> AgentSession:
        gemini_model = RealtimeModel(
            model="gemini-2.5-flash-native-audio-preview-12-2025",
            voice="Puck",
            enable_affective_dialog=True,
            realtime_input_config=types.RealtimeInputConfig(
                automatic_activity_detection=types.AutomaticActivityDetection(
                    disabled=False,
                    start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_HIGH,
                    end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
                    prefix_padding_ms=100,
                    silence_duration_ms=300,
                ),
            ),
            
        )
        return AgentSession(
            llm=gemini_model,
            user_away_timeout=8
        )
          
        # return AgentSession(
        #     llm=google.realtime.RealtimeModel(
        #         # model="gemini-live-2.5-flash-preview",
        #         model="gemini-2.5-flash-native-audio-preview-09-2025",                       
        #         voice="Puck",
        #         temperature=0.8,
        #         modalities=["AUDIO"]
        #     ),
        #     user_away_timeout=8
        # )

    # async def create_agent_session(self) -> AgentSession:
    #     return AgentSession(
    #         llm=realtime.RealtimeModel(
    #             model="gpt-realtime-mini",                
    #             voice="marin",#cedar 
    #             temperature=0.8,
    #             turn_detection=TurnDetection(
    #                 type="semantic_vad",
    #                 eagerness="auto",
    #             )
    #         ),            
    #         user_away_timeout=8
    #     )
    
    async def start_session(self, ctx: JobContext, session: AgentSession, session_param, startdatetime):
        sessionid = session_param["SessionReference"]
        customer_reference = session_param["CustomerReference"]
        
        # Create session log with SQL Server compatible datetime format
        try:
            restaurant = await Helper_OrderMe.get_restaurant_Metadata(session_param)            
            log_body = {
                "SessionId": sessionid,
                "RestaurantId": customer_reference,
                "SessionTypeId": 0,
                "StartDateTime": startdatetime.strftime("%Y-%m-%d %H:%M:%S"),
                "AIAgentPricePerMinute": restaurant.AIAgentPricePerMinute
            }
                    
            print("logging start of the session order")
            await self.client.call_api_unified(
                method="POST",
                path_or_url="/api/sessionlogs",
                json=log_body
            )
            print(f"Session log created for session {sessionid}")
        except Exception as e:
            print(f"Failed to create session log: {e}")
        
        instructions = await Helper_OrderMe.get_instruction(session_param)
        #print(f"Starting OrderMe session with instructions: {instructions}")  
        await session.start(
            room=ctx.room,
            agent=Assistant_OrderMe(instructions=instructions),
            room_input_options=RoomInputOptions(noise_cancellation=noise_cancellation.BVC())
        )
     
    async def manage_shutdown(self, ctx: JobContext, session: AgentSession,session_param, participant, startdatetime, reference):
        # Implement shutdown logic specific to OrderMe
        print(f"Shutting down OrderMe session for {participant}, {session_param}")
        sessionid = session_param["SessionReference"]
        customer_reference = session_param["CustomerReference"]
        enddatetime = datetime.now()
        secondsconsumed = (enddatetime - startdatetime).total_seconds()
        transcript = json.dumps(session.history.to_dict(), indent=2) # Convert dict to JSON string
        try:
            print("logging session end")
            response = await self.client.call_api_unified(method="PATCH", path_or_url=f"/api/sessionlogs?session_id={sessionid}", json={ 
                        "TranscriptData": transcript,
                        "RecordingPath": reference,
                        "EndDateTime": f'{enddatetime.strftime("%Y-%m-%d %H:%M:%S")}',
                        "SecondsConsumed": secondsconsumed,#in Seconds
                    })
        except Exception as e:
            print(f"error occured: {e}") 
        # Add any specific cleanup here