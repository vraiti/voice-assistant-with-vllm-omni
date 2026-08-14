import logging
import os

import httpx
from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    cli,
    TurnHandlingOptions,
    inference,
)
from livekit.agents.metrics import RealtimeModelMetrics
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


def _on_metrics_collected(event) -> None:
    metrics = event.metrics
    if not isinstance(metrics, RealtimeModelMetrics):
        return
    if metrics.ttft >= 0:
        logger.info(
            "TTFA %.3fs (request_id=%s, duration=%.3fs, cancelled=%s)",
            metrics.ttft,
            metrics.request_id,
            metrics.duration,
            metrics.cancelled,
        )
    else:
        logger.info(
            "No audio token received (request_id=%s, duration=%.3fs, cancelled=%s)",
            metrics.request_id,
            metrics.duration,
            metrics.cancelled,
        )


@server.rtc_session(agent_name="voice-assistant")
async def entrypoint(ctx: JobContext):
    model_name = await _get_model_name()

    model = RealtimeModel(
        base_url=VLLM_BASE_URL,
        model=model_name,
        api_key="unused",
    )

    session = AgentSession(
        llm=model,
        turn_handling=TurnHandlingOptions(
            turn_detection=inference.TurnDetector(),
        ),
    )

    session.on("metrics_collected", _on_metrics_collected)

    await session.start(
        agent=VoiceAssistant(),
        room=ctx.room,
    )

    logger.info(
        "Voice assistant started (vad=%s, model=%s), connected to vLLM-Omni at %s",
        model_name,
        VLLM_BASE_URL,
    )


if __name__ == "__main__":
    cli.run_app(server)
