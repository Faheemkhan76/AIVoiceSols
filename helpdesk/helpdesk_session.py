from common.base_session import BaseSession
from livekit.agents import AgentSession, JobContext, RoomInputOptions
from livekit.plugins import google, noise_cancellation
from helpdesk.assistant_helpdesk import Assistant_Helpdesk
from livekit.plugins.google.realtime import RealtimeModel
from livekit.plugins.openai import realtime
from openai.types.beta.realtime.session import TurnDetection
from google.genai import types
from helpdesk.helper_helpdesk import Helper_Helpdesk
from common.helper import Helper
from common.apiclient import ApiClient
from datetime import datetime
import os, json
from dotenv import load_dotenv

load_dotenv(override=True)

class HelpdeskSession(BaseSession):
    def __init__(self):
        self.helpdesk_base_url = os.environ.get("CSS_BASE_URL", "https://vlr1odudnc.execute-api.us-west-2.amazonaws.com/dev")
        self.client = ApiClient(
            client_id=os.environ.get("COGNITO_CLIENT_ID", ""),
            client_secret=os.environ.get("COGNITO_CLIENT_SECRET", ""),
            token_url=os.environ.get("COGNITO_TOKEN_URL", ""),
            api_base_url=self.helpdesk_base_url
        )
        print(f"HelpdeskSession initialized")
        
    #async def create_agent_session(self) -> AgentSession:
        # gemini_model = RealtimeModel(
        #     model="gemini-2.5-flash-native-audio-preview-12-2025",
        #     voice="Puck",
        #     enable_affective_dialog=True,
        #     realtime_input_config=types.RealtimeInputConfig(
        #         automatic_activity_detection=types.AutomaticActivityDetection(
        #             disabled=False,
        #             start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_HIGH,
        #             end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
        #             prefix_padding_ms=100,
        #             silence_duration_ms=300,
        #         ),
        #     ),            
        # )
        # return AgentSession(
        #     llm=gemini_model,
        #     user_away_timeout=8
        # )
            
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

    async def create_agent_session(self) -> AgentSession:
        return AgentSession(
            llm=realtime.RealtimeModel(
                model="gpt-realtime-mini",                
                voice="cedar",#marin 
                temperature=0.8,
                turn_detection=TurnDetection(
                    type="semantic_vad",
                    eagerness="auto",
                )
            ),            
            user_away_timeout=8
            )

    async def get_organization(self, customer_reference: str):
        """
        Fetch organization details from the API
        Returns: dict with organization details or None if failed
        """
        try:
            response = await self.client.call_api_unified(
                method="GET",
                path_or_url=f"api/organizations/{customer_reference}"
            )
            if response.status_code == 200:
                org_data = response.json()
                print(f"Organization data fetched: {org_data.get('organization', {}).get('Name', 'Unknown')}")
                return org_data.get("organization")
            else:
                print(f"Failed to fetch organization: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error fetching organization: {e}")
            return None

    async def start_session(self, ctx: JobContext, session: AgentSession, session_param, startdatetime):
        sessionid = session_param["SessionReference"]
        customer_reference = session_param["CustomerReference"]
        phonenumber = session_param.get("PhoneNumber", "")
        
        # Fetch organization details
        organization = await self.get_organization(customer_reference)
        
        # Create session log with SQL Server compatible datetime format
        try:
            # Use organization rate if available, otherwise default to 0.15
            rate = organization.get("Rate", 0.15) if organization else 0.15
            
            log_body = {
                "sessionid": sessionid,
                "createddatetime": f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                "startdatetime": f'{startdatetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                "rate": rate,
                "customernumber": phonenumber,
                }
                    
            print("logging start of the helpdesk session")
            print(self.client.api_base_url)
            await self.client.call_api_unified(
                method="POST",
                path_or_url=f"api/organizations/{customer_reference}/sessions",
                json=log_body
            )
            print(f"Helpdesk session log created for session {sessionid}")
            #print("Helpdesk session logging is currently disabled.")
        except Exception as e:
            print(f"Failed to create helpdesk session log: {e}")
        
        instructions = await Helper_Helpdesk.get_instruction(organization)
        await session.start(
            room=ctx.room,
            agent=Assistant_Helpdesk(instructions=instructions),
            room_input_options=RoomInputOptions(noise_cancellation=noise_cancellation.BVC())
        )

    async def manage_shutdown(self, ctx: JobContext, session: AgentSession, session_param, participant, startdatetime, reference):
        # Implement shutdown logic specific to Helpdesk
        print(f"Shutting down Helpdesk session for {participant}, {session_param}")
        sessionid = session_param["SessionReference"]
        customer_reference = session_param["CustomerReference"]#organization id
        enddatetime = datetime.now()
        secondsconsumed = (enddatetime - startdatetime).total_seconds()
        transcript = json.dumps(session.history.to_dict(), indent=2) # Convert dict to JSON string
        
        try:
            response = await self.client.call_api_unified(
                method="PATCH", 
                path_or_url=f"/api/organizations/{customer_reference}/sessions/{sessionid}", 
                json={ 
                    "transcript": transcript,
                    "enddatetime": f'{enddatetime.strftime("%Y-%m-%d %H:%M:%S")}',
                    "secondsconsumed": secondsconsumed,  # in Seconds
                }
            )
            print(f"Helpdesk session shutdown logged successfully")
        except Exception as e:
            print(f"Error occurred during helpdesk session shutdown: {e}") 
        # Add any specific cleanup here