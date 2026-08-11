"use client";

import {
  LiveKitRoom,
  RoomAudioRenderer,
  BarVisualizer,
  DisconnectButton,
  useVoiceAssistant,
  useLocalParticipant,
  useTrackVolume,
} from "@livekit/components-react";
import "@livekit/components-styles";
import type { AgentState } from "@livekit/components-react";
import { LocalAudioTrack } from "livekit-client";
import { useCallback, useState } from "react";

interface ConnectionDetails {
  serverUrl: string;
  roomName: string;
  participantName: string;
  participantToken: string;
}

function UserMicIndicator() {
  const { microphoneTrack } = useLocalParticipant();
  const track = microphoneTrack?.track as LocalAudioTrack | undefined;
  const volume = useTrackVolume(track);
  const isSpeaking = volume > 0.01;
  const state: AgentState = isSpeaking ? "speaking" : "listening";

  return (
    <div className="flex flex-col items-center gap-4">
      <p className="text-xs font-medium tracking-wide text-zinc-500 uppercase">
        You
      </p>
      <div className="h-32 w-48">
        <BarVisualizer state={state} barCount={5} track={track} />
      </div>
      <p className="text-sm text-zinc-400 capitalize">{state}</p>
    </div>
  );
}

function AgentVisualizer() {
  const { state, audioTrack } = useVoiceAssistant();
  const displayState = state === "thinking" ? "generating" : state;

  return (
    <div className="flex flex-col items-center gap-4">
      <p className="text-xs font-medium tracking-wide text-zinc-500 uppercase">
        Assistant
      </p>
      <div className="h-32 w-48">
        <BarVisualizer state={state} barCount={5} track={audioTrack} />
      </div>
      <p className="text-sm text-zinc-400 capitalize">{displayState}</p>
    </div>
  );
}

type VadMode = "client" | "semantic";

export default function VoiceAssistant() {
  const [connectionDetails, setConnectionDetails] =
    useState<ConnectionDetails | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [vadMode, setVadMode] = useState<VadMode>("client");

  const handleConnect = useCallback(async () => {
    setConnecting(true);
    try {
      const response = await fetch("/api/token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ vad_mode: vadMode }),
      });
      if (!response.ok) throw new Error("Failed to get token");
      const details: ConnectionDetails = await response.json();
      setConnectionDetails(details);
    } catch (err) {
      console.error("Connection failed:", err);
      setConnecting(false);
    }
  }, [vadMode]);

  const handleDisconnected = useCallback(() => {
    setConnectionDetails(null);
    setConnecting(false);
  }, []);

  if (!connectionDetails) {
    return (
      <div className="flex flex-col items-center gap-6">
        <div className="flex items-center gap-3">
          <span className="text-sm text-zinc-400">VAD</span>
          <button
            onClick={() => setVadMode(vadMode === "client" ? "semantic" : "client")}
            disabled={connecting}
            className="relative inline-flex h-8 w-40 items-center rounded-full border border-zinc-700 bg-zinc-900 transition-colors disabled:opacity-50"
          >
            <span
              className={`absolute h-7 w-[calc(50%-2px)] rounded-full bg-zinc-700 transition-transform ${
                vadMode === "semantic" ? "translate-x-[calc(100%+2px)]" : "translate-x-[1px]"
              }`}
            />
            <span
              className={`relative z-10 flex-1 text-center text-xs font-medium ${
                vadMode === "client" ? "text-white" : "text-zinc-500"
              }`}
            >
              Client
            </span>
            <span
              className={`relative z-10 flex-1 text-center text-xs font-medium ${
                vadMode === "semantic" ? "text-white" : "text-zinc-500"
              }`}
            >
              Semantic
            </span>
          </button>
        </div>
        <button
          onClick={handleConnect}
          disabled={connecting}
          className="rounded-full bg-white px-8 py-4 text-lg font-medium text-black transition-opacity hover:opacity-80 disabled:opacity-50"
        >
          {connecting ? "Connecting..." : "Start Conversation"}
        </button>
      </div>
    );
  }

  return (
    <LiveKitRoom
      token={connectionDetails.participantToken}
      serverUrl={connectionDetails.serverUrl}
      connect={true}
      audio={true}
      onDisconnected={handleDisconnected}
      className="flex flex-col items-center gap-8"
    >
      <div className="flex items-start justify-center gap-16">
        <UserMicIndicator />
        <AgentVisualizer />
      </div>
      <RoomAudioRenderer />
      <DisconnectButton className="rounded-full border border-zinc-700 px-6 py-3 text-sm text-zinc-300 transition-colors hover:border-red-500 hover:text-red-400">
        End Conversation
      </DisconnectButton>
    </LiveKitRoom>
  );
}
