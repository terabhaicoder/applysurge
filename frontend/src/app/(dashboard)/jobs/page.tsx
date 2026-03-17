'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, MapPin, Building2, Bookmark, ExternalLink, Briefcase, Sparkles, DollarSign, ChevronRight } from 'lucide-react';
import Link from 'next/link';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { cn } from '@/lib/utils';
import { useToast } from '@/providers/toast-provider';

export default function JobsPage() {
  const { addToast } = useToast();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [source, setSource] = useState('all');
  const [page, setPage] = useState(1);

  const bookmarkMutation = useMutation({
    mutationFn: (jobId: string) => api.post(`/jobs/${jobId}/save`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      addToast({ title: 'Job bookmarked', variant: 'success' });
    },
    onError: () => {
      addToast({ title: 'Failed to bookmark job', variant: 'error' });
    },
  });

  const { data, isLoading } = useQuery({
    queryKey: ['jobs', { search, source, page }],
    queryFn: () =>
      api.get('/jobs', { params: { search, source: source !== 'all' ? source : undefined, page, page_size: 20, sort_by: 'match_score', sort_order: 'desc' } }).then((r) => r.data),
  });

  const sources = [
    { value: 'all', label: 'All Sources' },
    { value: 'linkedin', label: 'LinkedIn' },
    { value: 'naukri', label: 'Naukri' },
    { value: 'startup_outreach', label: 'Startups' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground tracking-tight">Discovered Jobs</h1>
          <p className="text-muted-foreground text-sm mt-1">Jobs matched to your preferences by the agent</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-card border border-border/50">
          <Sparkles className="w-4 h-4 text-primary" />
          <span className="text-sm font-medium text-foreground">{data?.total || 0}</span>
          <span className="text-sm text-muted-foreground">jobs found</span>
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
            placeholder="Search jobs by title, company..."
            className="w-full pl-11 pr-4 py-3 bg-card border border-border/50 rounded-xl text-sm text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/20 focus:border-primary/50 outline-none transition-all"
          />
        </div>
        <div className="flex gap-1.5">
          {sources.map((s) => (
            <button
              key={s.value}
              onClick={() => { setSource(s.value); setPage(1); }}
              className={cn(
                'px-4 py-2.5 text-sm rounded-xl whitespace-nowrap font-medium transition-all',
                source === s.value
                  ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/20'
                  : 'bg-card border border-border/50 text-muted-foreground hover:text-foreground hover:border-border'
              )}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Jobs List */}
      <div className="space-y-3">
        {isLoading ? (
          Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="bg-card rounded-2xl border border-border/50 p-5 animate-pulse">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-secondary rounded-xl" />
                <div className="flex-1 space-y-3">
                  <div className="h-5 bg-secondary rounded w-1/3" />
                  <div className="h-4 bg-secondary/60 rounded w-1/4" />
                  <div className="h-3 bg-secondary/40 rounded w-full" />
                </div>
              </div>
            </div>
          ))
        ) : (
          (data?.items || []).map((job: any) => (
            <Link
              key={job.id}
              href={`/jobs/${job.id}`}
              className="block bg-card rounded-2xl border border-border/50 p-5 hover:border-border hover:shadow-lg hover:shadow-foreground/5 transition-all group"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-4 flex-1 min-w-0">
                  {/* Company Initial */}
                  <div className="w-12 h-12 bg-secondary rounded-xl flex items-center justify-center flex-shrink-0">
                    <span className="text-lg font-bold text-foreground">
                      {job.company?.charAt(0) || 'J'}
                    </span>
                  </div>

                  <div className="flex-1 min-w-0">
                    {/* Title & Match Score */}
                    <div className="flex items-start gap-2 mb-1.5 flex-wrap">
                      <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors">
                        {job.title}
                      </h3>
                      {job.match_score && (
                        <span className={cn(
                          'text-xs px-2.5 py-0.5 rounded-full font-medium flex items-center gap-1',
                          job.match_score >= 80 ? 'bg-emerald-500/10 text-emerald-500' :
                          job.match_score >= 60 ? 'bg-blue-500/10 text-blue-500' :
                          'bg-secondary text-muted-foreground'
                        )}>
                          <Sparkles className="w-3 h-3" />
                          {job.match_score}% match
                        </span>
                      )}
                    </div>

                    {/* Meta Info */}
                    <div className="flex items-center gap-4 text-sm text-muted-foreground mb-3 flex-wrap">
                      <span className="flex items-center gap-1.5">
                        <Building2 className="w-3.5 h-3.5" />
                        {job.company}
                      </span>
                      {job.location && (
                        <span className="flex items-center gap-1.5">
                          <MapPin className="w-3.5 h-3.5" />
                          {job.location}
                        </span>
                      )}
                      <span className="text-xs px-2 py-0.5 bg-secondary rounded-lg capitalize">
                        {job.source}
                      </span>
                    </div>

                    {/* Description Preview */}
                    {job.description && job.description.length > 30 && !job.description.toLowerCase().startsWith('about the job') && (
                      <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                        {job.description.slice(0, 200)}
                      </p>
                    )}

                    {/* Skills preview */}
                    {job.skills && job.skills.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mb-3">
                        {job.skills.slice(0, 5).map((skill: string) => (
                          <span key={skill} className="text-xs px-2 py-0.5 rounded-md bg-secondary/50 text-muted-foreground border border-border/30">
                            {skill}
                          </span>
                        ))}
                        {job.skills.length > 5 && (
                          <span className="text-xs px-2 py-0.5 text-muted-foreground">
                            +{job.skills.length - 5} more
                          </span>
                        )}
                      </div>
                    )}

                    {/* Salary */}
                    {job.salary_text && (
                      <p className="text-sm font-medium text-emerald-500 flex items-center gap-1.5">
                        <DollarSign className="w-3.5 h-3.5" />
                        {job.salary_text}
                      </p>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-1.5 flex-shrink-0">
                  <button
                    onClick={(e) => { e.preventDefault(); bookmarkMutation.mutate(job.id); }}
                    className="p-2.5 hover:bg-secondary rounded-xl text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <Bookmark className="w-4 h-4" />
                  </button>
                  <a
                    href={job.source_url}
                    target="_blank"
                    rel="noopener"
                    onClick={(e) => e.stopPropagation()}
                    className="p-2.5 hover:bg-secondary rounded-xl text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                  <ChevronRight className="w-5 h-5 text-muted-foreground opacity-0 group-hover:opacity-100 -translate-x-2 group-hover:translate-x-0 transition-all" />
                </div>
              </div>
            </Link>
          ))
        )}

        {!isLoading && (!data?.items || data.items.length === 0) && (
          <div className="text-center py-16 bg-card rounded-2xl border border-border/50">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-secondary flex items-center justify-center">
              <Briefcase className="w-8 h-8 text-muted-foreground" />
            </div>
            <h3 className="font-semibold text-foreground mb-2">No jobs found</h3>
            <p className="text-sm text-muted-foreground">Start the agent to discover matching jobs</p>
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
