"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { Job, JobFilters } from "@/types/job";
import { PaginatedResponse } from "@/types/api";

export function useJobs(filters?: JobFilters) {
  return useQuery({
    queryKey: ["jobs", filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.search) params.set("search", filters.search);
      if (filters?.job_type?.length) params.set("job_type", filters.job_type.join(","));
      if (filters?.experience_level?.length) params.set("experience_level", filters.experience_level.join(","));
      if (filters?.location) params.set("location", filters.location);
      if (filters?.salary_min) params.set("salary_min", filters.salary_min.toString());
      if (filters?.salary_max) params.set("salary_max", filters.salary_max.toString());
      if (filters?.source?.length) params.set("source", filters.source.join(","));
      if (filters?.min_match_score) params.set("min_match_score", filters.min_match_score.toString());
      if (filters?.sort_by) params.set("sort_by", filters.sort_by);
      if (filters?.sort_order) params.set("sort_order", filters.sort_order);
      if (filters?.page) params.set("page", filters.page.toString());
      if (filters?.per_page) params.set("page_size", filters.per_page.toString());

      const response = await api.get<PaginatedResponse<Job>>(
        `/jobs?${params.toString()}`
      );
      return response.data;
    },
  });
}

export function useJob(id: string) {
  return useQuery({
    queryKey: ["job", id],
    queryFn: async () => {
      const response = await api.get<Job>(`/jobs/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useRecommendedJobs(limit: number = 10) {
  return useQuery({
    queryKey: ["jobs", "recommended", limit],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Job>>(
        `/jobs/?page=1&page_size=${limit}&sort_by=match_score&sort_order=desc`
      );
      return response.data.items;
    },
  });
}
