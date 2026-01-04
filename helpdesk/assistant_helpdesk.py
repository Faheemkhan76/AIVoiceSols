from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import aiohttp
import asyncio
import json
from helpdesk.helper_helpdesk import Helper_Helpdesk
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
        name="forward_to_human", 
        description="call this function when the customer requests to speak with a human agent, loan officer, mortgage specialist, or representative. Also use when the customer's question is too complex or outside your scope.")
    async def forward_to_human( 
            self,
            context: RunContext,
            reason: str
        ):
            """
            Forward the call to a human representative using cold transfer.
            Args:
                reason: Brief description of why the customer needs human assistance
            """
            room = get_job_context().room
            session_info = Helper.parse_session(room.name)
            customer_reference = session_info.get("CustomerReference")
            
            print(f"Forwarding call to human representative. Reason: {reason}")
            print(f"Room: {room.name}, Customer Reference: {customer_reference}")
            
            # Find the SIP participant (the actual caller)
            sip_participant = None
            for participant in room.remote_participants.values():
                if participant.identity.startswith("sip_"):
                    sip_participant = participant
                    break
            
            if not sip_participant:
                print("No SIP participant found in room")
                print(f"Available participants: {[p.identity for p in room.remote_participants.values()]}")
                return "I understand you'd like to speak with a specialist. I'm having trouble locating your call session. Please try calling back."
            
            participant_identity = sip_participant.identity
            print(f"Found SIP participant: {participant_identity}")
            
            # Fetch organization to get forwarding number
            try:
                organization = await Helper_Helpdesk.get_organization(customer_reference)
                
                if not organization:
                    print("Failed to fetch organization details")
                    return "I apologize, but I'm having trouble connecting you to a specialist right now. Please try calling back in a moment."
                
                forwarding_number = organization.get("ForwardingNumber")
                
                if not forwarding_number:
                    print("No forwarding number configured for this organization")
                    return "I apologize, but no forwarding number is configured. Please contact support directly."
                
                # Format the forwarding number as tel: URI (as per the example)
                # Remove any spaces, dashes, or parentheses
                clean_number = forwarding_number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
                
                # Ensure it starts with + for international format
                if not clean_number.startswith("+"):
                    if clean_number.startswith("1") and len(clean_number) == 11:
                        clean_number = "+" + clean_number
                    elif len(clean_number) == 10:
                        clean_number = "+1" + clean_number
                
                # Format as tel: URI (as shown in the GitHub example)
                transfer_to = f"tel:{clean_number}"
                
                print(f"Transferring call from {participant_identity} to {transfer_to}")
                
                # Perform the transfer
                await self._handle_transfer(participant_identity, transfer_to, reason)
                
                return f"Thank you for your patience. I'm transferring you now to one of our specialists who can better assist you with {reason}. Please stay on the line."
                
            except Exception as e:
                print(f"Error during call transfer: {e}")
                import traceback
                traceback.print_exc()
                return "I'm sorry, I couldn't transfer your call. Is there something else I can help with?"
    
    async def _handle_transfer(self, participant_identity: str, transfer_to: str, reason: str) -> None:
        """
        Handle the transfer process with messaging.
        Args:
            participant_identity: The participant's identity
            transfer_to: The number to transfer to
            reason: The reason for transfer
        """
        # Generate reply before transfer
        await self.session.generate_reply(
            user_input=f"I'm transferring you to our specialist team for {reason}. Please hold for just a moment."
        )
        
        # Wait a moment for the message to be delivered
        await asyncio.sleep(3)
        
        # Execute the transfer
        await self.transfer_call(participant_identity, transfer_to)
    
    async def transfer_call(self, participant_identity: str, transfer_to: str) -> None:
        """
        Transfer the SIP call to another number.
        Args:
            participant_identity: The identity of the participant
            transfer_to: The phone number to transfer the call to (tel: URI format)
        """
        print(f"Transferring call for participant {participant_identity} to {transfer_to}")
        
        try:
            room = get_job_context().room
            
            # Get LiveKit API credentials
            livekit_url = os.getenv('LIVEKIT_URL')
            api_key = os.getenv('LIVEKIT_API_KEY')
            api_secret = os.getenv('LIVEKIT_API_SECRET')
            
            print(f"Initializing LiveKit API client with URL: {livekit_url}")
            
            livekit_api = api.LiveKitAPI(
                url=livekit_url,
                api_key=api_key,
                api_secret=api_secret
            )
            
            # Import the protocol buffer version of the request
            from livekit.protocol import sip as proto_sip
            
            transfer_request = proto_sip.TransferSIPParticipantRequest(
                participant_identity=participant_identity,
                room_name=room.name,
                transfer_to=transfer_to,
                play_dialtone=True
            )
            
            print(f"Transfer request: {transfer_request}")
            
            await livekit_api.sip.transfer_sip_participant(transfer_request)
            
            print(f"Successfully transferred participant {participant_identity} to {transfer_to}")
            
        except Exception as e:
            error_message = str(e)
            print(f"Failed to transfer call: {e}")
            import traceback
            traceback.print_exc()
            
            # Check if it's a "not yet supported" error - this is expected for PSTN transfers
            if "don't yet support transfers" in error_message or "not yet supported" in error_message:
                print("LiveKit does not support PSTN transfers. Implementing callback flow.")
                
                # Inform the user we'll arrange a callback
                await self.session.generate_reply(
                    user_input="I apologize, but I'm unable to transfer your call directly at this time. "
                    "However, I've noted your request, and one of our specialists will call you back at this number "
                    "within the next 5-10 minutes. Can I help you with anything else while you wait?"
                )
                
                # Log the callback request
                # try:
                #     session_info = Helper.parse_session(room.name)
                #     customer_reference = session_info.get("CustomerReference")
                    
                #     await servicelog_api.call_api_unified(
                #         method="POST",
                #         path_or_url=f"api/organizations/{customer_reference}/callbacks",
                #         json={
                #             "session_id": session_info.get("SessionReference"),
                #             "customer_number": session_info.get("PhoneNumber"),
                #             "forwarding_number": transfer_to.replace("tel:", ""),
                #             "requested_at": datetime.now(timezone.utc).isoformat(),
                #             "status": "pending",
                #             "notes": "Customer requested to speak with a specialist"
                #         }
                #     )
                #     print("Callback request logged successfully")
                # except Exception as log_error:
                #     print(f"Failed to log callback request: {log_error}")
            else:
                # For other errors, provide a generic message
                await self.session.generate_reply(
                    user_input="I'm sorry, I couldn't transfer your call. Is there something else I can help with?"
                )
        
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