import asyncio
from datetime import datetime
from dotenv import load_dotenv
from typing import AsyncIterable, Optional
from livekit import rtc

from livekit.agents import Agent, function_tool, get_job_context, RunContext, AgentSession, JobContext
from livekit import api, agents
from livekit.api import DeleteRoomRequest

# from prompts import WELCOME_MESSAGE, INSTRUCTIONS, USER_QUERY, ANALYZER_INSTRUCTIONS
from common.apiclient import ApiClient

class Assistant_CallforInterview(Agent):
    @function_tool(
        name="end_interview_session", 
        description="call this function if candidate is not ready or want to end the session or use inappropriate language or abusive behavior or talk irrelevant")
    async def end_interview_session( 
        self,                            
        context: RunContext,
        full_transcipt_with_label: str
    ):
        print("Ending interview session...")
        # await asyncio.shield(self.session.aclose())
        # get_job_context().delete_room()
        room = get_job_context().room        
        lkapi = api.LiveKitAPI()
        await lkapi.room.delete_room(DeleteRoomRequest(room=room.name,))    
        
    @function_tool(
        name="interview_concluded", 
        description="Call this function when interview concluded")
    async def interview_concluded( 
        self,
        context: RunContext,
        full_transcipt_with_label: str
    ):
        print("conclude interview session...")
        # await asyncio.shield(self.session.aclose())
        # get_job_context().delete_room()
        room = get_job_context().room               
        lkapi = api.LiveKitAPI()
        await lkapi.room.delete_room(DeleteRoomRequest(room=room.name,))        
    
    def __init__(self, instructions: str) -> None:
        instructions=instructions
        super().__init__(
            instructions=instructions
        )
    
    async def on_enter(self):
        self.session.generate_reply()    
                    