# Voice Assistant with vLLM-Omni

Real-time voice assistant powered by [Qwen3-Omni](https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct) served via [vLLM-Omni](https://github.com/vllm-project/vllm-omni), with a [LiveKit](https://livekit.io/) frontend.

## Architecture

```
[Local machine]                                           [GPU server]
┌──────────┐  WebRTC  ┌──────────────┐                    ┌─────────────────────┐
│ Browser   │◄───────►│ LiveKit      │                    │ vLLM-Omni           │
│ (React)   │         │ Server :7880 │                    │ Qwen3-Omni          │
│ :3000     │         └──────┬───────┘                    │ :8000               │
└──────────┘                 │                            └──────────┬──────────┘
                             ▼                            WebSocket   │
                    ┌──────────────────┐◄──────────────────────────►│
                    │ LiveKit Agent    │  ws://<gpu-host>:8000/v1/realtime
                    │ (Python)         │
                    └──────────────────┘
```

The browser captures audio via WebRTC, LiveKit routes it to a Python agent, and the agent streams it to vLLM-Omni's `/v1/realtime` WebSocket endpoint. Qwen3-Omni processes the audio natively (no separate STT/TTS) and streams spoken responses back.

## Project Structure

```
├── agent/                  # LiveKit Python agent (connects to vLLM-Omni via RealtimeModel)
│   ├── .env.local          # LiveKit + VLLM_BASE_URL config (not checked in)
│   └── src/agent.py
└── run-livekit-stack.sh    # Runs frontend + LiveKit server + agent together
```

The frontend lives outside this repo, in the sibling `agent-starter-react/` directory. vLLM-Omni itself is deployed separately (see `vllm-omni-aux/utils/deploy.py`), not by this repo.

## Setup

1. **GPU server** — deploy vLLM-Omni serving Qwen3-Omni with the `/v1/realtime` endpoint enabled.
2. **`agent/.env.local`** — set `LIVEKIT_URL`/`LIVEKIT_API_KEY`/`LIVEKIT_API_SECRET` (dev-mode defaults: `ws://localhost:7880` / `devkey` / `secret`) and `VLLM_BASE_URL` pointing at the GPU server's `/v1/realtime`-serving port.
3. **Run the stack:**

   ```bash
   ./run-livekit-stack.sh
   ```

   This starts the `agent-starter-react` frontend, a dev-mode `livekit-server`, and the agent together, tearing all three down if any one exits. Logs go to `/tmp/livekit/{frontend,server,agent}.log`.

Open http://localhost:3000, click **Start Conversation**, and speak.

## Troubleshooting

**Agent can't connect to vLLM-Omni:**
- Confirm the GPU server is serving `/v1/realtime` and is reachable from the local machine.
- Enable debug logging: `LK_OPENAI_DEBUG=1 uv run src/agent.py dev` (from `agent/`).

**No audio response:**
- Check browser microphone permissions.
- Verify the agent registered with LiveKit (check `/tmp/livekit/agent.log` for a "registered" message).
- Ensure `LIVEKIT_URL` in `agent/.env.local` matches the LiveKit server address.
