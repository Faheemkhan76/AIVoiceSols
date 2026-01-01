from abc import ABC, abstractmethod
from livekit.agents import AgentSession, JobContext

class BaseSession(ABC):
    @abstractmethod
    async def create_agent_session(self) -> AgentSession:
        pass

    @abstractmethod
    async def start_session(self, ctx: JobContext, session: AgentSession, session_param, startdatetime):
        pass

    @abstractmethod
    async def manage_shutdown(self, ctx: JobContext, session: AgentSession, participant, startdatetime, reference):
        pass