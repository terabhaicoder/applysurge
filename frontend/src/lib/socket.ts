import { io, Socket } from "socket.io-client";
import { getTokens } from "./auth";

const SOCKET_URL = process.env.NEXT_PUBLIC_SOCKET_URL || "http://localhost:8000";

let socket: Socket | null = null;

export function getSocket(): Socket {
  if (!socket) {
    const tokens = getTokens();

    socket = io(SOCKET_URL, {
      autoConnect: false,
      auth: {
        token: tokens?.access_token,
      },
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
    });
  }

  return socket;
}

export function connectSocket(): void {
  const s = getSocket();
  if (!s.connected) {
    const tokens = getTokens();
    if (tokens?.access_token) {
      s.auth = { token: tokens.access_token };
      s.connect();
    }
  }
}

export function disconnectSocket(): void {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
}

export function updateSocketAuth(): void {
  if (socket) {
    const tokens = getTokens();
    socket.auth = { token: tokens?.access_token };
    if (socket.connected) {
      socket.disconnect();
      socket.connect();
    }
  }
}
