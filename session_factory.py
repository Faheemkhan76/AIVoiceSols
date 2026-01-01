from common.base_session import BaseSession
from callforinterview.callforinterview_session import CallForInterviewSession
from callforinterview_corp.callforinterview_corp_session import CallForInterviewCorpSession
from orderme.orderme_session_new import OrderMeSession
from helpdesk.helpdesk_session import HelpdeskSession
import re


class SessionFactory:
    @staticmethod
    def create_session(product_name: str) -> BaseSession:
        """
        Create a session handler for the given product name.

        This method normalizes the incoming product_name so common variants
        (underscores, hyphens, or missing separators) map correctly. For
        example, both "CALLFORINTERVIEW_CORP" and "CALLFORINTERVIEWCORP"
        will resolve to the corp session handler.
        """
        if not product_name:
            raise ValueError("product_name is required to create a session")

        # Normalize: uppercase and remove non-alphanumeric characters
        normalized = re.sub(r'[^A-Z0-9]', '', product_name.upper())

        mapping = {
            'CALLFORINTERVIEW': CallForInterviewSession,
            'CALLFORINTERVIEWCORP': CallForInterviewCorpSession,
            'ORDERME': OrderMeSession,
            'HELPDESK': HelpdeskSession,
        }

        # Direct lookup
        if normalized in mapping:
            return mapping[normalized]()

        # Try a few heuristics: e.g., if name contains CALLFORINTERVIEW then pick that
        if 'CALLFORINTERVIEW' in normalized:
            # Choose corp variant only if 'CORP' is present
            if 'CORP' in normalized:
                return CallForInterviewCorpSession()
            return CallForInterviewSession()

        if 'ORDERME' in normalized:
            return OrderMeSession()

        if 'HELPDESK' in normalized:
            return HelpdeskSession()

        raise ValueError(f"Unknown product: {product_name}")