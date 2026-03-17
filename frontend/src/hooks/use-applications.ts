"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { Application, ApplicationFilters } from "@/types/application";
import { PaginatedResponse } from "@/types/api";

export function useApplications(filters?: ApplicationFilters) {
  return useQuery({
    queryKey: ["applications", filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status?.length) params.set("status", filters.status.join(","));
      if (filters?.applied_via) params.set("source", filters.applied_via);
      if (filters?.search) params.set("company", filters.search);
      if (filters?.sort_by) params.set("sort_by", filters.sort_by);
      if (filters?.sort_order) params.set("sort_order", filters.sort_order);
      if (filters?.page) params.set("page", filters.page.toString());
      if (filters?.per_page) params.set("page_size", filters.per_page.toString());

      const response = await api.get<PaginatedResponse<Application>>(
        `/applications?${params.toString()}`
      );
      return response.data;
    },
  });
}

export function useApplication(id: string) {
  return useQuery({
    queryKey: ["application", id],
    queryFn: async () => {
      const response = await api.get<Application>(`/applications/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useUpdateApplication() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Application> }) => {
      const response = await api.patch<Application>(`/applications/${id}`, data);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      queryClient.setQueryData(["application", data.id], data);
    },
  });
}

export function useWithdrawApplication() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post(`/applications/${id}/withdraw`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
  });
}

export function useRecentApplications(limit: number = 5) {
  return useQuery({
    queryKey: ["applications", "recent", limit],
    queryFn: async () => {
      const response = await api.get<{ items: Application[] }>(
        `/applications/?page=1&page_size=${limit}&sort_by=created_at&sort_order=desc`
      );
      return response.data.items;
    },
  });
}
