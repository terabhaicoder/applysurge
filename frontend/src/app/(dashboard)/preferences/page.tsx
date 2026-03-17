'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Save, Plus, X, Loader2, Target, MapPin, DollarSign, Sparkles, SlidersHorizontal } from 'lucide-react';
import api from '@/lib/api';
import { useToast } from '@/providers/toast-provider';
import { cn } from '@/lib/utils';

export default function PreferencesPage() {
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
    min_salary: '',
    experience_levels: [] as string[],
    min_match_score: 60,
    excluded_companies: [] as string[],
    excluded_keywords: [] as string[],
  });

  const [newTitle, setNewTitle] = useState('');
  const [newLocation, setNewLocation] = useState('');

  useEffect(() => {
    if (prefs) {
      setForm({
        desired_titles: prefs.desired_titles || [],
        desired_locations: prefs.desired_locations || [],
        remote_preference: prefs.remote_preference || 'any',
        min_salary: prefs.min_salary?.toString() || '',
        experience_levels: prefs.experience_levels || [],
        min_match_score: prefs.min_match_score ?? 60,
        excluded_companies: prefs.excluded_companies || [],
        excluded_keywords: prefs.excluded_keywords || [],
      });
    }
  }, [prefs]);

  const mutation = useMutation({
    mutationFn: (data: any) => api.put('/preferences/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['preferences'] });
      addToast({ title: 'Preferences saved', variant: 'success' });
    },
    onError: () => {
      addToast({ title: 'Failed to save preferences', variant: 'error' });
    },
  });

  const handleSave = () => {
    mutation.mutate({
      ...form,
      min_salary: form.min_salary ? parseInt(form.min_salary) : null,
    });
  };

  const addToList = (field: string, value: string, setter: (v: string) => void) => {
    if (value.trim()) {
      setForm((prev: any) => ({ ...prev, [field]: [...prev[field], value.trim()] }));
      setter('');
    }
  };

  const removeFromList = (field: string, index: number) => {
    setForm((prev: any) => ({ ...prev, [field]: prev[field].filter((_: any, i: number) => i !== index) }));
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <div className="w-12 h-12 rounded-2xl bg-card border border-border/50 flex items-center justify-center">
          <Loader2 className="w-5 h-5 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="w-9 h-9 rounded-lg bg-amber-500/10 flex items-center justify-center">
              <SlidersHorizontal className="w-4 h-4 text-amber-400" />
            </div>
            <h1 className="text-2xl font-bold text-foreground tracking-tight">Job Preferences</h1>
          </div>
          <p className="text-muted-foreground text-sm mt-1 ml-12">Define what jobs the agent should look for</p>
        </div>
        <button
          onClick={handleSave}
          disabled={mutation.isPending}
          className="px-5 py-2.5 bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-medium rounded-xl flex items-center gap-2 transition-all shadow-lg shadow-primary/20 hover:shadow-primary/30"
        >
          {mutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          Save Changes
        </button>
      </div>

      {/* Target Titles */}
      <div className="bg-card rounded-2xl border border-border/50 p-6 space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-blue-400/10 flex items-center justify-center">
            <Target className="w-4 h-4 text-blue-400" />
          </div>
          <div>
            <label className="text-sm font-semibold text-foreground">Target Job Titles</label>
            <p className="text-xs text-muted-foreground">Jobs matching these titles will be prioritized</p>
          </div>
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addToList('desired_titles', newTitle, setNewTitle))}
            placeholder="e.g. Software Engineer"
            className="flex-1 px-4 py-2.5 bg-secondary border border-border/50 rounded-xl text-sm text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary/50 outline-none transition-all"
          />
          <button
            onClick={() => addToList('desired_titles', newTitle, setNewTitle)}
            className="px-4 py-2.5 bg-secondary border border-border/50 rounded-xl hover:bg-secondary/80 text-muted-foreground hover:text-foreground transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {form.desired_titles.map((t, i) => (
            <span key={i} className="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-400/10 text-blue-400 rounded-full text-sm font-medium">
              {t}
              <button onClick={() => removeFromList('desired_titles', i)} className="hover:text-blue-200 transition-colors">
                <X className="w-3.5 h-3.5" />
              </button>
            </span>
          ))}
          {form.desired_titles.length === 0 && (
            <span className="text-sm text-muted-foreground">No titles added yet</span>
          )}
        </div>
      </div>

      {/* Preferred Locations */}
      <div className="bg-card rounded-2xl border border-border/50 p-6 space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-400/10 flex items-center justify-center">
            <MapPin className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <label className="text-sm font-semibold text-foreground">Preferred Locations</label>
            <p className="text-xs text-muted-foreground">Where you want to work</p>
          </div>
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={newLocation}
            onChange={(e) => setNewLocation(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addToList('desired_locations', newLocation, setNewLocation))}
            placeholder="e.g. Remote, San Francisco"
            className="flex-1 px-4 py-2.5 bg-secondary border border-border/50 rounded-xl text-sm text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary/50 outline-none transition-all"
          />
          <button
            onClick={() => addToList('desired_locations', newLocation, setNewLocation)}
            className="px-4 py-2.5 bg-secondary border border-border/50 rounded-xl hover:bg-secondary/80 text-muted-foreground hover:text-foreground transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {form.desired_locations.map((l, i) => (
            <span key={i} className="inline-flex items-center gap-2 px-3 py-1.5 bg-emerald-400/10 text-emerald-400 rounded-full text-sm font-medium">
              {l}
              <button onClick={() => removeFromList('desired_locations', i)} className="hover:text-emerald-200 transition-colors">
                <X className="w-3.5 h-3.5" />
              </button>
            </span>
          ))}
          {form.desired_locations.length === 0 && (
            <span className="text-sm text-muted-foreground">No locations added yet</span>
          )}
        </div>
      </div>

      {/* Remote Preference */}
      <div className="bg-card rounded-2xl border border-border/50 p-6 space-y-4">
        <label className="text-sm font-semibold text-foreground">Remote Preference</label>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {[
            { value: 'any', label: 'Any' },
            { value: 'remote', label: 'Remote' },
            { value: 'hybrid', label: 'Hybrid' },
            { value: 'onsite', label: 'Onsite' },
          ].map((opt) => (
            <button
              key={opt.value}
              onClick={() => setForm(prev => ({ ...prev, remote_preference: opt.value }))}
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

      {/* Minimum Salary */}
      <div className="bg-card rounded-2xl border border-border/50 p-6 space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-amber-400/10 flex items-center justify-center">
            <DollarSign className="w-4 h-4 text-amber-400" />
          </div>
          <div>
            <label className="text-sm font-semibold text-foreground">Minimum Salary (Annual)</label>
            <p className="text-xs text-muted-foreground">Only show jobs above this salary</p>
          </div>
        </div>
        <input
          type="number"
          value={form.min_salary}
          onChange={(e) => setForm(prev => ({ ...prev, min_salary: e.target.value }))}
          placeholder="e.g. 100000"
          className="w-full px-4 py-2.5 bg-secondary border border-border/50 rounded-xl text-sm text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary/50 outline-none transition-all"
        />
      </div>

      {/* Match Score Threshold */}
      <div className="bg-card rounded-2xl border border-border/50 p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-violet-400/10 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-violet-400" />
            </div>
            <div>
              <label className="text-sm font-semibold text-foreground">Minimum Match Score</label>
              <p className="text-xs text-muted-foreground">Only apply to jobs matching this threshold</p>
            </div>
          </div>
          <span className="text-2xl font-bold text-primary">{form.min_match_score}%</span>
        </div>
        <div className="relative pt-2">
          <input
            type="range"
            min="0"
            max="100"
            step="5"
            value={form.min_match_score}
            onChange={(e) => setForm(prev => ({ ...prev, min_match_score: parseInt(e.target.value) }))}
            className="w-full h-2 bg-secondary rounded-full appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary [&::-webkit-slider-thumb]:shadow-lg [&::-webkit-slider-thumb]:shadow-primary/30 [&::-webkit-slider-thumb]:cursor-pointer"
          />
          <div className="flex justify-between text-xs text-muted-foreground mt-2">
            <span>0%</span>
            <span>50%</span>
            <span>100%</span>
          </div>
        </div>
      </div>
    </div>
  );
}
