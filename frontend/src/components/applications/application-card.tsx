"use client";

import Link from "next/link";
import { Building2, Bot, User } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { StatusBadge } from "./status-badge";
import { Application } from "@/types/application";
import { formatRelativeDate } from "@/lib/utils";

interface ApplicationCardProps {
  application: Application;
}

export function ApplicationCard({ application }: ApplicationCardProps) {
  return (
    <Link href={`/applications/${application.id}`}>
      <Card className="hover:shadow-md transition-shadow cursor-pointer">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-secondary rounded-lg flex items-center justify-center">
                <Building2 className="w-5 h-5 text-muted-foreground" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-foreground">{application.job?.title}</h3>
                <p className="text-xs text-muted-foreground">{application.job?.company}</p>
              </div>
            </div>
            <StatusBadge status={application.status} />
          </div>
          <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              {application.applied_via === "agent" ? (
                <><Bot className="w-3.5 h-3.5" /> AI Agent</>
              ) : (
                <><User className="w-3.5 h-3.5" /> Manual</>
              )}
            </div>
            <span>{formatRelativeDate(application.created_at)}</span>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
