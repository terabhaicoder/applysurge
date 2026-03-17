"use client";

import { useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { useAgentStore } from "@/stores/agent-store";
import { useToast } from "@/providers/toast-provider";
import { AgentStatus, AgentSettings } from "@/types/agent";

export function useAgent() {
  const queryClient = useQueryClient();
  const { setStatus, setQueue } = useAgentStore();
  const { addToast } = useToast();

  const statusQuery = useQuery({
    queryKey: ["agent-status"],
    queryFn: async () => {
      const response = await api.get<AgentStatus>("/agent/status");
      setStatus(response.data);
      return response.data;
    },
    refetchInterval: 5000,
  });

  const queueQuery = useQuery({
    queryKey: ["agent-queue"],
    queryFn: async () => {
      const response = await api.get("/jobs/queue");
      setQueue(response.data);
      return response.data;
    },
    refetchInterval: 10000,
  });

  const startMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post<AgentStatus>("/agent/start");
      return response.data;
    },
    onSuccess: (data) => {
      setStatus(data);
      queryClient.invalidateQueries({ queryKey: ["agent-status"] });
    },
    onError: (error: any) => {
      const statusCode = error?.response?.status;
      const message =
        error?.response?.data?.message || error?.response?.data?.detail || "Failed to start the agent";
      if (statusCode === 429) {
        addToast({
          title: "Application Limit Reached",
          description: message,
          variant: "error",
        });
      } else if (statusCode === 403) {
        addToast({
          title: "Subscription required",
          description: message,
          variant: "error",
        });
      } else {
        addToast({ title: message, variant: "error" });
      }
    },
  });

  const stopMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post<AgentStatus>("/agent/stop");
      return response.data;
    },
    onSuccess: (data) => {
      setStatus(data);
      queryClient.invalidateQueries({ queryKey: ["agent-status"] });
    },
  });

  const pauseMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post<AgentStatus>("/agent/pause");
      return response.data;
    },
    onSuccess: (data) => {
      setStatus(data);
      queryClient.invalidateQueries({ queryKey: ["agent-status"] });
    },
  });

  const resumeMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post<AgentStatus>("/agent/resume");
      return response.data;
    },
    onSuccess: (data) => {
      setStatus(data);
      queryClient.invalidateQueries({ queryKey: ["agent-status"] });
    },
  });

  const unqueueMutation = useMutation({
    mutationFn: async (jobId: string) => {
      const response = await api.delete(`/jobs/${jobId}/queue`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agent-queue"] });
      queryClient.invalidateQueries({ queryKey: ["agent-status"] });
      addToast({ title: "Job removed from queue", variant: "success" });
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || "Failed to remove from queue";
      addToast({ title: message, variant: "error" });
    },
  });

  const updateSettings = useMutation({
    mutationFn: async (settings: Partial<AgentSettings>) => {
      const response = await api.put("/agent/settings", settings);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agent-settings"] });
    },
  });

  const settingsQuery = useQuery({
    queryKey: ["agent-settings"],
    queryFn: async () => {
      const response = await api.get<AgentSettings>("/agent/settings");
      return response.data;
    },
  });

  const start = useCallback(() => startMutation.mutate(), [startMutation]);
  const stop = useCallback(() => stopMutation.mutate(), [stopMutation]);
  const pause = useCallback(() => pauseMutation.mutate(), [pauseMutation]);
  const resume = useCallback(() => resumeMutation.mutate(), [resumeMutation]);
  const unqueue = useCallback(
    (jobId: string) => unqueueMutation.mutate(jobId),
    [unqueueMutation]
  );

  return {
    status: statusQuery.data,
    queue: queueQuery.data,
    settings: settingsQuery.data,
    isLoading: statusQuery.isLoading,
    start,
    stop,
    pause,
    resume,
    unqueue,
    updateSettings: updateSettings.mutate,
    isStarting: startMutation.isPending,
    isStopping: stopMutation.isPending,
    isPausing: pauseMutation.isPending,
  };
}
