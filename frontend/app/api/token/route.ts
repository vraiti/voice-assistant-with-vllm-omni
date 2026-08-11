import { AccessToken, RoomAgentDispatch, RoomConfiguration } from "livekit-server-sdk";
import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const apiKey = process.env.LIVEKIT_API_KEY;
  const apiSecret = process.env.LIVEKIT_API_SECRET;
  const serverUrl = process.env.LIVEKIT_URL;

  if (!apiKey || !apiSecret || !serverUrl) {
    return NextResponse.json(
      { error: "LiveKit credentials not configured" },
      { status: 500 }
    );
  }

  let vadMode = "client";
  try {
    const body = await req.json();
    if (body.vad_mode === "semantic" || body.vad_mode === "client") {
      vadMode = body.vad_mode;
    }
  } catch {
    // no body or invalid JSON — use default
  }

  const roomName = `voice-room-${Math.random().toString(36).slice(2, 9)}`;
  const participantName = `user-${Math.random().toString(36).slice(2, 7)}`;

  const at = new AccessToken(apiKey, apiSecret, {
    identity: participantName,
    name: participantName,
  });

  at.addGrant({
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canSubscribe: true,
  });

  at.roomConfig = new RoomConfiguration({
    agents: [new RoomAgentDispatch({ agentName: "voice-assistant" })],
    metadata: JSON.stringify({ vad_mode: vadMode }),
  });

  const token = await at.toJwt();

  return NextResponse.json({
    serverUrl,
    roomName,
    participantName,
    participantToken: token,
  });
}
