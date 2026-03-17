"use client";

import { Building2, MapPin, Bot, User, ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "./status-badge";
import { ApplicationTimeline } from "./application-timeline";
import { Application } from "@/types/application";
import { formatDate } from "@/lib/utils";

interface ApplicationDetailsProps {
  application: Application;
}

export function ApplicationDetails({ application }: ApplicationDetailsProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 space-y-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-secondary rounded-xl flex items-center justify-center">
                  <Building2 className="w-6 h-6 text-muted-foreground" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-foreground">{application.job?.title}</h1>
                  <p className="text-muted-foreground">{application.job?.company}</p>
                  <div className="mt-2 flex items-center gap-3 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1"><MapPin className="w-4 h-4" />{application.job?.location}</span>
                    <span className="flex items-center gap-1">
                      {application.applied_via === "agent" ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
                      {application.applied_via === "agent" ? "AI Agent" : "Manual"}
                    </span>
                  </div>
                </div>
              </div>
              <StatusBadge status={application.status} />
            </div>

            <div className="mt-6 flex gap-3">
              <Button variant="outline" size="sm" className="gap-2">
                <ExternalLink className="w-4 h-4" />
                View Job Posting
              </Button>
              {application.status !== "withdrawn" && (
                <Button variant="outline" size="sm" className="text-red-600 hover:text-red-700 hover:bg-red-50">
                  Withdraw
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Activity Timeline</CardTitle>
          </CardHeader>
          <CardContent>
            <ApplicationTimeline logs={application.logs} />
          </CardContent>
        </Card>

        {application.screenshots.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Screenshots</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                {application.screenshots.map((ss) => (
                  <div key={ss.id} className="border rounded-lg overflow-hidden">
                    <img src={ss.url} alt={ss.step} className="w-full h-32 object-cover" />
                    <div className="p-2 bg-secondary">
                      <p className="text-xs text-muted-foreground">{ss.step}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <p className="text-xs text-muted-foreground uppercase font-medium">Applied On</p>
              <p className="text-sm text-foreground">{formatDate(application.created_at, "MMMM d, yyyy")}</p>
            </div>
            {application.match_score && (
              <div>
                <p className="text-xs text-muted-foreground uppercase font-medium">Match Score</p>
                <p className="text-sm text-foreground">{application.match_score}%</p>
              </div>
            )}
            {application.response_date && (
              <div>
                <p className="text-xs text-muted-foreground uppercase font-medium">Response Date</p>
                <p className="text-sm text-foreground">{formatDate(application.response_date)}</p>
              </div>
            )}
            {application.interview_date && (
              <div>
                <p className="text-xs text-muted-foreground uppercase font-medium">Interview Date</p>
                <p className="text-sm text-foreground">{formatDate(application.interview_date)}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {application.notes && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Notes</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-foreground whitespace-pre-wrap">{application.notes}</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
