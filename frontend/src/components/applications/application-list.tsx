"use client";

import { Application } from "@/types/application";
import { ApplicationCard } from "./application-card";
import { EmptyState } from "@/components/common/empty-state";
import { FileText } from "lucide-react";

interface ApplicationListProps {
  applications: Application[];
}

export function ApplicationList({ applications }: ApplicationListProps) {
  if (applications.length === 0) {
    return (
      <EmptyState
        icon={FileText}
        title="No applications found"
        description="Start the AI Agent or apply manually to see your applications here."
      />
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {applications.map((app) => (
        <ApplicationCard key={app.id} application={app} />
      ))}
    </div>
  );
}
