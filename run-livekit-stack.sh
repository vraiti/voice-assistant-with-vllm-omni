#!/usr/bin/env bash
# Runs the frontend, LiveKit server, and agent together; exits (and tears
# down the other two) the moment any one of them exits.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/../agent-starter-react"
AGENT_DIR="$SCRIPT_DIR/agent"
LOG_DIR="/tmp/livekit"

mkdir -p "$LOG_DIR"

pids=()

cleanup() {
    for pid in "${pids[@]}"; do
        kill "$pid" 2>/dev/null
    done
    wait 2>/dev/null
}
trap cleanup EXIT INT TERM

(cd "$FRONTEND_DIR" && pnpm dev) > "$LOG_DIR/frontend.log" 2>&1 &
pids+=("$!")

livekit-server --dev > "$LOG_DIR/server.log" 2>&1 &
pids+=("$!")

(cd "$AGENT_DIR" && source .env.local && uv run src/agent.py start) > "$LOG_DIR/agent.log" 2>&1 &
pids+=("$!")

echo "frontend pid=${pids[0]} -> $LOG_DIR/frontend.log"
echo "server   pid=${pids[1]} -> $LOG_DIR/server.log"
echo "agent    pid=${pids[2]} -> $LOG_DIR/agent.log"

wait -n "${pids[@]}"
exit_code=$?
echo "A process exited (code $exit_code) -- shutting the rest down."
exit "$exit_code"
