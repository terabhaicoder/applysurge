"use client";

import { Job } from "@/types/job";
import { JobCard } from "./job-card";
import { EmptyState } from "@/components/common/empty-state";
import { Briefcase } from "lucide-react";

interface JobListProps {
  jobs: Job[];
}

export function JobList({ jobs }: JobListProps) {
  if (jobs.length === 0) {
    return (
      <EmptyState
        icon={Briefcase}
        title="No jobs found"
        description="Try adjusting your filters or check back later for new listings."
      />
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {jobs.map((job) => (
        <JobCard key={job.id} job={job} />
      ))}
    </div>
  );
}
