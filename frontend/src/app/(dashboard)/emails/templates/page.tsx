'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Edit2, Trash2, Mail, X, ArrowLeft, Sparkles, Loader2 } from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { api } from '@/lib/api';
import { useToast } from '@/providers/toast-provider';

const EMAIL_TEMPLATE_TYPES: Record<string, string> = {
  cold_outreach: 'Cold Outreach',
  follow_up: 'Follow Up',
  thank_you: 'Thank You',
  referral: 'Referral Request',
};

interface EmailTemplate {
  id: string;
  name: string;
  template_type: string;
  subject_template: string;
  body_template: string;
  is_default: boolean;
}

export default function EmailTemplatesPage() {
  const { addToast } = useToast();
  const queryClient = useQueryClient();
  const [showDialog, setShowDialog] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<EmailTemplate | null>(null);
  const [newTemplate, setNewTemplate] = useState({ name: '', template_type: 'cold_outreach', subject_template: '', body_template: '' });

  const { data: templates = [], isLoading } = useQuery({
    queryKey: ['email-templates'],
    queryFn: () => api.get<EmailTemplate[]>('/email/templates').then((r) => r.data),
  });

  const createMutation = useMutation({
    mutationFn: (data: typeof newTemplate) => api.post('/email/templates', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['email-templates'] });
      setShowDialog(false);
      setNewTemplate({ name: '', template_type: 'cold_outreach', subject_template: '', body_template: '' });
      addToast({ title: 'Template created', variant: 'success' });
    },
    onError: (error: any) => {
      addToast({ title: error.response?.data?.detail || 'Failed to create template', variant: 'error' });
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: { id: string } & typeof newTemplate) => api.put(`/email/templates/${data.id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['email-templates'] });
      setEditingTemplate(null);
      setShowDialog(false);
      setNewTemplate({ name: '', template_type: 'cold_outreach', subject_template: '', body_template: '' });
      addToast({ title: 'Template updated', variant: 'success' });
    },
    onError: (error: any) => {
      addToast({ title: error.response?.data?.detail || 'Failed to update template', variant: 'error' });
    },
  });

  const handleEdit = (template: EmailTemplate) => {
    setEditingTemplate(template);
    setNewTemplate({
      name: template.name,
      template_type: template.template_type,
      subject_template: template.subject_template,
      body_template: template.body_template,
    });
    setShowDialog(true);
  };

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/email/templates/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['email-templates'] });
      addToast({ title: 'Template deleted', variant: 'success' });
    },
    onError: () => {
      addToast({ title: 'Failed to delete template', variant: 'error' });
    },
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Link
            href="/emails"
            className="p-2 rounded-xl hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-foreground tracking-tight">Email Templates</h1>
            <p className="text-muted-foreground text-sm mt-1">Manage your email outreach templates</p>
          </div>
        </div>
        <button
          onClick={() => { setEditingTemplate(null); setNewTemplate({ name: '', template_type: 'cold_outreach', subject_template: '', body_template: '' }); setShowDialog(true); }}
          className="px-5 py-2.5 bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-medium rounded-xl flex items-center gap-2 transition-all shadow-lg shadow-primary/20 hover:shadow-primary/30"
        >
          <Plus className="w-4 h-4" />
          New Template
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-16 text-muted-foreground">
          <Loader2 className="w-5 h-5 animate-spin mr-2" />
          Loading templates...
        </div>
      ) : templates.length === 0 ? (
        <div className="text-center py-16">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-secondary flex items-center justify-center">
            <Mail className="w-8 h-8 text-muted-foreground" />
          </div>
          <h3 className="font-semibold text-foreground mb-2">No templates yet</h3>
          <p className="text-sm text-muted-foreground">Create your first email template to get started</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {templates.map((template) => (
            <div key={template.id} className="bg-card rounded-2xl border border-border/50 p-5 hover:border-border transition-all group">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-violet-400/10 rounded-xl flex items-center justify-center">
                    <Mail className="w-5 h-5 text-violet-400" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-foreground">{template.name}</h3>
                    <span className="text-xs text-muted-foreground px-2 py-0.5 bg-secondary rounded-full">
                      {EMAIL_TEMPLATE_TYPES[template.template_type] || template.template_type}
                    </span>
                  </div>
                </div>
                {template.is_default && (
                  <span className="text-xs px-2.5 py-1 bg-primary/10 text-primary rounded-full font-medium flex items-center gap-1">
                    <Sparkles className="w-3 h-3" />
                    Default
                  </span>
                )}
              </div>

              <div className="space-y-3 mb-4">
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Subject:</p>
                  <p className="text-sm text-foreground">{template.subject_template}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Preview:</p>
                  <p className="text-xs text-muted-foreground line-clamp-2">{template.body_template}</p>
                </div>
              </div>

              <div className="flex gap-2 pt-4 border-t border-border/50">
                <button
                  onClick={() => handleEdit(template)}
                  className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-sm font-medium text-foreground hover:bg-secondary rounded-xl transition-colors"
                >
                  <Edit2 className="w-3.5 h-3.5" />
                  Edit
                </button>
                <button
                  onClick={() => deleteMutation.mutate(template.id)}
                  disabled={deleteMutation.isPending}
                  className="px-3 py-2 text-red-400 hover:bg-red-400/10 rounded-xl transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Dialog */}
      {showDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setShowDialog(false)} />
          <div className="relative bg-card border border-border rounded-2xl w-full max-w-lg p-6 shadow-2xl animate-in fade-in-0 zoom-in-95">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-foreground">{editingTemplate ? 'Edit Email Template' : 'Create Email Template'}</h2>
              <button onClick={() => setShowDialog(false)} className="p-2 rounded-lg hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Template Name</label>
                <input
                  type="text"
                  value={newTemplate.name}
                  onChange={(e) => setNewTemplate((prev) => ({ ...prev, name: e.target.value }))}
                  placeholder="e.g., Initial Outreach"
                  className="w-full px-4 py-2.5 bg-secondary border border-border/50 rounded-xl text-sm text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary/50 outline-none transition-all"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Type</label>
                <select
                  value={newTemplate.template_type}
                  onChange={(e) => setNewTemplate((prev) => ({ ...prev, template_type: e.target.value }))}
                  className="w-full px-4 py-2.5 bg-secondary border border-border/50 rounded-xl text-sm text-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary/50 outline-none transition-all"
                >
                  {Object.entries(EMAIL_TEMPLATE_TYPES).map(([key, label]) => (
                    <option key={key} value={key}>{label}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Subject</label>
                <input
                  type="text"
                  value={newTemplate.subject_template}
                  onChange={(e) => setNewTemplate((prev) => ({ ...prev, subject_template: e.target.value }))}
                  placeholder="Email subject line"
                  className="w-full px-4 py-2.5 bg-secondary border border-border/50 rounded-xl text-sm text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary/50 outline-none transition-all"
                />
                <p className="text-xs text-muted-foreground">Variables: {'{{name}}'}, {'{{company}}'}, {'{{job_title}}'}</p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Body</label>
                <textarea
                  value={newTemplate.body_template}
                  onChange={(e) => setNewTemplate((prev) => ({ ...prev, body_template: e.target.value }))}
                  placeholder="Write your email template..."
                  rows={5}
                  className="w-full px-4 py-2.5 bg-secondary border border-border/50 rounded-xl text-sm text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary/50 outline-none transition-all resize-none"
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowDialog(false)}
                className="flex-1 px-4 py-2.5 text-sm font-medium border border-border rounded-xl text-foreground hover:bg-secondary transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  if (editingTemplate) {
                    updateMutation.mutate({ id: editingTemplate.id, ...newTemplate });
                  } else {
                    createMutation.mutate(newTemplate);
                  }
                }}
                disabled={(editingTemplate ? updateMutation.isPending : createMutation.isPending) || !newTemplate.name || !newTemplate.subject_template}
                className="flex-1 px-4 py-2.5 bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-medium rounded-xl transition-all shadow-lg shadow-primary/20 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {(editingTemplate ? updateMutation.isPending : createMutation.isPending) ? 'Saving...' : editingTemplate ? 'Update Template' : 'Save Template'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
