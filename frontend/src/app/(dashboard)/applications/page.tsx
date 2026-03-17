'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, FileText, ChevronRight, Filter, Calendar, Building2, MapPin } from 'lucide-react';
import Link from 'next/link';
import api from '@/lib/api';
import { cn } from '@/lib/utils';

const STATUS_OPTIONS = [
  { value: 'all', label: 'All' },
  { value: 'applied', label: 'Applied' },
  { value: 'response_received', label: 'Response' },
  { value: 'interview_scheduled', label: 'Interview' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'failed', label: 'Failed' },
];

const STATUS_CONFIG: Record<string, { bg: string; text: string; dot: string }> = {
  pending: { bg: 'bg-secondary', text: 'text-muted-foreground', dot: 'bg-muted-foreground' },
  in_progress: { bg: 'bg-amber-500/10', text: 'text-amber-500', dot: 'bg-amber-500' },
  applied: { bg: 'bg-blue-500/10', text: 'text-blue-500', dot: 'bg-blue-500' },
  response_received: { bg: 'bg-emerald-500/10', text: 'text-emerald-500', dot: 'bg-emerald-500' },
  interview_scheduled: { bg: 'bg-violet-500/10', text: 'text-violet-500', dot: 'bg-violet-500' },
  interviewing: { bg: 'bg-violet-500/10', text: 'text-violet-500', dot: 'bg-violet-500' },
  offer_received: { bg: 'bg-primary/10', text: 'text-primary', dot: 'bg-primary' },
  rejected: { bg: 'bg-red-500/10', text: 'text-red-500', dot: 'bg-red-500' },
  failed: { bg: 'bg-red-500/10', text: 'text-red-500', dot: 'bg-red-500' },
  withdrawn: { bg: 'bg-secondary', text: 'text-muted-foreground', dot: 'bg-muted-foreground' },
};

export default function ApplicationsPage() {
  const [status, setStatus] = useState('all');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ['applications', { status, search, page }],
    queryFn: () =>
      api.get('/applications', {
        params: { status: status !== 'all' ? status : undefined, search, page, page_size: 20 },
      }).then((r) => r.data),
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground tracking-tight">Applications</h1>
          <p className="text-muted-foreground text-sm mt-1">Track all your job applications</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-card border border-border/50">
          <FileText className="w-4 h-4 text-primary" />
          <span className="text-sm font-medium text-foreground">{data?.total || 0}</span>
          <span className="text-sm text-muted-foreground">total applications</span>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by job title, company..."
            className="w-full pl-11 pr-4 py-3 bg-card border border-border/50 rounded-xl text-sm text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary/50 outline-none transition-all"
          />
        </div>
        <div className="flex gap-1.5 overflow-x-auto pb-1 sm:pb-0 scrollbar-hide">
          {STATUS_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => { setStatus(opt.value); setPage(1); }}
              className={cn(
                'px-4 py-2.5 text-sm rounded-xl whitespace-nowrap font-medium transition-all',
                status === opt.value
                  ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/20'
                  : 'bg-card border border-border/50 text-muted-foreground hover:text-foreground hover:border-border'
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Applications Table */}
      <div className="bg-card rounded-2xl border border-border/50 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border/50">
                <th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider px-5 py-4">Job</th>
                <th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider px-5 py-4 hidden md:table-cell">Method</th>
                <th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider px-5 py-4">Status</th>
                <th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider px-5 py-4 hidden sm:table-cell">Date</th>
                <th className="text-right text-xs font-medium text-muted-foreground uppercase tracking-wider px-5 py-4"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/50">
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-secondary rounded-xl" />
                        <div className="space-y-2">
                          <div className="h-4 bg-secondary rounded w-32" />
                          <div className="h-3 bg-secondary/60 rounded w-24" />
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-4 hidden md:table-cell"><div className="h-4 bg-secondary rounded w-20" /></td>
                    <td className="px-5 py-4"><div className="h-6 bg-secondary rounded-full w-20" /></td>
                    <td className="px-5 py-4 hidden sm:table-cell"><div className="h-4 bg-secondary rounded w-20" /></td>
                    <td className="px-5 py-4"><div className="h-4 bg-secondary rounded w-8 ml-auto" /></td>
                  </tr>
                ))
              ) : (
                (data?.items || []).map((app: any) => {
                  const config = STATUS_CONFIG[app.status] || STATUS_CONFIG.pending;
                  return (
                    <tr key={app.id} className="group hover:bg-secondary/30 transition-colors">
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-secondary rounded-xl flex items-center justify-center flex-shrink-0">
                            <span className="text-sm font-semibold text-foreground">
                              {app.company_name?.charAt(0) || 'J'}
                            </span>
                          </div>
                          <div className="min-w-0">
                            <p className="text-sm font-medium text-foreground truncate">{app.job_title}</p>
                            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                              <span className="flex items-center gap-1 truncate">
                                <Building2 className="w-3 h-3" />
                                {app.company_name}
                              </span>
                              {app.job_location && (
                                <span className="flex items-center gap-1 truncate hidden lg:flex">
                                  <MapPin className="w-3 h-3" />
                                  {app.job_location}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-4 hidden md:table-cell">
                        <span className="text-xs text-muted-foreground capitalize px-2.5 py-1 bg-secondary rounded-lg">
                          {app.application_method?.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        <span className={cn('text-xs px-3 py-1.5 rounded-full font-medium inline-flex items-center gap-1.5', config.bg, config.text)}>
                          <span className={cn('w-1.5 h-1.5 rounded-full', config.dot)} />
                          {app.status?.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="px-5 py-4 hidden sm:table-cell">
                        <span className="text-xs text-muted-foreground flex items-center gap-1.5">
                          <Calendar className="w-3 h-3" />
                          {app.applied_at ? new Date(app.applied_at).toLocaleDateString() : '-'}
                        </span>
                      </td>
                      <td className="px-5 py-4 text-right">
                        <Link
                          href={`/applications/${app.id}`}
                          className="inline-flex items-center gap-1 text-muted-foreground hover:text-primary transition-colors text-sm font-medium"
                        >
                          View
                          <ChevronRight className="w-4 h-4 opacity-0 -translate-x-1 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
                        </Link>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {!isLoading && (!data?.items || data.items.length === 0) && (
          <div className="p-16 text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-secondary flex items-center justify-center">
              <FileText className="w-8 h-8 text-muted-foreground" />
            </div>
            <h3 className="font-semibold text-foreground mb-2">No applications yet</h3>
            <p className="text-sm text-muted-foreground max-w-sm mx-auto">
              Applications will appear here once the agent starts working
            </p>
          </div>
        )}
      </div>

      {/* Pagination */}
      {data?.total > 20 && (
        <div className="flex justify-center items-center gap-3">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="px-4 py-2 text-sm font-medium border border-border/50 rounded-xl hover:bg-secondary text-foreground disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Previous
          </button>
          <div className="flex items-center gap-2">
            <span className="px-4 py-2 text-sm font-medium bg-primary/10 text-primary rounded-xl">
              {page}
            </span>
            <span className="text-sm text-muted-foreground">of {Math.ceil(data.total / 20)}</span>
          </div>
          <button
            onClick={() => setPage(page + 1)}
            disabled={page >= Math.ceil(data.total / 20)}
            className="px-4 py-2 text-sm font-medium border border-border/50 rounded-xl hover:bg-secondary text-foreground disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
