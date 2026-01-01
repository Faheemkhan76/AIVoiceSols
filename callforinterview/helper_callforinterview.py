# import os
# import re
# import json
# import boto3 
# from datetime import datetime
# from dotenv import load_dotenv

# from livekit import agents
# import livekit.api as api
# from livekit.agents import AgentSession, RoomInputOptions
# from livekit.plugins import (noise_cancellation)
# from livekit.plugins.openai import realtime
# from openai.types.beta.realtime.session import TurnDetection
# from helper import Helper
# from prompts import WELCOME_MESSAGE, ANALYZER_INSTRUCTIONS
# from apiclient import ApiClient
# from assistant_callforinterview import Assistant_CallforInterview

# client = ApiClient(
# client_id=os.environ.get("COGNITO_CLIENT_ID"),
# client_secret=os.environ.get("COGNITO_CLIENT_SECRET"),
# token_url=os.environ.get("COGNITO_TOKEN_URL"),
# api_base_url=os.environ.get("CFI_BASE_URL")
# )

# class Helper_CallforInterview:
#     @staticmethod
#     async def create_agent_session():
#         print("Creating Agent Session...")
#         return AgentSession(
#                     llm=realtime.RealtimeModel(
#                     model="gpt-realtime-mini",#"gpt-4o-mini-realtime-preview",
#                     voice="cedar",#"marin",
#                     temperature=0.8,
#                     turn_detection=TurnDetection(
#                         type="semantic_vad",
#                         eagerness= "auto",
#                         create_response=True,
#                         interrupt_response=True                        
#                         ),                        
#                     ),
#                     user_away_timeout=8 # time in seconds to detect silence
#                 )
        
#     @staticmethod
#     async def start_session(ctx, session, session_id, instructions):    
#         startdatetime = datetime.now()       
#         await session.start(
#                     room=ctx.room,
#                     agent=Assistant_CallforInterview(instructions=instructions),
#                     room_input_options=RoomInputOptions(noise_cancellation=noise_cancellation.BVC())                
#                 )
#         #Update with session started        
#         await client.call_api(method="PATCH",path= f"/api/sessions/{int(session_id)}", json={ 
#                 "startdatetime": f'{startdatetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
#                 "status": 2 #session started
#             })                
        
#     async def manage_shutdown(ctx,session, participant, startdatetime, recording_path):
#         enddatetime = datetime.now()
#         secondsconsumed = (enddatetime - startdatetime).total_seconds()
#         session_id = ctx.room.name #UI set session id in room name attribute and email in participant 
#         identity = participant
#         print(f"shutting session for room: {session_id} and participant: {identity}")
            
#         current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
#         # Upload interview transcript to S3
#         json_str = json.dumps(session.history.to_dict(), indent=2) # Convert dict to JSON string
#         transcript_object_key = await Helper.upload_transcript(identity=identity, session_id=session_id, trsnascript= json_str)
#         try:
#             response = await client.call_api(method="PATCH",path= f"/api/sessions/{int(session_id)}", json={ 
#                         "startdatetime": f'{startdatetime.strftime("%Y-%m-%d %H:%M:%S")}',
#                         "Transcriptpath": transcript_object_key,
#                         "RecordingPath": recording_path,
#                         "enddatetime": f'{enddatetime.strftime("%Y-%m-%d %H:%M:%S")}',
#                         "MinutesConsumed": secondsconsumed,#in Seconds
#                         "Status": 3 #session end
#                     })
#         except Exception as e:
#             print(f"error occured: {e}")      