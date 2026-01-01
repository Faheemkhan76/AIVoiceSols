# from livekit.agents import AgentSession, RoomInputOptions
# # from livekit.plugins.turn_detector.english import EnglishModel
# from livekit.plugins import google
# from livekit.plugins import (noise_cancellation)
# from assistant_orderme import Assistant_OrderMe
# from livekit.plugins import (noise_cancellation)
# from google.genai import types

# class OrderMe_Session:
#     @staticmethod
#     async def create_agent_session():
#         return AgentSession(
#                     # llm=google.realtime.RealtimeModel(
#                     #     model="gemini-2.0-flash-exp",
#                     #     voice="Puck",
#                     #     temperature=0.8,
#                     #     modalities= ["AUDIO"]                
#                     # ),
#                     llm=google.beta.realtime.RealtimeModel(
#                         model="gemini-live-2.5-flash-preview",
#                         voice="Puck",
#                         temperature=0.8,
#                         modalities= ["AUDIO"]
#                     ),
#                     user_away_timeout=12 # time in seconds to detect silence
#                 )

#     @staticmethod
#     async def start_session(ctx, session, instructions):
#         await session.start(
#                     room=ctx.room,
#                     agent=Assistant_OrderMe(instructions=instructions),
#                     room_input_options=RoomInputOptions(noise_cancellation=noise_cancellation.BVC())                
#                 )