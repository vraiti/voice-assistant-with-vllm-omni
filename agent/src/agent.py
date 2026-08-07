import logging
import os

from dotenv import load_dotenv
from livekit.agents import Agent, AgentServer, AgentSession, AutoSubscribe, JobContext, cli
from livekit.plugins import silero
from livekit.plugins.openai.realtime import RealtimeModel

load_dotenv(".env.local")
logger = logging.getLogger("voice-assistant")

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8091/v1")

server = AgentServer()


class VoiceAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are a helpful voice assistant. Respond naturally and concisely.",
        )


@server.rtc_session(agent_name="voice-assistant")
async def entrypoint(ctx: JobContext):
    model = RealtimeModel(
        base_url=VLLM_BASE_URL,
        model="Qwen/Qwen3-Omni-30B-A3B-Instruct",
        api_key="unused",
        turn_detection=None,
    )

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    session = AgentSession(
        llm=model,
        vad=silero.VAD.load(min_silence_duration=0.5),
        turn_detection="vad",
    )
    await session.start(
        agent=VoiceAssistant(),
        room=ctx.room,
    )

    logger.info("Voice assistant started, connected to vLLM-Omni at %s", VLLM_BASE_URL)


if __name__ == "__main__":
    cli.run_app(server)
