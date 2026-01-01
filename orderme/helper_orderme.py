import os
import json
from dotenv import load_dotenv

from datetime import datetime, timezone, timedelta
from orderme.prompts_orderme import INSTRUCTIONS
from common.apiclient import ApiClient
from enum import Enum
from dataclasses import dataclass
from typing import Any

client = ApiClient(
client_id=os.environ.get("COGNITO_CLIENT_ID"),
client_secret=os.environ.get("COGNITO_CLIENT_SECRET"),
token_url=os.environ.get("COGNITO_TOKEN_URL"),
api_base_url=os.environ.get("CFI_BASE_URL")
)

@dataclass
class Restaurant:
    name: str
    restaurant_id: int
    description: str
    address: str
    website_url: str
    policies: str
    api_base_url: str
    api_auth_token: str
    menu_endpoint: str
    order_endpoint: str
    order_sample: str
    status_endpoint: str
    timezone: str
    order_confirmation_id_field: str
    operational_config: Any = None
    AIAgentPricePerMinute: float = 0.0
    
class Helper_OrderMe:    
    class Products(Enum):
        CALLFORINTERVIEW = 1
        CALLFORINTERVIEW_CORP = 2
        ORDERME = 3
    
    @staticmethod
    async def get_restaurant_Metadata(session_info: dict):
        customer_reference = session_info['CustomerReference']
        response = await client.call_api_unified(method="POST", path_or_url=f"https://bistrocircle.base44.app/functions/getRestaurantById", token_key="x-api-key", token="b470ca71aaf44cb086a823175ec16cb8", json={
            "restaurant_id": customer_reference
            })
        data = response.json()
        restaurant_data = data["data"]
        def _maybe_load(obj):
            # If obj is a str, try to parse JSON, otherwise return as-is
            if isinstance(obj, str):
                try:
                    return json.loads(obj)
                except Exception:
                    return obj
            return obj

        restaurant = Restaurant( 
            name=restaurant_data.get("name"),
            restaurant_id=customer_reference,
            description=restaurant_data.get("description"),
            address=restaurant_data.get("address"),
            website_url=restaurant_data.get("website_url"),
            policies=restaurant_data.get("policies"),
            api_base_url=restaurant_data.get("api_base_url"),
            api_auth_token=restaurant_data.get("api_auth_token"),
            menu_endpoint=restaurant_data.get("menu_endpoint"),
            order_endpoint=restaurant_data.get("order_endpoint"),
            order_sample=_maybe_load(restaurant_data.get("order_endpoint", {}).get("sample_body")),
            order_confirmation_id_field=_maybe_load(restaurant_data.get("order_endpoint", {}).get("order_confirmation_id_field")),
            status_endpoint=restaurant_data.get("status_endpoint"),
            timezone=restaurant_data.get("timezone"),
            operational_config=_maybe_load(restaurant_data.get("operational_config")),
            AIAgentPricePerMinute=float(restaurant_data.get("AIAgentPricePerMinute", 0.0))
        ) 
        return restaurant        
        
    @staticmethod
    async def get_instruction(session_info: dict):
        restaurant = await Helper_OrderMe.get_restaurant_Metadata(session_info)
        response = await client.call_api_unified(method="POST", path_or_url=restaurant.api_base_url, token_key="api-key", token=restaurant.api_auth_token)
        menu = response.json()
        from string import Template
        template = Template(INSTRUCTIONS)
        result = template.substitute(
            current_datetime= await Helper_OrderMe.local_current_time(restaurant.timezone),
            restaurant_type="Desi",
            restaurant_name=restaurant.name,
            about_restaurant=restaurant.description,
            order_types="Dine-in, Takeaway, Home Delivery",
            order_charges="All taxes and delivery charges are included in the order total.",    
            restaurant_menu=json.dumps(menu, indent=4),
            order_format=json.dumps(restaurant.order_sample, indent=4),
            operational_config=json.dumps(restaurant.operational_config, indent=4)
        )
        return result
    
    @staticmethod
    async def local_current_time(     
        restaurant_timezone: str
    ):
        base_utc = datetime.now(timezone.utc) #- timedelta(hours=2)

        # Resolve timezone robustly: try zoneinfo first, then python-dateutil, then fallback to UTC
        tzinfo = None
        try:
            # zoneinfo may exist but the system tzdata may be missing (ZoneInfo may raise ZoneInfoNotFoundError)
            from zoneinfo import ZoneInfo
            try:
                tzinfo = ZoneInfo(restaurant_timezone)
            except Exception:
                tzinfo = None
        except Exception:
            tzinfo = None        
        if tzinfo is None:
            try:
                # dateutil provides a fallback tz database when installed
                from dateutil import tz as dateutil_tz

                tzinfo = dateutil_tz.gettz(restaurant_timezone) or timezone.utc
            except Exception:
                tzinfo = timezone.utc

        local_time = base_utc.astimezone(tzinfo)
        # Return long date format e.g., 'Oct/Monday/2025'
        # Format: Date: Wednesday, October 22, 2025; Time: 21:28
        date_part = local_time.strftime("%A, %B %d, %Y")
        time_part = local_time.strftime("%H:%M")
        result = f"Current Date: {date_part}; Current Time: {time_part}"
        return result