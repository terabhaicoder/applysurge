"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Separator } from "@/components/ui/separator";
import { api } from "@/lib/api";
import { useToast } from "@/providers/toast-provider";
import { Loader2 } from "lucide-react";

interface AgentSettings {
  max_applications_per_day: number;
  cooldown_seconds: number;
  auto_apply: boolean;
  cover_letter_enabled: boolean;
  preferred_apply_time_start: string | null;
  preferred_apply_time_end: string | null;
  skip_easy_apply: boolean;
  require_salary_info: boolean;
}

const defaultSettings: AgentSettings = {
  max_applications_per_day: 50,
  cooldown_seconds: 30,
  auto_apply: true,
  cover_letter_enabled: true,
  preferred_apply_time_start: "09:00",
  preferred_apply_time_end: "18:00",
  skip_easy_apply: false,
  require_salary_info: false,
};

const SPEED_PRESETS: Record<string, { label: string; value: number }> = {
  slow: { label: "Slow (90s between apps)", value: 90 },
  normal: { label: "Normal (30s between apps)", value: 30 },
  fast: { label: "Fast (15s between apps)", value: 15 },
};

function getCooldownPreset(seconds: number): string {
  if (seconds >= 60) return "slow";
  if (seconds >= 20) return "normal";
  return "fast";
}

export function AgentSettingsForm() {
  const { addToast } = useToast();
  const queryClient = useQueryClient();
  const [settings, setSettings] = useState<AgentSettings>(defaultSettings);

  const { data: savedSettings, isLoading } = useQuery({
    queryKey: ["agent-settings"],
    queryFn: () => api.get("/agent/settings").then((r) => r.data),
  });

  useEffect(() => {
    if (savedSettings) {
      setSettings({
        max_applications_per_day: savedSettings.max_applications_per_day ?? defaultSettings.max_applications_per_day,
        cooldown_seconds: savedSettings.cooldown_seconds ?? defaultSettings.cooldown_seconds,
        auto_apply: savedSettings.auto_apply ?? defaultSettings.auto_apply,
        cover_letter_enabled: savedSettings.cover_letter_enabled ?? defaultSettings.cover_letter_enabled,
        preferred_apply_time_start: savedSettings.preferred_apply_time_start ?? defaultSettings.preferred_apply_time_start,
        preferred_apply_time_end: savedSettings.preferred_apply_time_end ?? defaultSettings.preferred_apply_time_end,
        skip_easy_apply: savedSettings.skip_easy_apply ?? defaultSettings.skip_easy_apply,
        require_salary_info: savedSettings.require_salary_info ?? defaultSettings.require_salary_info,
      });
    }
  }, [savedSettings]);

  const saveMutation = useMutation({
    mutationFn: (data: Partial<AgentSettings>) => api.put("/agent/settings", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agent-settings"] });
      addToast({ title: "Agent settings saved", variant: "success" });
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || "Failed to save settings";
      addToast({ title: message, variant: "error" });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    saveMutation.mutate(settings);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="max-w-2xl space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Application Limits</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Daily Application Limit</Label>
            <div className="flex items-center gap-4">
              <Slider
                value={[settings.max_applications_per_day]}
                onValueChange={([value]) => setSettings((prev) => ({ ...prev, max_applications_per_day: value }))}
                max={200}
                step={5}
                className="flex-1"
              />
              <span className="text-sm font-semibold text-foreground w-12">{settings.max_applications_per_day}</span>
            </div>
            <p className="text-xs text-muted-foreground">Maximum number of applications per day</p>
          </div>

          <div className="space-y-2">
            <Label>Application Speed</Label>
            <div className="flex gap-2">
              {Object.entries(SPEED_PRESETS).map(([key, preset]) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => setSettings((prev) => ({ ...prev, cooldown_seconds: preset.value }))}
                  className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors ${
                    getCooldownPreset(settings.cooldown_seconds) === key
                      ? "bg-primary text-primary-foreground border-primary"
                      : "bg-secondary text-foreground border-border hover:bg-secondary/80"
                  }`}
                >
                  {preset.label}
                </button>
              ))}
            </div>
            <p className="text-xs text-muted-foreground">
              Cooldown: {settings.cooldown_seconds}s between applications
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Behavior</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label>Auto Apply</Label>
              <p className="text-xs text-muted-foreground mt-0.5">Automatically submit applications without confirmation</p>
            </div>
            <Switch
              checked={settings.auto_apply}
              onCheckedChange={(checked) => setSettings((prev) => ({ ...prev, auto_apply: checked }))}
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <Label>AI Cover Letters</Label>
              <p className="text-xs text-muted-foreground mt-0.5">Generate AI cover letters tailored to each job</p>
            </div>
            <Switch
              checked={settings.cover_letter_enabled}
              onCheckedChange={(checked) => setSettings((prev) => ({ ...prev, cover_letter_enabled: checked }))}
            />
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div>
              <Label>Skip Easy Apply</Label>
              <p className="text-xs text-muted-foreground mt-0.5">Skip LinkedIn Easy Apply jobs</p>
            </div>
            <Switch
              checked={settings.skip_easy_apply}
              onCheckedChange={(checked) => setSettings((prev) => ({ ...prev, skip_easy_apply: checked }))}
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <Label>Require Salary Info</Label>
              <p className="text-xs text-muted-foreground mt-0.5">Only apply to jobs that list salary information</p>
            </div>
            <Switch
              checked={settings.require_salary_info}
              onCheckedChange={(checked) => setSettings((prev) => ({ ...prev, require_salary_info: checked }))}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Working Hours</CardTitle>
          <CardDescription>Restrict agent activity to specific hours</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Start Time</Label>
              <Input
                type="time"
                value={settings.preferred_apply_time_start || ""}
                onChange={(e) => setSettings((prev) => ({ ...prev, preferred_apply_time_start: e.target.value || null }))}
              />
            </div>
            <div className="space-y-2">
              <Label>End Time</Label>
              <Input
                type="time"
                value={settings.preferred_apply_time_end || ""}
                onChange={(e) => setSettings((prev) => ({ ...prev, preferred_apply_time_end: e.target.value || null }))}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Button type="submit" disabled={saveMutation.isPending}>
        {saveMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
        Save Agent Settings
      </Button>
    </form>
  );
}
