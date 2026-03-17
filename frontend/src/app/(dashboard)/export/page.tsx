'use client';

import { useState } from 'react';
import { Download, FileSpreadsheet, FileText, FileJson, BarChart3, ChevronDown, Check, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import api from '@/lib/api';
import { useToast } from '@/providers/toast-provider';

export default function ExportPage() {
  const { addToast } = useToast();
  const [format, setFormat] = useState('csv');
  const [dateRange, setDateRange] = useState('all');
  const [formatOpen, setFormatOpen] = useState(false);
  const [dateOpen, setDateOpen] = useState(false);
  const [exporting, setExporting] = useState<string | null>(null);
  const [includes, setIncludes] = useState({
    notes: true,
    logs: true,
    scores: true,
  });

  const handleExport = async (dataType: string) => {
    setExporting(dataType);
    try {
      const response = await api.get(`/export/${dataType}`, {
        params: { format, date_range: dateRange, include_notes: includes.notes, include_logs: includes.logs, include_scores: includes.scores },
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${dataType}_export.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      addToast({ title: `${dataType} exported successfully`, variant: 'success' });
    } catch {
      addToast({ title: `Failed to export ${dataType}`, variant: 'error' });
    } finally {
      setExporting(null);
    }
  };

  const handleExportAll = async () => {
    for (const option of ['applications', 'jobs', 'emails', 'analytics']) {
      await handleExport(option);
    }
  };

  const exportOptions = [
    { id: 'applications', label: 'Applications', description: 'All job applications and their statuses', icon: FileText, color: 'text-blue-400', bg: 'bg-blue-400/10' },
    { id: 'jobs', label: 'Saved Jobs', description: 'Jobs discovered by the AI agent', icon: FileSpreadsheet, color: 'text-emerald-400', bg: 'bg-emerald-400/10' },
    { id: 'emails', label: 'Email Outreach', description: 'Email campaign data and responses', icon: FileText, color: 'text-violet-400', bg: 'bg-violet-400/10' },
    { id: 'analytics', label: 'Analytics Data', description: 'Response rates, charts, and statistics', icon: BarChart3, color: 'text-amber-400', bg: 'bg-amber-400/10' },
  ];

  const formatOptions = [
    { value: 'csv', label: 'CSV' },
    { value: 'xlsx', label: 'Excel (XLSX)' },
    { value: 'json', label: 'JSON' },
  ];

  const dateOptions = [
    { value: 'all', label: 'All Time' },
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' },
    { value: '90d', label: 'Last 90 Days' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground tracking-tight">Export Data</h1>
        <p className="text-muted-foreground text-sm mt-1">Download your data in various formats</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Export Options */}
        <div className="lg:col-span-2 space-y-3">
          {exportOptions.map((option) => (
            <div
              key={option.id}
              className="bg-card rounded-2xl border border-border/50 p-5 hover:border-border transition-all group"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={cn('w-11 h-11 rounded-xl flex items-center justify-center', option.bg)}>
                    <option.icon className={cn('w-5 h-5', option.color)} />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-foreground">{option.label}</h3>
                    <p className="text-xs text-muted-foreground">{option.description}</p>
                  </div>
                </div>
                <button
                  onClick={() => handleExport(option.id)}
                  disabled={exporting === option.id}
                  className="px-4 py-2 text-sm font-medium border border-border/50 rounded-xl hover:bg-secondary text-foreground flex items-center gap-2 transition-colors group-hover:border-primary/50 group-hover:text-primary disabled:opacity-50"
                >
                  {exporting === option.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                  {exporting === option.id ? 'Exporting...' : 'Export'}
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Export Settings */}
        <div className="bg-card rounded-2xl border border-border/50 p-5">
          <h2 className="text-lg font-semibold text-foreground mb-5">Export Settings</h2>

          <div className="space-y-5">
            {/* Format Dropdown */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Format</label>
              <div className="relative">
                <button
                  onClick={() => setFormatOpen(!formatOpen)}
                  className="w-full flex items-center justify-between px-4 py-2.5 bg-secondary border border-border/50 rounded-xl text-sm text-foreground hover:border-border transition-colors"
                >
                  <span>{formatOptions.find(f => f.value === format)?.label}</span>
                  <ChevronDown className={cn('w-4 h-4 text-muted-foreground transition-transform', formatOpen && 'rotate-180')} />
                </button>
                {formatOpen && (
                  <div className="absolute z-10 top-full left-0 right-0 mt-1 bg-card border border-border rounded-xl overflow-hidden shadow-xl">
                    {formatOptions.map((opt) => (
                      <button
                        key={opt.value}
                        onClick={() => { setFormat(opt.value); setFormatOpen(false); }}
                        className={cn(
                          'w-full px-4 py-2.5 text-sm text-left hover:bg-secondary transition-colors flex items-center justify-between',
                          format === opt.value ? 'text-primary' : 'text-foreground'
                        )}
                      >
                        {opt.label}
                        {format === opt.value && <Check className="w-4 h-4" />}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Date Range Dropdown */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Date Range</label>
              <div className="relative">
                <button
                  onClick={() => setDateOpen(!dateOpen)}
                  className="w-full flex items-center justify-between px-4 py-2.5 bg-secondary border border-border/50 rounded-xl text-sm text-foreground hover:border-border transition-colors"
                >
                  <span>{dateOptions.find(d => d.value === dateRange)?.label}</span>
                  <ChevronDown className={cn('w-4 h-4 text-muted-foreground transition-transform', dateOpen && 'rotate-180')} />
                </button>
                {dateOpen && (
                  <div className="absolute z-10 top-full left-0 right-0 mt-1 bg-card border border-border rounded-xl overflow-hidden shadow-xl">
                    {dateOptions.map((opt) => (
                      <button
                        key={opt.value}
                        onClick={() => { setDateRange(opt.value); setDateOpen(false); }}
                        className={cn(
                          'w-full px-4 py-2.5 text-sm text-left hover:bg-secondary transition-colors flex items-center justify-between',
                          dateRange === opt.value ? 'text-primary' : 'text-foreground'
                        )}
                      >
                        {opt.label}
                        {dateRange === opt.value && <Check className="w-4 h-4" />}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Include Checkboxes */}
            <div className="space-y-3">
              <label className="text-sm font-medium text-foreground">Include</label>
              <div className="space-y-2">
                {[
                  { key: 'notes', label: 'Notes' },
                  { key: 'logs', label: 'Activity Logs' },
                  { key: 'scores', label: 'Match Scores' },
                ].map((item) => (
                  <label key={item.key} className="flex items-center gap-3 cursor-pointer group">
                    <div
                      onClick={() => setIncludes(prev => ({ ...prev, [item.key]: !prev[item.key as keyof typeof prev] }))}
                      className={cn(
                        'w-5 h-5 rounded-md border flex items-center justify-center transition-all',
                        includes[item.key as keyof typeof includes]
                          ? 'bg-primary border-primary'
                          : 'border-border bg-secondary group-hover:border-border'
                      )}
                    >
                      {includes[item.key as keyof typeof includes] && (
                        <Check className="w-3 h-3 text-primary-foreground" />
                      )}
                    </div>
                    <span className="text-sm text-muted-foreground">{item.label}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Export All Button */}
            <button
              onClick={handleExportAll}
              disabled={!!exporting}
              className="w-full py-2.5 bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-medium rounded-xl flex items-center justify-center gap-2 transition-all shadow-lg shadow-primary/20 hover:shadow-primary/30 disabled:opacity-50"
            >
              {exporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
              {exporting ? 'Exporting...' : 'Export All'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
