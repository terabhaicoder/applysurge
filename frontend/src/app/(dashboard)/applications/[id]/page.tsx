"use client";

import { useParams } from "next/navigation";
import { useApplication } from "@/hooks/use-applications";
import { ApplicationDetails } from "@/components/applications/application-details";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function ApplicationDetailPage() {
  const params = useParams();
  const { data: application, isLoading, error } = useApplication(params.id as string);

  return (
    <div>
      <div className="mb-6">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/applications" className="gap-2">
            <ArrowLeft className="w-4 h-4" />
            Back to Applications
          </Link>
        </Button>
      </div>

      {isLoading && <LoadingState type="detail" />}
      {error && <ErrorState message="Failed to load application details" />}
      {application && <ApplicationDetails application={application} />}
    </div>
  );
}
