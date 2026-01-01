from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import aiohttp
import asyncio
import json
from livekit.agents import Agent, function_tool, get_job_context, RunContext
from livekit import api
from livekit.api import DeleteRoomRequest
from common.apiclient import ApiClient
from orderme.helper_orderme import Helper_OrderMe, Restaurant
from common.helper import Helper
from zoneinfo import ZoneInfo
import os
from typing import Dict, Any, Optional
from pydantic import Field
# from prompts import WELCOME_MESSAGE, INSTRUCTIONS, USER_QUERY, ANALYZER_INSTRUCTIONS

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
api_base_url=os.environ.get("ORDERME_BASE_URL", "")
)

class Assistant_OrderMe(Agent):
    
    @function_tool(
    name="order_status", 
    description="call this function when customer inquire about submitted order.")
    async def order_status( 
        self,
        context: RunContext,
        order_number: str
    ):
        if order_number.isdigit():
             order_id = int(order_number)
        try:
            print(order_id)
            session_info = Helper.parse_session(get_job_context().room.name)
            restaurant = await Helper_OrderMe.get_restaurant_Metadata(session_info)
            response = await client.call_api_unified(method="POST", path_or_url=restaurant.api_base_url, token_key="api-key", token=restaurant.api_auth_token, json={
            restaurant.order_confirmation_id_field: order_id
            })
            # Check if response is JSON, if not, return as plain string
            try:
                print("logging order status")
                sessionid = session_info["SessionReference"]
                await servicelog_api.call_api_unified(method="PATCH", path_or_url=f"/api/sessionlogs?session_id={sessionid}", json={ 
                        "SessionTypeId": 2,
                        "OrderId": order_number,
                    })
            except Exception as e:
                print(f"error occured: {e}") 
            try:              
                data = response.json()
                return json.dumps(data)
            except ValueError:
                # Not JSON, return as plain text
                return response.text            
        except Exception:
            return "We couldn’t find an order matching your request. If you placed it recently, please allow a few minutes for the system to update and try again shortly."     
    
    @function_tool(
        name="order_taking", 
        description="call this function everytime customer add, update or remove the item in the order.")
    async def order_taking( 
        self,
        context: RunContext,
        order_items: str
    ):
        print(order_items)
        # output = {"items": items}
        # json_output = json.dumps(output)
        # print(json_output)
        payload = order_items.encode("utf-8")
        await get_job_context().room.local_participant.publish_data(payload, reliable=True, topic="suborder")
        return "your order updated"  
    
    @function_tool(        
        name="one_time_password", 
        description="call this function to get OTP (one time password) to be confirm from the customer.")
    async def one_time_password( 
        self,
        context: RunContext,
        phone_number: str
    ):
        otp = 1234 # Helper.generate_otp()
        print(f"OTP generated: {otp}")
        # await Helper.send_sms_via_sns(phone_number, f"Your OTP is '{otp}'")
        print(phone_number)
        return f"OTP is '{otp}' (DO NOT share this with anyone), confirm the OTP with the user."  # In real implementation, generate and send OTP to customer


    @function_tool(        
        name="otp_verification", 
        description="call this function to verify OTP from the customer.")
    async def otp_verification( 
        self,
        context: RunContext,
        System_otp: str,
        Customer_otp: str
    ):
        print(System_otp)
        print(Customer_otp)
        if System_otp == Customer_otp:
            return "OTP verified successfully."
        else:   
            return "OTP not verified. Please try again."


    @function_tool(
        name="submit_final_order", 
        description="call this function to submit the final order.")
    async def submit_final_order( 
        self,
        context: RunContext,
        order: str
    ):
        # Parse the order string to dict
        if isinstance(order, str):
            order = json.loads(order)
        
        data = json.dumps(order)
        print(f"order data: {data}")
        session_info = Helper.parse_session(get_job_context().room.name)
        restaurant = await Helper_OrderMe.get_restaurant_Metadata(session_info)
        print(f"AIAgentPricePerMinute: {restaurant.AIAgentPricePerMinute}")
        response = await client.call_api_unified(method="POST", path_or_url=restaurant.api_base_url, token_key="api-key", token=restaurant.api_auth_token, json=order)
        orderconfirmation_json = response.json()
        
        print(f"AIAgentPricePerMinute: {restaurant.AIAgentPricePerMinute}")
        def json_to_readable_lines(data, indent=0, visited=None):
            """
            Convert JSON object into a human-readable, line-by-line format.
            Prevents infinite recursion on circular references.
            """
            if visited is None:
                visited = set()

            lines = []
            prefix = " " * indent

            # Avoid infinite recursion if the object is already seen
            obj_id = id(data)
            if obj_id in visited:
                lines.append(f"{prefix}[Circular reference detected]")
                return lines
            visited.add(obj_id)

            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        lines.append(f"{prefix}{key.capitalize()} details:")
                        lines.extend(json_to_readable_lines(value, indent + 2, visited))
                    else:
                        lines.append(f"{prefix}{key.capitalize()}: {value}")
            elif isinstance(data, list):
                for i, item in enumerate(data, 1):
                    lines.append(f"{prefix}Item {i}:")
                    lines.extend(json_to_readable_lines(item, indent + 2, visited))
            else:
                lines.append(f"{prefix}{data}")

            return lines
        # Convert back to JSON string
        payload = json_to_readable_lines(response.json())
        data = "\n".join(payload)
        payload  = data.encode("utf-8")
        print(payload)
        await get_job_context().room.local_participant.publish_data(payload, reliable=True, topic="finalorder")
        try:
            print("logging final order")
            orderconfirmation = json.dumps(orderconfirmation_json)
            # Temporary solution: Extract order ID from confirmation. 
            # Each restraurant may have different field names
            print(restaurant.order_confirmation_id_field)
            order_id = orderconfirmation_json.get(restaurant.order_confirmation_id_field, "N/A")
            print(f"Order ID: {order_id}")
            sessionid = session_info["SessionReference"]
            response = await servicelog_api.call_api_unified(method="PATCH", path_or_url=f"/api/sessionlogs?session_id={sessionid}", json={ 
                        "SessionTypeId": 1,
                        "OrderId": order_id,
                        "FinalOrder": order,
                        "OrderConfirmation": orderconfirmation
                    })
            
            return f"Order is submitted successfully and Order number is **{order_id}**, you will receive confirmation message shorthly on your phone. Thank you for ordering with {restaurant.name}!."
        except Exception as e:
                print(f"error occured: {e}") 

    # @function_tool(
    # name="order_submitted", 
    # description="Call this function when order number is spoken to the customer.")
    # async def order_submitted( 
    #     self,
    #     context: RunContext,
    #     order_submitted: bool
    # ):
    #     room = get_job_context().room               
    #     lkapi = api.LiveKitAPI()
    #     await lkapi.room.delete_room(DeleteRoomRequest(room=room.name,))
            
    @function_tool(
    name="delete_room", 
    description="call this function if Customer done with the order or not ready or want to end the session or use inappropriate language or abusive behavior")
    async def delete_room( 
        self,
        context: RunContext,
        high_accuracy: bool
    ):
        room = get_job_context().room               
        lkapi = api.LiveKitAPI()
        await lkapi.room.delete_room(DeleteRoomRequest(room=room.name,))        

    @function_tool(
    name="restaurant_closed", 
    description="call this function if restaurant is closed.")
    async def restaurant_closed( 
        self,
        context: RunContext,
        high_accuracy: bool
    ):
        room = get_job_context().room               
        lkapi = api.LiveKitAPI()
        await lkapi.room.delete_room(DeleteRoomRequest(room=room.name,))        
    
    @function_tool(
    name="current_time", 
    description="call this function when LLM need restaurant local current time.")
    async def current_time( 
        context: RunContext,
        restaurant_timezone: str
    ):
        print(restaurant_timezone)
        result = await Helper_OrderMe.local_current_time(restaurant_timezone)
        return result                

    @function_tool(
    name="session_started", 
    description="call this function when session starts.")
    async def session_started( 
        context: RunContext,
        status: str
    ):
        
        #Convert back to JSON string
        #payload = menu.encode("utf-8")
        #await get_job_context().room.local_participant.publish_data(payload, reliable=True, topic="menu")
        print(status)

    def __init__(self, instructions: str) -> None:
        instructions=instructions
        super().__init__(
            instructions=instructions
        )
        
    async def on_enter(self):
        self.session.generate_reply()   