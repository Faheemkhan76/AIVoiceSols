import os
import asyncio
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import UserStateChangedEvent, function_tool, get_job_context
from common.apiclient import ApiClient
from common.helper import Helper
from session_factory import SessionFactory

load_dotenv()

logger = logging.getLogger("replacing-llm-output")
logger.setLevel(logging.INFO)
    
client = ApiClient(
client_id=os.environ.get("COGNITO_CLIENT_ID"),
client_secret=os.environ.get("COGNITO_CLIENT_SECRET"),
token_url=os.environ.get("COGNITO_TOKEN_URL"),
api_base_url=os.environ.get("CFI_BASE_URL")
)

async def entrypoint(ctx: agents.JobContext):    
    startdatetime = datetime.now()
             
    reference = "disabled"    
    session_id = ctx.room.name
    session_info = Helper.parse_session(session_id)
    print(f"Session Info: {session_info}")
    
    session_handler = None
    if isinstance(session_info, dict):
        print(f"Starting session for Application: {session_info['ApplicationName']}, CustomerReference: {session_info['CustomerReference']}, SessionReference: {session_info['SessionReference']}") 
        session_handler = SessionFactory.create_session(session_info['ApplicationName'])
        session_param = session_info
    else:
        print(f"Starting session with name: {ctx.room.name}")
        session_handler = SessionFactory.create_session("CALLFORINTERVIEW")  # Default
        session_param = session_id  # ctx.room.name
    
    print(f'session_param: {session_param}')
    session = await session_handler.create_agent_session()
    await session_handler.start_session(ctx, session, session_param, startdatetime)

    
    # inactivity tracking: only start inactivity when user has actually been idle
    INACTIVITY_THRESHOLD = float(os.environ.get("INACTIVITY_THRESHOLD", "25"))
    AGENT_RECENT_GRACE = float(os.environ.get("AGENT_RECENT_GRACE", "3"))

    inactivity_task: asyncio.Task | None = None
    # track last activity timestamps (monotonic)
    loop = asyncio.get_event_loop()
    last_user_activity = loop.time()
    last_agent_activity = 0.0
    agent_state: str = "idle"

    async def user_presence_task():
        # try to ping the user 3 times, if we get no answer, close the session
        print("User inactive, ending session...")
        try:
            await asyncio.shield(session.aclose())
        finally:
            ctx.delete_room()

    # update on user transcription events (user spoke)
    @session.on("user_input_transcribed")
    def _on_user_input_transcribed(ev):
        nonlocal last_user_activity, inactivity_task
        last_user_activity = loop.time()
        if inactivity_task is not None:
            inactivity_task.cancel()
            inactivity_task = None

    # update on agent state changes (agent speaking should suppress inactivity)
    @session.on("agent_state_changed")
    def _on_agent_state_changed(ev):
        nonlocal last_agent_activity, agent_state, inactivity_task
        agent_state = ev.new_state
        if ev.new_state == "speaking":
            last_agent_activity = loop.time()
            # cancel any running inactivity timer while agent speaks
            if inactivity_task is not None:
                inactivity_task.cancel()
                inactivity_task = None

    @session.on("user_state_changed")
    def _user_state_changed(ev: UserStateChangedEvent):
        nonlocal inactivity_task, last_user_activity, last_agent_activity, agent_state

        now = loop.time()
        # Only start inactivity timer if the user is away AND we haven't seen recent user activity
        # and the agent has not been speaking very recently (to avoid false away while agent speaks)
        if ev.new_state == "away":
            user_idle = now - last_user_activity
            agent_recent = (now - last_agent_activity) < AGENT_RECENT_GRACE
            if user_idle >= INACTIVITY_THRESHOLD and not agent_recent:
                print("User is away and idle, starting inactivity timer...")
                inactivity_task = asyncio.create_task(user_presence_task())
            else:
                print(f"Ignoring away: user_idle={user_idle:.1f}s agent_recent={agent_recent}")
            return

        # ev.new_state: listening, speaking, .. cancel inactivity if user returns
        if inactivity_task is not None:
            inactivity_task.cancel()
            inactivity_task = None

        
        
    await ctx.connect()
    participant  = await ctx.wait_for_participant()
    print(f'room/session_id:{session_id} participant/user: {participant.name}')
    # Register shutdown callback to perform session end activities.
    print(f'session_param: {session_param}')
    ctx.add_shutdown_callback(lambda: session_handler.manage_shutdown(ctx, session,session_param, participant, startdatetime, reference)) 
   
if __name__ == "__main__":
   #agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint,  agent_name="365AIVoiceSols"))
   agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))  