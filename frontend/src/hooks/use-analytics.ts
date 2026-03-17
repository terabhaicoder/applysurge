"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { AnalyticsData } from "@/types/api";

export function useAnalytics(period: string = "30d") {
  const days = period === "7d" ? 7 : period === "30d" ? 30 : 90;
  return useQuery({
    queryKey: ["analytics", period],
    queryFn: async () => {
      const response = await api.get<AnalyticsData>(`/analytics/daily?days=${days}`);
      return response.data;
    },
  });
}

export function useAnalyticsOverview() {
  return useQuery({
    queryKey: ["analytics", "overview"],
    queryFn: async () => {
      const response = await api.get("/analytics/overview");
      return response.data;
    },
  });
}
