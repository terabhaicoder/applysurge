"use client";

import Link from "next/link";
import { MapPin, Clock, Building2, Briefcase, Zap, Globe, DollarSign, GraduationCap } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MatchScoreBadge } from "./match-score-badge";
import { Job } from "@/types/job";
import { formatRelativeDate, formatCurrency, cn } from "@/lib/utils";
import { JOB_TYPES, EXPERIENCE_LEVELS, PLATFORMS } from "@/lib/constants";

interface JobCardProps {
  job: Job;
}

export function JobCard({ job }: JobCardProps) {
  const formatSalary = () => {
    if (job.salary_text) return job.salary_text;
    if (!job.salary_min && !job.salary_max) return null;
    const currency = job.salary_currency || "USD";
    const min = job.salary_min ? formatCurrency(job.salary_min, currency) : null;
    const max = job.salary_max ? formatCurrency(job.salary_max, currency) : null;
    if (min && max) return `${min} - ${max}`;
    if (min) return `${min}+`;
    if (max) return `Up to ${max}`;
    return null;
  };

  const salary = formatSalary();
  const skills = job.skills || [];

  return (
    <Link href={`/jobs/${job.id}`}>
      <Card className="hover:border-zinc-600 transition-all cursor-pointer border-zinc-800 bg-zinc-900/50 hover:bg-zinc-900/80">
        <CardContent className="p-5">
          {/* Top Row: Logo, Title, Score */}
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-start gap-3 min-w-0">
              <div className="w-11 h-11 bg-zinc-800 rounded-lg flex items-center justify-center flex-shrink-0 border border-zinc-700">
                <Building2 className="w-5 h-5 text-zinc-500" />
              </div>
              <div className="min-w-0">
                <h3 className="font-semibold text-zinc-100 text-sm leading-tight truncate">{job.title}</h3>
                <p className="text-sm text-zinc-400 truncate">{job.company}</p>
              </div>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              {job.match_score != null && job.match_score > 0 && (
                <MatchScoreBadge score={job.match_score} size="sm" />
              )}
            </div>
          </div>

          {/* Meta Row: Location, Time, Salary */}
          <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1.5 text-xs text-zinc-500">
            <span className="flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5" />
              <span className="truncate max-w-[160px]">{job.location || "Not specified"}</span>
            </span>
            {job.is_remote && (
              <span className="flex items-center gap-1 text-emerald-400">
                <Globe className="w-3.5 h-3.5" />
                Remote
              </span>
            )}
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              {formatRelativeDate(job.posted_date || job.posted_at)}
            </span>
            {salary && (
              <span className="flex items-center gap-1 text-emerald-400">
                <DollarSign className="w-3.5 h-3.5" />
                {salary}
              </span>
            )}
          </div>

          {/* Badges Row: Job Type, Experience, Easy Apply, Source */}
          <div className="mt-3 flex flex-wrap gap-1.5">
            {job.job_type && (
              <Badge variant="secondary" className="text-xs bg-zinc-800 text-zinc-300 border-zinc-700">
                <Briefcase className="w-3 h-3 mr-1" />
                {JOB_TYPES[job.job_type] || job.job_type}
              </Badge>
            )}
            {job.experience_level && (
              <Badge variant="secondary" className="text-xs bg-zinc-800 text-zinc-400 border-zinc-700">
                <GraduationCap className="w-3 h-3 mr-1" />
                {EXPERIENCE_LEVELS[job.experience_level] || job.experience_level}
              </Badge>
            )}
            {job.is_easy_apply && (
              <Badge className="text-xs bg-blue-500/10 text-blue-400 border-blue-500/20">
                <Zap className="w-3 h-3 mr-1" />
                Easy Apply
              </Badge>
            )}
            <Badge variant="outline" className="text-xs text-zinc-500 border-zinc-700">
              {PLATFORMS[job.source] || job.source}
            </Badge>
          </div>

          {/* Skills Row */}
          {skills.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1">
              {skills.slice(0, 4).map((skill) => (
                <Badge key={skill} variant="outline" className="text-[10px] px-1.5 py-0 text-zinc-400 border-zinc-700/50">
                  {skill}
                </Badge>
              ))}
              {skills.length > 4 && (
                <Badge variant="outline" className="text-[10px] px-1.5 py-0 text-zinc-500 border-zinc-700/50">
                  +{skills.length - 4} more
                </Badge>
              )}
            </div>
          )}

          {/* Description Preview - skip if it's just "About the job" */}
          {job.description && job.description.length > 30 && !job.description.toLowerCase().startsWith('about the job') && (
            <p className="mt-2.5 text-xs text-zinc-500 line-clamp-2 leading-relaxed">
              {job.description.substring(0, 150)}...
            </p>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}
