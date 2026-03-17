'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Save, Mail, Bell, Loader2 } from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { api } from '@/lib/api';
import { useToast } from '@/providers/toast-provider';

interface NotificationSettings {
  email_on_response: boolean;
  email_on_interview: boolean;
  email_on_offer: boolean;
  email_daily_summary: boolean;
  push_on_agent_error: boolean;
  push_on_application: boolean;
}

const defaultSettings: NotificationSettings = {
  email_on_response: true,
  email_on_interview: true,
  email_on_offer: true,
  email_daily_summary: true,
  push_on_agent_error: true,
  push_on_application: false,
};

export default function NotificationsSettingsPage() {
  const { addToast } = useToast();
  const queryClient = useQueryClient();
  const [settings, setSettings] = useState<NotificationSettings>(defaultSettings);

  const { data: agentSettings, isLoading } = useQuery({
    queryKey: ['agent-settings'],
    queryFn: () => api.get('/agent/settings').then((r) => r.data),
  });

  useEffect(() => {
    if (agentSettings) {
      setSettings({
        email_on_response: agentSettings.notify_on_response ?? true,
        email_on_interview: agentSettings.notify_on_interview ?? true,
        email_on_offer: agentSettings.notify_on_response ?? true,
        email_daily_summary: agentSettings.notify_daily_summary ?? true,
        push_on_agent_error: agentSettings.notify_on_application ?? true,
        push_on_application: agentSettings.notify_on_application ?? false,
      });
    }
  }, [agentSettings]);

  const saveMutation = useMutation({
    mutationFn: () => api.put('/agent/settings', {
      notify_on_response: settings.email_on_response,
      notify_on_interview: settings.email_on_interview,
      notify_daily_summary: settings.email_daily_summary,
      notify_on_application: settings.push_on_application,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-settings'] });
      addToast({ title: 'Notification settings saved', variant: 'success' });
    },
    onError: () => {
      addToast({ title: 'Failed to save settings', variant: 'error' });
    },
  });

  const toggle = (key: keyof NotificationSettings) => {
    setSettings((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const Switch = ({ checked, onChange }: { checked: boolean; onChange: () => void }) => (
    <button
      onClick={onChange}
      className={cn(
        'relative w-11 h-6 rounded-full transition-colors',
        checked ? 'bg-primary' : 'bg-secondary'
      )}
    >
      <span
        className={cn(
          'absolute top-1 left-1 w-4 h-4 bg-white rounded-full shadow transition-transform',
          checked && 'translate-x-5'
        )}
      />
    </button>
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Link
            href="/settings"
            className="p-2 rounded-xl hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-foreground tracking-tight">Notifications</h1>
            <p className="text-muted-foreground text-sm mt-1">Choose how you want to be notified</p>
          </div>
        </div>
        <button
          onClick={() => saveMutation.mutate()}
          disabled={saveMutation.isPending}
          className="px-5 py-2.5 bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-medium rounded-xl flex items-center gap-2 transition-all shadow-lg shadow-primary/20 hover:shadow-primary/30"
        >
          {saveMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          Save Changes
        </button>
      </div>

      {/* Email Notifications */}
      <div className="bg-card rounded-2xl border border-border/50 overflow-hidden">
        <div className="p-5 border-b border-border/50">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-blue-400/10 flex items-center justify-center">
              <Mail className="w-4 h-4 text-blue-400" />
            </div>
            <div>
              <h2 className="font-semibold text-foreground">Email Notifications</h2>
              <p className="text-xs text-muted-foreground">Receive email alerts for important events</p>
            </div>
          </div>
        </div>
        <div className="divide-y divide-border/50">
          {[
            { key: 'email_on_response', label: 'Response received', desc: 'When an employer responds to your application' },
            { key: 'email_on_interview', label: 'Interview scheduled', desc: 'When an interview is scheduled' },
            { key: 'email_on_offer', label: 'Offer received', desc: 'When you receive a job offer' },
            { key: 'email_daily_summary', label: 'Daily summary', desc: 'Daily digest of your job search activity' },
          ].map((item) => (
            <div key={item.key} className="flex items-center justify-between p-4 hover:bg-secondary/30 transition-colors">
              <div>
                <p className="text-sm font-medium text-foreground">{item.label}</p>
                <p className="text-xs text-muted-foreground">{item.desc}</p>
              </div>
              <Switch
                checked={settings[item.key as keyof NotificationSettings]}
                onChange={() => toggle(item.key as keyof NotificationSettings)}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Push Notifications */}
      <div className="bg-card rounded-2xl border border-border/50 overflow-hidden">
        <div className="p-5 border-b border-border/50">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-violet-400/10 flex items-center justify-center">
              <Bell className="w-4 h-4 text-violet-400" />
            </div>
            <div>
              <h2 className="font-semibold text-foreground">Push Notifications</h2>
              <p className="text-xs text-muted-foreground">Real-time browser notifications</p>
            </div>
          </div>
        </div>
        <div className="divide-y divide-border/50">
          {[
            { key: 'push_on_agent_error', label: 'Agent errors', desc: 'When the agent encounters an error' },
            { key: 'push_on_application', label: 'Each application sent', desc: 'For every application submitted' },
          ].map((item) => (
            <div key={item.key} className="flex items-center justify-between p-4 hover:bg-secondary/30 transition-colors">
              <div>
                <p className="text-sm font-medium text-foreground">{item.label}</p>
                <p className="text-xs text-muted-foreground">{item.desc}</p>
              </div>
              <Switch
                checked={settings[item.key as keyof NotificationSettings]}
                onChange={() => toggle(item.key as keyof NotificationSettings)}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
