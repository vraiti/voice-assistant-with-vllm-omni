import json
import logging
import os

import httpx
from dotenv import load_dotenv
from livekit.agents import Agent, AgentServer, AgentSession, AutoSubscribe, JobContext, cli
from livekit.plugins import silero
from livekit.plugins.openai.realtime import RealtimeModel

load_dotenv(".env.local")
logger = logging.getLogger("voice-assistant")

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:9090/v1")

server = AgentServer()


class VoiceAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are a helpful voice assistant. Respond naturally and concisely.",
        )


async def _get_model_name() -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{VLLM_BASE_URL}/models")
        resp.raise_for_status()
        data = resp.json()
    models = data.get("data", [])
    if not models:
        raise RuntimeError(f"No models available at {VLLM_BASE_URL}/models")
    model_id = models[0]["id"]
    logger.info("Using model: %s", model_id)
    return model_id


def _get_vad_mode(ctx: JobContext) -> str:
    metadata = ctx.room.metadata
    if metadata:
        try:
            data = json.loads(metadata)
            mode = data.get("vad_mode", "client")
            if mode in ("client", "semantic"):
                return mode
        except (json.JSONDecodeError, AttributeError):
            pass
    return "client"


@server.rtc_session(agent_name="voice-assistant")
async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    model_name = await _get_model_name()
    vad_mode = _get_vad_mode(ctx)
    logger.info("VAD mode: %s", vad_mode)

    if vad_mode == "semantic":
        model = RealtimeModel(
            base_url=VLLM_BASE_URL,
            model=model_name,
            api_key="unused",
        )
        session = AgentSession(llm=model)
    else:
        model = RealtimeModel(
            base_url=VLLM_BASE_URL,
            model=model_name,
            api_key="unused",
            turn_detection=None,
        )
        session = AgentSession(
            llm=model,
            vad=silero.VAD.load(min_silence_duration=0.5),
            turn_detection="vad",
        )

    await session.start(
        agent=VoiceAssistant(),
        room=ctx.room,
    )

    logger.info("Voice assistant started (vad=%s, model=%s), connected to vLLM-Omni at %s", vad_mode, model_name, VLLM_BASE_URL)


if __name__ == "__main__":
    cli.run_app(server)
