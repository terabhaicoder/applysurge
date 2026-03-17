"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { api } from "@/lib/api";
import { useToast } from "@/providers/toast-provider";
import { Loader2 } from "lucide-react";

interface EmailSettings {
  from_name: string;
  from_email: string;
  provider: string;
  smtp_host: string;
  smtp_port: number;
  smtp_username: string;
  smtp_password: string;
}

const defaultSettings: EmailSettings = {
  from_name: "",
  from_email: "",
  provider: "gmail",
  smtp_host: "",
  smtp_port: 587,
  smtp_username: "",
  smtp_password: "",
};

export function EmailSettingsForm() {
  const { addToast } = useToast();
  const queryClient = useQueryClient();
  const [useGmail, setUseGmail] = useState(true);
  const [settings, setSettings] = useState<EmailSettings>(defaultSettings);

  const { data: savedSettings, isLoading } = useQuery({
    queryKey: ["email-settings"],
    queryFn: () => api.get("/email/settings").then((r) => r.data),
  });

  useEffect(() => {
    if (savedSettings) {
      setSettings({
        from_name: savedSettings.from_name || "",
        from_email: savedSettings.email_address || savedSettings.from_email || "",
        provider: savedSettings.provider || "gmail",
        smtp_host: savedSettings.smtp_host || "",
        smtp_port: savedSettings.smtp_port || 587,
        smtp_username: savedSettings.smtp_username || "",
        smtp_password: "",
      });
      setUseGmail(savedSettings.provider === "gmail" || !savedSettings.provider);
    }
  }, [savedSettings]);

  const saveMutation = useMutation({
    mutationFn: () => api.put("/email/settings", {
      from_name: settings.from_name,
      email_address: settings.from_email,
      provider: useGmail ? "gmail" : "smtp",
      smtp_host: useGmail ? "smtp.gmail.com" : settings.smtp_host,
      smtp_port: useGmail ? 587 : settings.smtp_port,
      smtp_username: useGmail ? settings.from_email : settings.smtp_username,
      smtp_password: settings.smtp_password || undefined,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["email-settings"] });
      addToast({ title: "Email settings saved", variant: "success" });
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || "Failed to save settings";
      addToast({ title: message, variant: "error" });
    },
  });

  const testMutation = useMutation({
    mutationFn: () => api.post("/email/settings/test", {
      to_email: settings.from_email,
      subject: "Apply Surge - Test Email",
    }),
    onSuccess: () => {
      addToast({ title: "Test email sent!", variant: "success" });
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || "Failed to send test email";
      addToast({ title: message, variant: "error" });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    saveMutation.mutate();
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
          <CardTitle className="text-lg">Sender Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="from_name">From Name</Label>
            <Input
              id="from_name"
              placeholder="Your full name"
              value={settings.from_name}
              onChange={(e) => setSettings((prev) => ({ ...prev, from_name: e.target.value }))}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="from_email">From Email</Label>
            <Input
              id="from_email"
              type="email"
              placeholder="you@gmail.com"
              value={settings.from_email}
              onChange={(e) => setSettings((prev) => ({ ...prev, from_email: e.target.value }))}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Email Provider</CardTitle>
          <CardDescription>Choose how to send emails</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label>Use Gmail</Label>
              <p className="text-xs text-muted-foreground mt-0.5">Send via Gmail with App Password</p>
            </div>
            <Switch checked={useGmail} onCheckedChange={setUseGmail} />
          </div>

          <Separator />

          {useGmail ? (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="gmail_app_password">Gmail App Password</Label>
                <Input
                  id="gmail_app_password"
                  type="password"
                  placeholder="xxxx xxxx xxxx xxxx"
                  value={settings.smtp_password}
                  onChange={(e) => setSettings((prev) => ({ ...prev, smtp_password: e.target.value }))}
                />
                <p className="text-xs text-muted-foreground">
                  Generate at: Google Account &gt; Security &gt; App Passwords
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="smtp_host">SMTP Host</Label>
                  <Input
                    id="smtp_host"
                    placeholder="smtp.example.com"
                    value={settings.smtp_host}
                    onChange={(e) => setSettings((prev) => ({ ...prev, smtp_host: e.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="smtp_port">SMTP Port</Label>
                  <Input
                    id="smtp_port"
                    type="number"
                    placeholder="587"
                    value={settings.smtp_port}
                    onChange={(e) => setSettings((prev) => ({ ...prev, smtp_port: parseInt(e.target.value) || 587 }))}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="smtp_username">SMTP Username</Label>
                <Input
                  id="smtp_username"
                  placeholder="username"
                  value={settings.smtp_username}
                  onChange={(e) => setSettings((prev) => ({ ...prev, smtp_username: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="smtp_password">SMTP Password</Label>
                <Input
                  id="smtp_password"
                  type="password"
                  placeholder="password"
                  value={settings.smtp_password}
                  onChange={(e) => setSettings((prev) => ({ ...prev, smtp_password: e.target.value }))}
                />
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex gap-3">
        <Button type="submit" disabled={saveMutation.isPending}>
          {saveMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
          Save Settings
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={() => testMutation.mutate()}
          disabled={testMutation.isPending || !settings.from_email}
        >
          {testMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
          Send Test Email
        </Button>
      </div>
    </form>
  );
}
