'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Check, Loader2, Trash2, Shield, Link2, Eye, EyeOff, ChevronDown, Cable } from 'lucide-react';
import api from '@/lib/api';
import { useToast } from '@/providers/toast-provider';
import { cn } from '@/lib/utils';

export default function ConnectionsPage() {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  const { data: credentials } = useQuery({
    queryKey: ['credentials'],
    queryFn: () => api.get('/credentials/').then((r) => r.data),
  });

  const [showLinkedIn, setShowLinkedIn] = useState(false);
  const [showNaukri, setShowNaukri] = useState(false);
  const [linkedInForm, setLinkedInForm] = useState({ email: '', password: '' });
  const [naukriForm, setNaukriForm] = useState({ email: '', password: '' });
  const [showLinkedInPassword, setShowLinkedInPassword] = useState(false);
  const [showNaukriPassword, setShowNaukriPassword] = useState(false);
  const [editingLinkedIn, setEditingLinkedIn] = useState(false);
  const [editingNaukri, setEditingNaukri] = useState(false);
  const [loadingLinkedInCreds, setLoadingLinkedInCreds] = useState(false);
  const [loadingNaukriCreds, setLoadingNaukriCreds] = useState(false);

  const connectMutation = useMutation({
    mutationFn: ({ platform, data }: { platform: string; data: { email: string; password: string } }) =>
      api.post(`/credentials/${platform}`, { username: data.email, password: data.password }),
    onSuccess: (_, { platform }) => {
      queryClient.invalidateQueries({ queryKey: ['credentials'] });
      addToast({ title: `${platform} updated successfully`, variant: 'success' });
      setShowLinkedIn(false);
      setShowNaukri(false);
      setEditingLinkedIn(false);
      setEditingNaukri(false);
      setLinkedInForm({ email: '', password: '' });
      setNaukriForm({ email: '', password: '' });
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Connection failed. Check your credentials.';
      addToast({ title: message, variant: 'error' });
    },
  });

  const disconnectMutation = useMutation({
    mutationFn: (platform: string) => api.delete(`/credentials/${platform}`),
    onSuccess: (_, platform) => {
      queryClient.invalidateQueries({ queryKey: ['credentials'] });
      addToast({ title: 'Disconnected', variant: 'success' });
      if (platform === 'linkedin') { setEditingLinkedIn(false); setLinkedInForm({ email: '', password: '' }); }
      if (platform === 'naukri') { setEditingNaukri(false); setNaukriForm({ email: '', password: '' }); }
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to disconnect. Please try again.';
      addToast({ title: message, variant: 'error' });
    },
  });

  const toggleEditLinkedIn = async () => {
    if (editingLinkedIn) {
      setEditingLinkedIn(false);
      setLinkedInForm({ email: '', password: '' });
      return;
    }
    setLoadingLinkedInCreds(true);
    try {
      const res = await api.get('/credentials/linkedin/detail');
      setLinkedInForm({ email: res.data.email, password: res.data.password });
    } catch {
      const cred = credentials?.find((c: any) => c.platform === 'linkedin');
      setLinkedInForm({ email: cred?.username || '', password: '' });
    }
    setLoadingLinkedInCreds(false);
    setEditingLinkedIn(true);
  };

  const toggleEditNaukri = async () => {
    if (editingNaukri) {
      setEditingNaukri(false);
      setNaukriForm({ email: '', password: '' });
      return;
    }
    setLoadingNaukriCreds(true);
    try {
      const res = await api.get('/credentials/naukri/detail');
      setNaukriForm({ email: res.data.email, password: res.data.password });
    } catch {
      const cred = credentials?.find((c: any) => c.platform === 'naukri');
      setNaukriForm({ email: cred?.username || '', password: '' });
    }
    setLoadingNaukriCreds(false);
    setEditingNaukri(true);
  };

  const getStatus = (platform: string) => {
    const cred = credentials?.find((c: any) => c.platform === platform);
    return cred ? { connected: true, valid: cred.is_valid } : { connected: false, valid: false };
  };

  const linkedIn = getStatus('linkedin');
  const naukri = getStatus('naukri');

  return (
    <div className="max-w-2xl space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-1">
          <div className="w-9 h-9 rounded-lg bg-blue-500/10 flex items-center justify-center">
            <Cable className="w-4 h-4 text-blue-400" />
          </div>
          <h1 className="text-2xl font-bold text-foreground tracking-tight">Connections</h1>
        </div>
        <p className="text-muted-foreground text-sm mt-1 ml-12">Connect your job platform accounts for automated applications</p>
      </div>

      {/* LinkedIn */}
      <div className="bg-card rounded-2xl border border-border/50 p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 bg-blue-500/10 rounded-xl flex items-center justify-center">
              <span className="text-blue-400 font-bold text-sm">in</span>
            </div>
            <div>
              <h3 className="font-semibold text-foreground">LinkedIn</h3>
              <p className="text-xs text-muted-foreground">Easy Apply automation</p>
            </div>
          </div>
          {linkedIn.connected ? (
            <div className="flex items-center gap-2">
              <span className="flex items-center gap-1.5 text-sm text-emerald-400 bg-emerald-400/10 px-3 py-1.5 rounded-full">
                <Check className="w-3.5 h-3.5" /> Connected
              </span>
              <button
                onClick={toggleEditLinkedIn}
                disabled={loadingLinkedInCreds}
                className="p-2 text-muted-foreground hover:text-foreground hover:bg-secondary rounded-lg transition-colors"
              >
                {loadingLinkedInCreds ? <Loader2 className="w-4 h-4 animate-spin" /> : <ChevronDown className={cn("w-4 h-4 transition-transform", editingLinkedIn && "rotate-180")} />}
              </button>
              <button
                onClick={() => disconnectMutation.mutate('linkedin')}
                className="p-2 text-muted-foreground hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowLinkedIn(!showLinkedIn)}
              className={cn(
                'px-5 py-2.5 text-sm font-medium rounded-xl flex items-center gap-2 transition-all',
                showLinkedIn
                  ? 'bg-secondary text-foreground'
                  : 'bg-blue-500 hover:bg-blue-600 text-white shadow-lg shadow-blue-500/20'
              )}
            >
              <Link2 className="w-4 h-4" />
              {showLinkedIn ? 'Cancel' : 'Connect'}
            </button>
          )}
        </div>

        {editingLinkedIn && linkedIn.connected && (
          <div className="pt-4 border-t border-border/50 space-y-4">
            <p className="text-xs text-muted-foreground">Update your LinkedIn credentials</p>
            <input
              type="email"
              value={linkedInForm.email}
              onChange={(e) => setLinkedInForm(prev => ({ ...prev, email: e.target.value }))}
              placeholder="LinkedIn email"
              className="w-full px-4 py-2.5 bg-secondary border border-border/50 rounded-xl text-sm text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary/50 outline-none transition-all"
            />
            <div className="relative">
              <input
                type={showLinkedInPassword ? 'text' : 'password'}
                value={linkedInForm.password}
                onChange={(e) => setLinkedInForm(prev => ({ ...prev, password: e.target.value }))}
                placeholder="Password"
                className="w-full px-4 py-2.5 pr-11 bg-secondary border border-border/50 rounded-xl text-sm text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary/50 outline-none transition-all"
              />
              <button
                type="button"
                onClick={() => setShowLinkedInPassword(!showLinkedInPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              >
                {showLinkedInPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            <button
              onClick={() => connectMutation.mutate({ platform: 'linkedin', data: linkedInForm })}
              disabled={connectMutation.isPending || !linkedInForm.email.trim() || !linkedInForm.password.trim()}
              className="w-full py-2.5 bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-medium rounded-xl flex items-center justify-center gap-2 transition-all shadow-lg shadow-primary/20 hover:shadow-primary/30 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none"
            >
              {connectMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
              Update
            </button>
          </div>
        )}

        {showLinkedIn && !linkedIn.connected && (
          <div className="pt-4 border-t border-border/50 space-y-4">
            <div className="p-3 bg-amber-400/10 border border-amber-400/20 rounded-xl text-xs text-amber-400 flex items-start gap-2">
              <Shield className="w-4 h-4 flex-shrink-0 mt-0.5" />
              Your credentials are encrypted and stored securely. We use them only for automated applications.
            </div>
            <input
              type="email"
              value={linkedInForm.email}
              onChange={(e) => setLinkedInForm(prev => ({ ...prev, email: e.target.value }))}
              placeholder="LinkedIn email"
              className="w-full px-4 py-2.5 bg-secondary border border-border/50 rounded-xl text-sm text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary/50 outline-none transition-all"
            />
            <div className="relative">
              <input
                type={showLinkedInPassword ? 'text' : 'password'}
                value={linkedInForm.password}
                onChange={(e) => setLinkedInForm(prev => ({ ...prev, password: e.target.value }))}
                placeholder="LinkedIn password"
                className="w-full px-4 py-2.5 pr-11 bg-secondary border border-border/50 rounded-xl text-sm text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary/50 outline-none transition-all"
              />
              <button
                type="button"
                onClick={() => setShowLinkedInPassword(!showLinkedInPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              >
                {showLinkedInPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            <button
              onClick={() => connectMutation.mutate({ platform: 'linkedin', data: linkedInForm })}
              disabled={connectMutation.isPending || !linkedInForm.email.trim() || !linkedInForm.password.trim()}
              className="w-full py-2.5 bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-medium rounded-xl flex items-center justify-center gap-2 transition-all shadow-lg shadow-primary/20 hover:shadow-primary/30 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none"
            >
              {connectMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
              Connect LinkedIn
            </button>
          </div>
        )}
      </div>

      {/* Naukri */}
      <div className="bg-card rounded-2xl border border-border/50 p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 bg-violet-500/10 rounded-xl flex items-center justify-center">
              <span className="text-violet-400 font-bold text-sm">N</span>
            </div>
            <div>
              <h3 className="font-semibold text-foreground">Naukri.com</h3>
              <p className="text-xs text-muted-foreground">Quick Apply automation</p>
            </div>
          </div>
          {naukri.connected ? (
            <div className="flex items-center gap-2">
              <span className="flex items-center gap-1.5 text-sm text-emerald-400 bg-emerald-400/10 px-3 py-1.5 rounded-full">
                <Check className="w-3.5 h-3.5" /> Connected
              </span>
              <button
                onClick={toggleEditNaukri}
                disabled={loadingNaukriCreds}
                className="p-2 text-muted-foreground hover:text-foreground hover:bg-secondary rounded-lg transition-colors"
              >
                {loadingNaukriCreds ? <Loader2 className="w-4 h-4 animate-spin" /> : <ChevronDown className={cn("w-4 h-4 transition-transform", editingNaukri && "rotate-180")} />}
              </button>
              <button
                onClick={() => disconnectMutation.mutate('naukri')}
                className="p-2 text-muted-foreground hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowNaukri(!showNaukri)}
              className={cn(
                'px-5 py-2.5 text-sm font-medium rounded-xl flex items-center gap-2 transition-all',
                showNaukri
                  ? 'bg-secondary text-foreground'
                  : 'bg-violet-500 hover:bg-violet-600 text-white shadow-lg shadow-violet-500/20'
              )}
            >
              <Link2 className="w-4 h-4" />
              {showNaukri ? 'Cancel' : 'Connect'}
            </button>
          )}
        </div>

        {editingNaukri && naukri.connected && (
          <div className="pt-4 border-t border-border/50 space-y-4">
            <p className="text-xs text-muted-foreground">Update your Naukri credentials</p>
            <input
              type="email"
              value={naukriForm.email}
              onChange={(e) => setNaukriForm(prev => ({ ...prev, email: e.target.value }))}
              placeholder="Naukri email"
              className="w-full px-4 py-2.5 bg-secondary border border-border/50 rounded-xl text-sm text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary/50 outline-none transition-all"
            />
            <div className="relative">
              <input
                type={showNaukriPassword ? 'text' : 'password'}
                value={naukriForm.password}
                onChange={(e) => setNaukriForm(prev => ({ ...prev, password: e.target.value }))}
                placeholder="Password"
                className="w-full px-4 py-2.5 pr-11 bg-secondary border border-border/50 rounded-xl text-sm text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary/50 outline-none transition-all"
              />
              <button
                type="button"
                onClick={() => setShowNaukriPassword(!showNaukriPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              >
                {showNaukriPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            <button
              onClick={() => connectMutation.mutate({ platform: 'naukri', data: naukriForm })}
              disabled={connectMutation.isPending || !naukriForm.email.trim() || !naukriForm.password.trim()}
              className="w-full py-2.5 bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-medium rounded-xl flex items-center justify-center gap-2 transition-all shadow-lg shadow-primary/20 hover:shadow-primary/30 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none"
            >
              {connectMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
              Update
            </button>
          </div>
        )}

        {showNaukri && !naukri.connected && (
          <div className="pt-4 border-t border-border/50 space-y-4">
            <input
              type="email"
              value={naukriForm.email}
              onChange={(e) => setNaukriForm(prev => ({ ...prev, email: e.target.value }))}
              placeholder="Naukri email"
              className="w-full px-4 py-2.5 bg-secondary border border-border/50 rounded-xl text-sm text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary/50 outline-none transition-all"
            />
            <div className="relative">
              <input
                type={showNaukriPassword ? 'text' : 'password'}
                value={naukriForm.password}
                onChange={(e) => setNaukriForm(prev => ({ ...prev, password: e.target.value }))}
                placeholder="Naukri password"
                className="w-full px-4 py-2.5 pr-11 bg-secondary border border-border/50 rounded-xl text-sm text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary/50 outline-none transition-all"
              />
              <button
                type="button"
                onClick={() => setShowNaukriPassword(!showNaukriPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              >
                {showNaukriPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            <button
              onClick={() => connectMutation.mutate({ platform: 'naukri', data: naukriForm })}
              disabled={connectMutation.isPending || !naukriForm.email.trim() || !naukriForm.password.trim()}
              className="w-full py-2.5 bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-medium rounded-xl flex items-center justify-center gap-2 transition-all shadow-lg shadow-primary/20 hover:shadow-primary/30 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none"
            >
              {connectMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
              Connect Naukri
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
