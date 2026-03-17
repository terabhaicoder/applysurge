"use client";

import { useParams } from "next/navigation";
import { useJob } from "@/hooks/use-jobs";
import { JobDetails } from "@/components/jobs/job-details";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function JobDetailPage() {
  const params = useParams();
  const { data: job, isLoading, error } = useJob(params.id as string);

  return (
    <div>
      <div className="mb-6">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/jobs" className="gap-2">
            <ArrowLeft className="w-4 h-4" />
            Back to Jobs
          </Link>
        </Button>
      </div>

      {isLoading && <LoadingState type="detail" />}
      {error && <ErrorState message="Failed to load job details" />}
      {job && <JobDetails job={job} />}
    </div>
  );
}
