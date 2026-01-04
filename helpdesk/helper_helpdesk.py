import os
import json
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from common.apiclient import ApiClient
from enum import Enum
from dataclasses import dataclass
from typing import Any

client = ApiClient(
    client_id=os.environ.get("COGNITO_CLIENT_ID"),
    client_secret=os.environ.get("COGNITO_CLIENT_SECRET"),
    token_url=os.environ.get("COGNITO_TOKEN_URL"),
    api_base_url=os.environ.get("CSS_BASE_URL")
)

@dataclass
class HelpdeskConfig:
    name: str
    organization_id: int
    description: str
    support_email: str
    support_phone: str
    business_hours: str
    api_base_url: str
    api_auth_token: str
    timezone: str
    escalation_config: Any = None
    
class Helper_Helpdesk:    
    class Products(Enum):
        CALLFORINTERVIEW = 1
        CALLFORINTERVIEW_CORP = 2
        ORDERME = 3
        HELPDESK = 4  
        
    @staticmethod
    async def get_organization(customer_reference: str):
        """
        Fetch organization details from the API
        Returns: dict with organization details or None if failed
        """
        try:
            response = await client.call_api_unified(
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
    
    @staticmethod
    async def get_instruction(organization: dict):
        instruction = organization.get("Instruction", None) if organization else None
    
        # from string import Template
        # template = Template(instruction)
        # result = template.substitute(
        #     organization_name=organization.get("Name"),        
        # )
        # return result
        return instruction
    
    @staticmethod
    async def local_current_time(timezone_str: str):
        base_utc = datetime.now(timezone.utc)

        # Resolve timezone robustly: try zoneinfo first, then python-dateutil, then fallback to UTC
        tzinfo = None
        try:
            # zoneinfo may exist but the system tzdata may be missing (ZoneInfo may raise ZoneInfoNotFoundError)
            from zoneinfo import ZoneInfo
            try:
                tzinfo = ZoneInfo(timezone_str)
            except Exception:
                tzinfo = None
        except Exception:
            tzinfo = None        
        if tzinfo is None:
            try:
                # dateutil provides a fallback tz database when installed
                from dateutil import tz as dateutil_tz
                tzinfo = dateutil_tz.gettz(timezone_str) or timezone.utc
            except Exception:
                tzinfo = timezone.utc

        local_time = base_utc.astimezone(tzinfo)
        # Return long date format e.g., 'Oct/Monday/2025'
        # Format: Date: Wednesday, October 22, 2025; Time: 21:28
        date_part = local_time.strftime("%A, %B %d, %Y")
        time_part = local_time.strftime("%H:%M")
        result = f"Current Date: {date_part}; Current Time: {time_part}"
        print(result)
        return result
