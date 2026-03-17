"use client";

import { useEffect, useCallback, useRef } from "react";
import { Socket } from "socket.io-client";
import { getSocket, connectSocket, disconnectSocket } from "@/lib/socket";
import { useAuthStore } from "@/stores/auth-store";

export function useSocket() {
  const socketRef = useRef<Socket | null>(null);
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) {
      connectSocket();
      socketRef.current = getSocket();
    }

    return () => {
      // Don't disconnect on unmount, just clean ref
    };
  }, [isAuthenticated]);

  const disconnect = useCallback(() => {
    disconnectSocket();
    socketRef.current = null;
  }, []);

  const emit = useCallback((event: string, data?: unknown) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit(event, data);
    }
  }, []);

  const on = useCallback((event: string, handler: (...args: unknown[]) => void) => {
    const socket = getSocket();
    socket.on(event, handler);
    return () => {
      socket.off(event, handler);
    };
  }, []);

  const off = useCallback((event: string, handler?: (...args: unknown[]) => void) => {
    const socket = getSocket();
    socket.off(event, handler);
  }, []);

  return {
    socket: socketRef.current,
    isConnected: socketRef.current?.connected || false,
    emit,
    on,
    off,
    disconnect,
  };
}
