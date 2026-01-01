from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import aiohttp
import asyncio
import json
from livekit.agents import Agent, function_tool, get_job_context, RunContext
from livekit import api
from livekit.api import DeleteRoomRequest
from common.apiclient import ApiClient
from common.helper import Helper
from zoneinfo import ZoneInfo
import os

load_dotenv()

client = ApiClient(
    client_id="",
    client_secret="",
    token_url="",
    api_base_url=""
)

servicelog_api = ApiClient(
    client_id=os.environ.get("COGNITO_CLIENT_ID", ""),
    client_secret=os.environ.get("COGNITO_CLIENT_SECRET", ""),
    token_url=os.environ.get("COGNITO_TOKEN_URL", ""),
    api_base_url=os.environ.get("HELPDESK_BASE_URL", "")
)

class Assistant_Helpdesk(Agent):
    
    # @function_tool(
    #     name="create_ticket", 
    #     description="call this function when customer wants to create a support ticket.")
    # async def create_ticket( 
    #     self,
    #     context: RunContext,
    #     issue_description: str,
    #     priority: str = "medium"
    # ):
    #     try:
    #         session_info = Helper.parse_session(get_job_context().room.name)
    #         ticket_data = {
    #             "description": issue_description,
    #             "priority": priority,
    #             "customer_reference": session_info.get('CustomerReference', 'unknown'),
    #             "session_reference": session_info.get('SessionReference', 'unknown'),
    #             "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #         }
            
    #         response = await servicelog_api.call_api_unified(
    #             method="POST", 
    #             path_or_url="/api/tickets", 
    #             json=ticket_data
    #         )
            
    #         if response.status_code == 201:
    #             ticket_info = response.json()
    #             ticket_id = ticket_info.get('ticket_id', 'N/A')
    #             return f"Support ticket created successfully. Ticket ID: {ticket_id}. We will get back to you soon."
    #         else:
    #             return "Sorry, there was an issue creating your support ticket. Please try again later."
                
    #     except Exception as e:
    #         print(f"Error creating ticket: {e}")
    #         return "Sorry, there was an issue creating your support ticket. Please try again later."

    # @function_tool(
    #     name="check_ticket_status", 
    #     description="call this function when customer inquires about their support ticket status.")
    # async def check_ticket_status( 
    #     self,
    #     context: RunContext,
    #     ticket_id: str
    # ):
    #     try:
    #         response = await servicelog_api.call_api_unified(
    #             method="GET", 
    #             path_or_url=f"/api/tickets/{ticket_id}"
    #         )
            
    #         if response.status_code == 200:
    #             ticket_info = response.json()
    #             status = ticket_info.get('status', 'unknown')
    #             created_date = ticket_info.get('created_at', 'unknown')
    #             description = ticket_info.get('description', 'No description available')
                
    #             return f"Ticket #{ticket_id} - Status: {status}. Created: {created_date}. Issue: {description}"
    #         else:
    #             return f"Sorry, I couldn't find a ticket with ID {ticket_id}. Please check the ticket number and try again."
                
    #     except Exception as e:
    #         print(f"Error checking ticket status: {e}")
    #         return "Sorry, there was an issue checking your ticket status. Please try again later."

    
    # @function_tool(
    #     name="escalate_to_human", 
    #     description="call this function when customer requests to speak with a human agent.")
    # async def escalate_to_human( 
    #     self,
    #     context: RunContext,
    #     reason: str = "Customer requested human assistance"
    # ):
    #     try:
    #         session_info = Helper.parse_session(get_job_context().room.name)
    #         escalation_data = {
    #             "reason": reason,
    #             "customer_reference": session_info.get('CustomerReference', 'unknown'),
    #             "session_reference": session_info.get('SessionReference', 'unknown'),
    #             "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #         }
            
    #         response = await servicelog_api.call_api_unified(
    #             method="POST", 
    #             path_or_url="/api/escalations", 
    #             json=escalation_data
    #         )
            
    #         if response.status_code == 201:
    #             escalation_info = response.json()
    #             wait_time = escalation_info.get('estimated_wait_time', '5-10 minutes')
    #             return f"I'm connecting you to a human agent. Estimated wait time: {wait_time}. Please stay on the line."
    #         else:
    #             return "I'm having trouble connecting you to a human agent right now. Please try again in a few minutes or create a support ticket."
                
    #     except Exception as e:
    #         print(f"Error escalating to human: {e}")
    #         return "I'm having trouble connecting you to a human agent right now. Please try again in a few minutes or create a support ticket."

    @function_tool(
        name="current_rate", 
        description="call this function if Customer ask about current rate.")
    async def current_rate( 
            self,
            context: RunContext,
            customer_details: str
        ):
            print(f"Fetching current rate for customer details: {customer_details}")
            return "The current rate is 5.25% APR. Please note that rates may vary based on individual qualifications and market conditions. For personalized rate information, I recommend speaking with a mortgage specialist."
        
    @function_tool(
        name="delete_room", 
        description="call this function if Customer not ready or want to end the session, use inappropriate language, abusive behavior or ask questions which not related to helpdesk.")
    async def delete_room( 
            self,
            context: RunContext,
            high_accuracy: bool
        ):
            room = get_job_context().room               
            lkapi = api.LiveKitAPI()
            await lkapi.room.delete_room(DeleteRoomRequest(room=room.name,))        

    @function_tool(
        name="current_time", 
        description="call this function to get the current date and time.")
    async def current_time(
        self,
        context: RunContext
    ):
        try:
            # Get current UTC time
            utc_now = datetime.now(timezone.utc)
            # Convert to local timezone (you can customize this based on customer location)
            local_time = utc_now.replace(tzinfo=timezone.utc)
            
            # Format: Date: Wednesday, October 22, 2025; Time: 21:28
            date_part = local_time.strftime("%A, %B %d, %Y")
            time_part = local_time.strftime("%H:%M")
            result = f"Current Date: {date_part}; Current Time: {time_part} UTC"
            print(result)
            return result
            
        except Exception as e:
            print(f"Error getting current time: {e}")
            return "I'm having trouble getting the current time. Please try again."
        
    async def on_enter(self):
        self.session.generate_reply() 