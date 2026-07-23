'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  User,
  SlidersHorizontal,
  FileText,
  Link2,
  CreditCard,
  Save,
  Loader2,
  Plus,
  X,
  Trash2,
  Upload,
  Check,
  Shield,
  Eye,
  EyeOff,
  ChevronDown,
  Crown,
  Sparkles,
  Star,
  Download,
} from 'lucide-react';
import api from '@/lib/api';
import { useToast } from '@/providers/toast-provider';
import { useAuthStore } from '@/stores/auth-store';
import { cn } from '@/lib/utils';
import { formatDate } from '@/lib/utils';

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

type TabKey = 'profile' | 'preferences' | 'resume' | 'linkedin' | 'billing';

interface TabDef {
  key: TabKey;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const tabs: TabDef[] = [
  { key: 'profile', label: 'Profile', icon: User },
  { key: 'preferences', label: 'Preferences', icon: SlidersHorizontal },
  { key: 'resume', label: 'Resume', icon: FileText },
  { key: 'linkedin', label: 'LinkedIn', icon: Link2 },
  { key: 'billing', label: 'Billing', icon: CreditCard },
];

/* ------------------------------------------------------------------ */
/*  Tag Input                                                          */
/* ------------------------------------------------------------------ */

function TagInput({
  tags,
  onAdd,
  onRemove,
  placeholder,
  colorClass = 'bg-primary/10 text-primary',
}: {
  tags: string[];
  onAdd: (tag: string) => void;
  onRemove: (index: number) => void;
  placeholder: string;
  colorClass?: string;
}) {
  const [value, setValue] = useState('');

  const handleAdd = () => {
    if (value.trim()) {
      onAdd(value.trim());
      setValue('');
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              handleAdd();
            }
          }}
          placeholder={placeholder}
          className="flex-1 px-4 py-2.5 bg-secondary border border-border/50 rounded-xl text-sm text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary/50 outline-none transition-all"
        />
        <button
          type="button"
          onClick={handleAdd}
          className="px-4 py-2.5 bg-secondary border border-border/50 rounded-xl hover:bg-secondary/80 text-muted-foreground hover:text-foreground transition-colors"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>
      <div className="flex flex-wrap gap-2">
        {tags.map((tag, i) => (
          <span
            key={i}
            className={cn(
              'inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium',
              colorClass
            )}
          >
            {tag}
            <button
              type="button"
              onClick={() => onRemove(i)}
              className="hover:opacity-70 transition-opacity"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </span>
        ))}
        {tags.length === 0 && (
          <span className="text-sm text-muted-foreground">None added yet</span>
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Profile Tab                                                        */
/* ------------------------------------------------------------------ */

function ProfileTab() {
  const { user } = useAuthStore();
  const { addToast } = useToast();
  const [fullName, setFullName] = useState('');
  const [yearsExp, setYearsExp] = useState<string>('');
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get('/profile/').catch(() => ({ data: null }));
        setFullName(user?.full_name || '');
        setYearsExp(
          res.data?.years_of_experience != null
            ? String(res.data.years_of_experience)
            : ''
        );
      } catch {
        setFullName(user?.full_name || '');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [user]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.patch('/profile/', {
        years_of_experience: yearsExp ? parseInt(yearsExp) : null,
      });
      if (fullName && fullName !== user?.full_name) {
        await api.patch('/users/me', { full_name: fullName });
      }
      addToast({ title: 'Profile saved', variant: 'success' });
    } catch {
      addToast({ title: 'Failed to save profile', variant: 'error' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="w-5 h-5 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-card rounded-2xl border border-border/50 p-6 space-y-5">
        <div className="space-y-2">
          <label className="text-sm font-semibold text-foreground">
            Full Name
          </label>
          <input
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Your full name"
            className="w-full px-4 py-2.5 bg-secondary border border-border/50 rounded-xl text-sm text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary/50 outline-none transition-all"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-semibold text-foreground">
            Years of Experience
          </label>
          <input
            type="number"
            min={0}
            max={50}
            value={yearsExp}
            onChange={(e) => setYearsExp(e.target.value)}
            placeholder="e.g. 3"
            className="w-full px-4 py-2.5 bg-secondary border border-border/50 rounded-xl text-sm text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary/50 outline-none transition-all"
          />
          <p className="text-xs text-muted-foreground">
            Used for job filtering. The agent will only show jobs within a
            reasonable range of your experience level.
          </p>
        </div>
      </div>

      <button
        onClick={handleSave}
        disabled={saving}
        className="px-6 py-2.5 bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-600 hover:to-violet-600 text-white text-sm font-medium rounded-xl flex items-center gap-2 transition-all shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/30 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {saving ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Save className="w-4 h-4" />
        )}
        Save
      </button>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Preferences Tab                                                    */
/* ------------------------------------------------------------------ */

function PreferencesTab() {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  const { data: prefs, isLoading } = useQuery({
    queryKey: ['preferences'],
    queryFn: () => api.get('/preferences/').then((r) => r.data),
  });

  const [form, setForm] = useState({
    desired_titles: [] as string[],
    desired_locations: [] as string[],
    remote_preference: 'any',
    min_match_score: 60,
  });

  useEffect(() => {
    if (prefs) {
      setForm({
        desired_titles: prefs.desired_titles || [],
        desired_locations: prefs.desired_locations || [],
        remote_preference: prefs.remote_preference || 'any',
        min_match_score: prefs.min_match_score ?? 60,
      });
    }
  }, [prefs]);

  const mutation = useMutation({
    mutationFn: (data: typeof form) => api.put('/preferences/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['preferences'] });
      addToast({ title: 'Preferences saved', variant: 'success' });
    },
    onError: () => {
      addToast({ title: 'Failed to save preferences', variant: 'error' });
    },
  });

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="w-5 h-5 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Target Titles */}
      <div className="bg-card rounded-2xl border border-border/50 p-6 space-y-4">
        <div>
          <label className="text-sm font-semibold text-foreground">
            Target Job Titles
          </label>
          <p className="text-xs text-muted-foreground mt-0.5">
            Jobs matching these titles will be prioritized
          </p>
        </div>
        <TagInput
          tags={form.desired_titles}
          onAdd={(tag) =>
            setForm((prev) => ({
              ...prev,
              desired_titles: [...prev.desired_titles, tag],
            }))
          }
          onRemove={(i) =>
            setForm((prev) => ({
              ...prev,
              desired_titles: prev.desired_titles.filter((_, idx) => idx !== i),
            }))
          }
          placeholder="e.g. Software Engineer"
          colorClass="bg-blue-400/10 text-blue-400"
        />
      </div>

      {/* Preferred Locations */}
      <div className="bg-card rounded-2xl border border-border/50 p-6 space-y-4">
        <div>
          <label className="text-sm font-semibold text-foreground">
            Preferred Locations
          </label>
          <p className="text-xs text-muted-foreground mt-0.5">
            Where you want to work
          </p>
        </div>
        <TagInput
          tags={form.desired_locations}
          onAdd={(tag) =>
            setForm((prev) => ({
              ...prev,
              desired_locations: [...prev.desired_locations, tag],
            }))
          }
          onRemove={(i) =>
            setForm((prev) => ({
              ...prev,
              desired_locations: prev.desired_locations.filter(
                (_, idx) => idx !== i
              ),
            }))
          }
          placeholder="e.g. Remote, San Francisco"
          colorClass="bg-emerald-400/10 text-emerald-400"
        />
      </div>

      {/* Remote Preference */}
      <div className="bg-card rounded-2xl border border-border/50 p-6 space-y-4">
        <label className="text-sm font-semibold text-foreground">
          Remote Preference
        </label>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {[
            { value: 'remote', label: 'Remote Only' },
            { value: 'hybrid', label: 'Hybrid' },
            { value: 'onsite', label: 'On-site' },
            { value: 'any', label: 'Any' },
          ].map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() =>
                setForm((prev) => ({
                  ...prev,
                  remote_preference: opt.value,
                }))
              }
              className={cn(
                'px-4 py-2.5 text-sm font-medium rounded-xl transition-all',
                form.remote_preference === opt.value
                  ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/20'
                  : 'bg-secondary border border-border/50 text-muted-foreground hover:text-foreground hover:border-border'
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Minimum Match Score */}
      <div className="bg-card rounded-2xl border border-border/50 p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <label className="text-sm font-semibold text-foreground">
              Minimum Match Score
            </label>
            <p className="text-xs text-muted-foreground mt-0.5">
              Only apply to jobs matching this threshold
            </p>
          </div>
          <span className="text-2xl font-bold text-primary">
            {form.min_match_score}%
          </span>
        </div>
        <div className="relative pt-2">
          <input
            type="range"
            min="0"
            max="100"
            step="5"
            value={form.min_match_score}
            onChange={(e) =>
              setForm((prev) => ({
                ...prev,
                min_match_score: parseInt(e.target.value),
              }))
            }
            className="w-full h-2 bg-secondary rounded-full appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary [&::-webkit-slider-thumb]:shadow-lg [&::-webkit-slider-thumb]:shadow-primary/30 [&::-webkit-slider-thumb]:cursor-pointer"
          />
          <div className="flex justify-between text-xs text-muted-foreground mt-2">
            <span>0%</span>
            <span>50%</span>
            <span>100%</span>
          </div>
        </div>
      </div>

      <button
        onClick={() => mutation.mutate(form)}
        disabled={mutation.isPending}
        className="px-6 py-2.5 bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-600 hover:to-violet-600 text-white text-sm font-medium rounded-xl flex items-center gap-2 transition-all shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/30 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {mutation.isPending ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Save className="w-4 h-4" />
        )}
        Save
      </button>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Resume Tab                                                         */
/* ------------------------------------------------------------------ */

interface ResumeItem {
  id: string;
  title: string;
  file_name: string;
  file_url: string;
  is_default: boolean;
  created_at: string;
}

function ResumeTab() {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const { data: resumes, isLoading } = useQuery({
    queryKey: ['resumes'],
    queryFn: () => api.get<ResumeItem[]>('/resumes/').then((r) => r.data),
  });

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', file.name.replace(/\.[^/.]+$/, ''));
      return api.post('/resumes/', formData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] });
      addToast({ title: 'Resume uploaded', variant: 'success' });
    },
    onError: (error: any) => {
      const message =
        error.response?.data?.detail || 'Failed to upload resume';
      addToast({ title: message, variant: 'error' });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/resumes/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] });
      addToast({ title: 'Resume deleted', variant: 'success' });
    },
    onError: () => {
      addToast({ title: 'Failed to delete resume', variant: 'error' });
    },
  });

  const setPrimaryMutation = useMutation({
    mutationFn: (id: string) =>
      api.patch(`/resumes/${id}`, { is_default: true }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] });
      addToast({ title: 'Primary resume updated', variant: 'success' });
    },
    onError: () => {
      addToast({
        title: 'Failed to update primary resume',
        variant: 'error',
      });
    },
  });

  const handleDownload = async (resume: ResumeItem) => {
    try {
      const response = await api.get(`/resumes/${resume.id}/download`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', resume.file_name);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch {
      addToast({ title: 'Failed to download resume', variant: 'error' });
    }
  };

  const handleFile = useCallback(
    (file: File) => {
      uploadMutation.mutate(file);
    },
    [uploadMutation]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setDragging(false);
  }, []);

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="w-5 h-5 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Existing resumes */}
      {resumes && resumes.length > 0 && (
        <div className="bg-card rounded-2xl border border-border/50 p-6 space-y-3">
          <h3 className="text-sm font-semibold text-foreground mb-4">
            Your Resumes
          </h3>
          {resumes.map((resume) => (
            <div
              key={resume.id}
              className="flex items-center justify-between p-3 bg-secondary/50 rounded-xl border border-border/30"
            >
              <div className="flex items-center gap-3 min-w-0">
                <FileText className="w-5 h-5 text-primary flex-shrink-0" />
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-foreground truncate">
                      {resume.title || resume.file_name}
                    </p>
                    {resume.is_default && (
                      <span className="text-[10px] px-2 py-0.5 bg-primary/10 text-primary rounded-full font-semibold flex-shrink-0">
                        Primary
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Uploaded {formatDate(resume.created_at)}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-1 flex-shrink-0">
                {!resume.is_default && (
                  <button
                    onClick={() => setPrimaryMutation.mutate(resume.id)}
                    disabled={setPrimaryMutation.isPending}
                    title="Set as primary"
                    className="p-2 text-muted-foreground hover:text-foreground hover:bg-secondary rounded-lg transition-colors"
                  >
                    <Star className="w-4 h-4" />
                  </button>
                )}
                <button
                  onClick={() => handleDownload(resume)}
                  title="Download"
                  className="p-2 text-muted-foreground hover:text-foreground hover:bg-secondary rounded-lg transition-colors"
                >
                  <Download className="w-4 h-4" />
                </button>
                <button
                  onClick={() => deleteMutation.mutate(resume.id)}
                  disabled={deleteMutation.isPending}
                  title="Delete"
                  className="p-2 text-muted-foreground hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Upload area */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
        className={cn(
          'bg-card rounded-2xl border-2 border-dashed p-8 text-center cursor-pointer transition-all',
          dragging
            ? 'border-primary bg-primary/5'
            : 'border-border/50 hover:border-primary/40'
        )}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.doc,.docx"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
            e.target.value = '';
          }}
        />
        {uploadMutation.isPending ? (
          <div className="flex items-center justify-center gap-2 text-muted-foreground">
            <Loader2 className="w-5 h-5 animate-spin" />
            <span className="text-sm">Uploading...</span>
          </div>
        ) : (
          <>
            <Upload className="w-8 h-8 text-muted-foreground mx-auto mb-3" />
            <p className="text-sm font-medium text-foreground">
              Drop your resume here or click to browse
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              PDF or DOC, max 10MB
            </p>
          </>
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  LinkedIn Tab                                                       */
/* ------------------------------------------------------------------ */

function LinkedInTab() {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  const { data: credentials } = useQuery({
    queryKey: ['credentials'],
    queryFn: () => api.get('/credentials/').then((r) => r.data),
  });

  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ email: '', password: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [loadingCreds, setLoadingCreds] = useState(false);

  const connectMutation = useMutation({
    mutationFn: (data: { email: string; password: string }) =>
      api.post('/credentials/linkedin', {
        username: data.email,
        password: data.password,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['credentials'] });
      addToast({ title: 'LinkedIn updated successfully', variant: 'success' });
      setShowForm(false);
      setEditing(false);
      setForm({ email: '', password: '' });
    },
    onError: (error: any) => {
      const message =
        error.response?.data?.detail ||
        'Connection failed. Check your credentials.';
      addToast({ title: message, variant: 'error' });
    },
  });

  const disconnectMutation = useMutation({
    mutationFn: () => api.delete('/credentials/linkedin'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['credentials'] });
      addToast({ title: 'LinkedIn disconnected', variant: 'success' });
      setEditing(false);
      setForm({ email: '', password: '' });
    },
    onError: (error: any) => {
      const message =
        error.response?.data?.detail || 'Failed to disconnect.';
      addToast({ title: message, variant: 'error' });
    },
  });

  const getStatus = () => {
    const cred = credentials?.find((c: any) => c.platform === 'linkedin');
    return cred
      ? { connected: true, valid: cred.is_valid, username: cred.username }
      : { connected: false, valid: false, username: '' };
  };

  const status = getStatus();

  const toggleEdit = async () => {
    if (editing) {
      setEditing(false);
      setForm({ email: '', password: '' });
      return;
    }
    setLoadingCreds(true);
    try {
      const res = await api.get('/credentials/linkedin/detail');
      setForm({ email: res.data.email, password: res.data.password });
    } catch {
      setForm({ email: status.username || '', password: '' });
    }
    setLoadingCreds(false);
    setEditing(true);
  };

  return (
    <div className="space-y-6">
      <div className="bg-card rounded-2xl border border-border/50 p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 bg-blue-500/10 rounded-xl flex items-center justify-center">
              <span className="text-blue-400 font-bold text-sm">in</span>
            </div>
            <div>
              <h3 className="font-semibold text-foreground">LinkedIn</h3>
              <p className="text-xs text-muted-foreground">
                Easy Apply automation
              </p>
            </div>
          </div>
          {status.connected ? (
            <div className="flex items-center gap-2">
              <span className="flex items-center gap-1.5 text-sm text-emerald-400 bg-emerald-400/10 px-3 py-1.5 rounded-full">
                <Check className="w-3.5 h-3.5" /> Connected
              </span>
              <button
                onClick={toggleEdit}
                disabled={loadingCreds}
                className="p-2 text-muted-foreground hover:text-foreground hover:bg-secondary rounded-lg transition-colors"
              >
                {loadingCreds ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <ChevronDown
                    className={cn(
                      'w-4 h-4 transition-transform',
                      editing && 'rotate-180'
                    )}
                  />
                )}
              </button>
              <button
                onClick={() => disconnectMutation.mutate()}
                className="p-2 text-muted-foreground hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowForm(!showForm)}
              className={cn(
                'px-5 py-2.5 text-sm font-medium rounded-xl flex items-center gap-2 transition-all',
                showForm
                  ? 'bg-secondary text-foreground'
                  : 'bg-blue-500 hover:bg-blue-600 text-white shadow-lg shadow-blue-500/20'
              )}
            >
              <Link2 className="w-4 h-4" />
              {showForm ? 'Cancel' : 'Connect'}
            </button>
          )}
        </div>

        {/* Connected user email */}
        {status.connected && !editing && status.username && (
          <p className="text-sm text-muted-foreground">
            Connected as{' '}
            <span className="font-medium text-foreground">
              {status.username}
            </span>
          </p>
        )}

        {/* Edit form (connected) */}
        {editing && status.connected && (
          <div className="pt-4 border-t border-border/50 space-y-4">
            <p className="text-xs text-muted-foreground">
              Update your LinkedIn credentials
            </p>
            <input
              type="email"
              value={form.email}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, email: e.target.value }))
              }
              placeholder="LinkedIn email"
              className="w-full px-4 py-2.5 bg-secondary border border-border/50 rounded-xl text-sm text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary/50 outline-none transition-all"
            />
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={form.password}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, password: e.target.value }))
                }
                placeholder="Password"
                className="w-full px-4 py-2.5 pr-11 bg-secondary border border-border/50 rounded-xl text-sm text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary/50 outline-none transition-all"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              >
                {showPassword ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
              </button>
            </div>
            <button
              onClick={() => connectMutation.mutate(form)}
              disabled={
                connectMutation.isPending ||
                !form.email.trim() ||
                !form.password.trim()
              }
              className="w-full py-2.5 bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-600 hover:to-violet-600 text-white text-sm font-medium rounded-xl flex items-center justify-center gap-2 transition-all shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/30 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none"
            >
              {connectMutation.isPending && (
                <Loader2 className="w-4 h-4 animate-spin" />
              )}
              Update
            </button>
          </div>
        )}

        {/* Connect form (not connected) */}
        {showForm && !status.connected && (
          <div className="pt-4 border-t border-border/50 space-y-4">
            <div className="p-3 bg-amber-400/10 border border-amber-400/20 rounded-xl text-xs text-amber-400 flex items-start gap-2">
              <Shield className="w-4 h-4 flex-shrink-0 mt-0.5" />
              Your credentials are encrypted and stored securely. We use them
              only for automated applications.
            </div>
            <input
              type="email"
              value={form.email}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, email: e.target.value }))
              }
              placeholder="LinkedIn email"
              className="w-full px-4 py-2.5 bg-secondary border border-border/50 rounded-xl text-sm text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary/50 outline-none transition-all"
            />
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={form.password}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, password: e.target.value }))
                }
                placeholder="LinkedIn password"
                className="w-full px-4 py-2.5 pr-11 bg-secondary border border-border/50 rounded-xl text-sm text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary/50 outline-none transition-all"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              >
                {showPassword ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
              </button>
            </div>
            <button
              onClick={() => connectMutation.mutate(form)}
              disabled={
                connectMutation.isPending ||
                !form.email.trim() ||
                !form.password.trim()
              }
              className="w-full py-2.5 bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-600 hover:to-violet-600 text-white text-sm font-medium rounded-xl flex items-center justify-center gap-2 transition-all shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/30 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none"
            >
              {connectMutation.isPending && (
                <Loader2 className="w-4 h-4 animate-spin" />
              )}
              Connect LinkedIn
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Billing Tab                                                        */
/* ------------------------------------------------------------------ */

function BillingTab() {
  return (
    <div className="space-y-6">
      {/* Current Plan */}
      <div className="relative bg-gradient-to-br from-primary/10 to-transparent rounded-2xl border border-primary/20 p-6 overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl" />
        <div className="relative z-10 flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-primary/20 flex items-center justify-center">
            <Crown className="w-6 h-6 text-primary" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold text-foreground">Free Plan</h3>
              <span className="text-xs px-2.5 py-1 bg-primary text-primary-foreground rounded-full font-semibold">
                Current
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              You are on the free tier
            </p>
          </div>
        </div>
      </div>

      {/* Free plan features */}
      <div className="bg-card rounded-2xl border border-border/50 p-6">
        <h4 className="text-sm font-semibold text-foreground mb-4">
          What you get
        </h4>
        <ul className="space-y-3">
          {[
            '10 applications per month',
            'Basic job matching',
            'LinkedIn Easy Apply',
            'Email support',
          ].map((feature) => (
            <li
              key={feature}
              className="flex items-center gap-2 text-sm text-muted-foreground"
            >
              <div className="w-5 h-5 rounded-full bg-emerald-400/10 flex items-center justify-center flex-shrink-0">
                <Check className="w-3 h-3 text-emerald-400" />
              </div>
              {feature}
            </li>
          ))}
        </ul>
      </div>

      {/* Pro plan coming soon */}
      <div className="bg-card rounded-2xl border border-border/50 p-6 opacity-60">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-foreground">
              Pro Plan
            </h4>
            <span className="text-xs text-muted-foreground">Coming Soon</span>
          </div>
        </div>
        <ul className="space-y-3">
          {[
            '100 applications per month',
            'AI-powered job matching',
            'All job platforms',
            'Cold email outreach',
            'Priority support',
          ].map((feature) => (
            <li
              key={feature}
              className="flex items-center gap-2 text-sm text-muted-foreground"
            >
              <div className="w-5 h-5 rounded-full bg-amber-400/10 flex items-center justify-center flex-shrink-0">
                <Check className="w-3 h-3 text-amber-400" />
              </div>
              {feature}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main Settings Page                                                 */
/* ------------------------------------------------------------------ */

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<TabKey>('profile');

  const renderTab = () => {
    switch (activeTab) {
      case 'profile':
        return <ProfileTab />;
      case 'preferences':
        return <PreferencesTab />;
      case 'resume':
        return <ResumeTab />;
      case 'linkedin':
        return <LinkedInTab />;
      case 'billing':
        return <BillingTab />;
      default:
        return null;
    }
  };

  return (
    <div className="max-w-3xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground tracking-tight">
          Settings
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          Manage your account and preferences
        </p>
      </div>

      {/* Tab bar */}
      <div className="flex flex-wrap gap-1 p-1 bg-secondary/50 rounded-xl border border-border/30">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={cn(
              'flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-all',
              activeTab === tab.key
                ? 'bg-primary text-primary-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground hover:bg-secondary/80'
            )}
          >
            <tab.icon className="w-4 h-4" />
            <span className="hidden sm:inline">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div>{renderTab()}</div>
    </div>
  );
}
