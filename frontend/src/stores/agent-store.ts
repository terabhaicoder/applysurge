import { create } from "zustand";
import { AgentStatus, AgentLog, QueueItem } from "@/types/agent";

interface AgentState {
  status: AgentStatus;
  logs: AgentLog[];
  queue: QueueItem[];
  liveScreenshot: string | null;
  setStatus: (status: AgentStatus) => void;
  addLog: (log: AgentLog) => void;
  setLogs: (logs: AgentLog[]) => void;
  setQueue: (queue: QueueItem[]) => void;
  setLiveScreenshot: (screenshot: string | null) => void;
  clearLogs: () => void;
}

const initialStatus: AgentStatus = {
  is_running: false,
  is_paused: false,
  status: "idle",
  applications_made_today: 0,
  applications_limit_today: 50,
  applications_total: 0,
  applications_limit_total: 10,
  errors_count: 0,
  queue_size: 0,
};

export const useAgentStore = create<AgentState>((set) => ({
  status: initialStatus,
  logs: [],
  queue: [],
  liveScreenshot: null,
  setStatus: (status) => set({ status }),
  addLog: (log) => set((state) => ({ logs: [log, ...state.logs].slice(0, 100) })),
  setLogs: (logs) => set({ logs }),
  setQueue: (queue) => set({ queue }),
  setLiveScreenshot: (liveScreenshot) => set({ liveScreenshot }),
  clearLogs: () => set({ logs: [] }),
}));
