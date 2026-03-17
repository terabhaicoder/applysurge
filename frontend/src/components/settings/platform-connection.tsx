"use client";

import { CheckCircle2, AlertCircle, Link2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PlatformConnection as PlatformConnectionType } from "@/types/api";

interface PlatformConnectionProps {
  platform: PlatformConnectionType;
  onConnect: () => void;
  onDisconnect: () => void;
}

const platformIcons: Record<string, { name: string; color: string }> = {
  linkedin: { name: "LinkedIn", color: "bg-blue-600" },
  naukri: { name: "Naukri", color: "bg-indigo-600" },
  indeed: { name: "Indeed", color: "bg-purple-600" },
};

export function PlatformConnection({ platform, onConnect, onDisconnect }: PlatformConnectionProps) {
  const config = platformIcons[platform.platform] || { name: platform.platform, color: "bg-muted-foreground" };

  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 ${config.color} rounded-lg flex items-center justify-center`}>
              <Link2 className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-foreground">{config.name}</h3>
              {platform.is_connected ? (
                <div className="flex items-center gap-1 mt-0.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
                  <span className="text-xs text-green-600">Connected as {platform.username}</span>
                </div>
              ) : (
                <span className="text-xs text-muted-foreground">Not connected</span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {platform.status === "error" && (
              <Badge variant="destructive" className="text-xs">Error</Badge>
            )}
            {platform.status === "expired" && (
              <Badge variant="warning" className="text-xs">Expired</Badge>
            )}
            {platform.is_connected ? (
              <Button variant="outline" size="sm" onClick={onDisconnect}>
                Disconnect
              </Button>
            ) : (
              <Button size="sm" onClick={onConnect}>
                Connect
              </Button>
            )}
          </div>
        </div>
        {platform.last_sync && (
          <p className="text-xs text-muted-foreground mt-2">Last synced: {platform.last_sync}</p>
        )}
      </CardContent>
    </Card>
  );
}
