"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  MapPin, Clock, Building2, ExternalLink, Bookmark, X, Loader2, Check,
  Briefcase, GraduationCap, Users, Globe, Zap,
  ChevronRight, TrendingUp, AlertCircle, CheckCircle2, XCircle,
  DollarSign, Star, Award, Target, Layers, ArrowUpRight,
  Calendar, CircleDot, Sparkles
} from "lucide-react";
import { Job } from "@/types/job";
import { formatDate, formatCurrency, cn } from "@/lib/utils";
import { JOB_TYPES, EXPERIENCE_LEVELS, PLATFORMS } from "@/lib/constants";
import { api } from "@/lib/api";
import { useToast } from "@/providers/toast-provider";

interface JobDetailsProps {
  job: Job;
}

export function JobDetails({ job }: JobDetailsProps) {
  const { addToast } = useToast();
  const queryClient = useQueryClient();
  const [isSaved, setIsSaved] = useState(false);

  const applyMutation = useMutation({
    mutationFn: () => api.post(`/jobs/${job.id}/apply`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      addToast({ title: "Application submitted!", variant: "success" });
    },
    onError: (error: any) => {
      const statusCode = error?.response?.status;
      const message = error?.response?.data?.message || error?.response?.data?.detail || "Failed to apply";
      if (statusCode === 429) {
        addToast({ title: "Application Limit Reached", description: message, variant: "error" });
      } else {
        addToast({ title: message, variant: "error" });
      }
    },
  });

  const saveMutation = useMutation({
    mutationFn: () => api.post(`/jobs/${job.id}/save`),
    onSuccess: () => {
      setIsSaved(true);
      addToast({ title: "Job saved!", variant: "success" });
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || "Failed to save job";
      addToast({ title: message, variant: "error" });
    },
  });

  const skipMutation = useMutation({
    mutationFn: () => api.post(`/jobs/${job.id}/skip`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      addToast({ title: "Job skipped", variant: "success" });
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || "Failed to skip job";
      addToast({ title: message, variant: "error" });
    },
  });

  const formatSalary = () => {
    if (job.salary_text) return job.salary_text;
    if (!job.salary_min && !job.salary_max) return null;
    const currency = job.salary_currency || "INR";
    const min = job.salary_min ? formatCurrency(job.salary_min, currency) : null;
    const max = job.salary_max ? formatCurrency(job.salary_max, currency) : null;
    if (min && max) return `${min} - ${max}`;
    if (min) return `From ${min}`;
    if (max) return `Up to ${max}`;
    return null;
  };

  const salary = formatSalary();
  const requiredSkills = job.skills || [];
  const preferredSkills = job.preferred_skills || [];
  const hasDescription = job.description && job.description.length > 20;
  const matchScore = job.match_score || 0;

  const getScoreColor = (score: number) => {
    if (score >= 80) return { bg: "bg-emerald-500/10", text: "text-emerald-400", bar: "bg-emerald-500", border: "border-emerald-500/20" };
    if (score >= 60) return { bg: "bg-blue-500/10", text: "text-blue-400", bar: "bg-blue-500", border: "border-blue-500/20" };
    if (score >= 40) return { bg: "bg-amber-500/10", text: "text-amber-400", bar: "bg-amber-500", border: "border-amber-500/20" };
    return { bg: "bg-zinc-500/10", text: "text-zinc-400", bar: "bg-zinc-500", border: "border-zinc-500/20" };
  };

  const scoreColors = getScoreColor(matchScore);

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Hero Header */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-zinc-900 via-zinc-900 to-zinc-800 border border-zinc-800">
        {/* Subtle gradient accent */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-bl from-emerald-500/5 via-transparent to-transparent" />
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-gradient-to-tr from-blue-500/5 via-transparent to-transparent" />

        <div className="relative p-8">
          <div className="flex items-start justify-between gap-6">
            {/* Left: Company Info */}
            <div className="flex items-start gap-5 flex-1 min-w-0">
              <div className="w-16 h-16 bg-zinc-800/80 rounded-2xl flex items-center justify-center flex-shrink-0 border border-zinc-700/50 backdrop-blur-sm">
                {job.company_logo ? (
                  <img src={job.company_logo} alt={job.company} className="w-12 h-12 rounded-xl object-contain" />
                ) : (
                  <span className="text-2xl font-bold text-zinc-300">
                    {(job.company || "J").charAt(0).toUpperCase()}
                  </span>
                )}
              </div>
              <div className="min-w-0">
                <h1 className="text-2xl font-bold text-zinc-50 leading-tight">{job.title}</h1>
                <div className="mt-1.5 flex items-center gap-2">
                  <span className="text-lg text-zinc-400 font-medium">{job.company}</span>
                  {job.source && (
                    <span className="text-xs px-2 py-0.5 rounded-md bg-zinc-800 text-zinc-500 border border-zinc-700/50">
                      via {PLATFORMS[job.source] || job.source}
                    </span>
                  )}
                </div>

                {/* Meta Row */}
                <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2.5 text-sm text-zinc-400">
                  <span className="flex items-center gap-1.5">
                    <MapPin className="w-4 h-4 text-zinc-500" />
                    {job.location || "Location not specified"}
                  </span>
                  {job.is_remote && (
                    <span className="flex items-center gap-1.5 text-emerald-400">
                      <Globe className="w-4 h-4" />
                      Remote
                    </span>
                  )}
                  {(job.posted_date || job.posted_at) && (
                    <span className="flex items-center gap-1.5">
                      <Calendar className="w-4 h-4 text-zinc-500" />
                      Posted {formatDate(job.posted_date || job.posted_at)}
                    </span>
                  )}
                  {job.applicant_count != null && job.applicant_count > 0 && (
                    <span className="flex items-center gap-1.5">
                      <Users className="w-4 h-4 text-zinc-500" />
                      {job.applicant_count} applicant{job.applicant_count !== 1 ? "s" : ""}
                    </span>
                  )}
                </div>

                {/* Tags Row */}
                <div className="mt-4 flex flex-wrap gap-2">
                  {job.job_type && (
                    <span className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg bg-zinc-800/80 text-zinc-300 border border-zinc-700/50">
                      <Briefcase className="w-3.5 h-3.5 text-zinc-500" />
                      {JOB_TYPES[job.job_type] || job.job_type}
                    </span>
                  )}
                  {job.experience_level && (
                    <span className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg bg-zinc-800/80 text-zinc-300 border border-zinc-700/50">
                      <GraduationCap className="w-3.5 h-3.5 text-zinc-500" />
                      {EXPERIENCE_LEVELS[job.experience_level] || job.experience_level}
                    </span>
                  )}
                  {job.is_easy_apply && (
                    <span className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
                      <Zap className="w-3.5 h-3.5" />
                      Easy Apply
                    </span>
                  )}
                  {salary && (
                    <span className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      <DollarSign className="w-3.5 h-3.5" />
                      {salary}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Right: Match Score */}
            {matchScore > 0 && (
              <div className="flex-shrink-0">
                <div className={cn(
                  "relative w-24 h-24 rounded-2xl flex flex-col items-center justify-center border",
                  scoreColors.bg, scoreColors.border
                )}>
                  <span className={cn("text-3xl font-bold tabular-nums", scoreColors.text)}>
                    {matchScore}
                  </span>
                  <span className="text-[10px] font-medium text-zinc-500 uppercase tracking-wider">
                    % match
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="mt-6 flex flex-wrap items-center gap-3 pt-6 border-t border-zinc-800">
            <button
              className={cn(
                "inline-flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold transition-all",
                applyMutation.isSuccess
                  ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                  : "bg-emerald-500 hover:bg-emerald-400 text-black shadow-lg shadow-emerald-500/20 hover:shadow-emerald-400/30"
              )}
              onClick={() => applyMutation.mutate()}
              disabled={applyMutation.isPending || applyMutation.isSuccess}
            >
              {applyMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : applyMutation.isSuccess ? (
                <Check className="w-4 h-4" />
              ) : (
                <Sparkles className="w-4 h-4" />
              )}
              {applyMutation.isSuccess ? "Queued for Apply" : "Apply Now"}
            </button>
            <button
              className={cn(
                "inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium border transition-all",
                isSaved
                  ? "border-amber-500/30 bg-amber-500/10 text-amber-400"
                  : "border-zinc-700 bg-zinc-800/50 text-zinc-300 hover:bg-zinc-800 hover:border-zinc-600"
              )}
              onClick={() => saveMutation.mutate()}
              disabled={saveMutation.isPending || isSaved}
            >
              {saveMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Bookmark className={cn("w-4 h-4", isSaved && "fill-current")} />
              )}
              {isSaved ? "Saved" : "Save"}
            </button>
            <button
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium border border-zinc-800 text-zinc-500 hover:text-red-400 hover:border-red-500/30 hover:bg-red-500/5 transition-all"
              onClick={() => skipMutation.mutate()}
              disabled={skipMutation.isPending}
            >
              {skipMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <X className="w-4 h-4" />
              )}
              Skip
            </button>
            {job.source_url && (
              <a
                href={job.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium text-zinc-500 hover:text-zinc-300 transition-all ml-auto"
              >
                View on {PLATFORMS[job.source] || "Source"}
                <ArrowUpRight className="w-4 h-4" />
              </a>
            )}
          </div>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Description & Requirements */}
        <div className="lg:col-span-2 space-y-6">
          {/* Job Description */}
          <div className="rounded-2xl bg-zinc-900/50 border border-zinc-800 overflow-hidden">
            <div className="px-6 py-4 border-b border-zinc-800/50">
              <h2 className="text-base font-semibold text-zinc-100 flex items-center gap-2">
                <Layers className="w-4 h-4 text-blue-400" />
                Job Description
              </h2>
            </div>
            <div className="px-6 py-5">
              {job.description_html ? (
                <div
                  className="prose prose-sm prose-invert max-w-none text-zinc-300
                    prose-headings:text-zinc-100 prose-headings:font-semibold
                    prose-strong:text-zinc-200
                    prose-li:text-zinc-300 prose-li:marker:text-zinc-600
                    prose-p:text-zinc-300 prose-p:leading-relaxed
                    prose-a:text-blue-400 prose-a:no-underline hover:prose-a:underline
                    prose-ul:space-y-1 prose-ol:space-y-1
                    prose-h2:text-lg prose-h2:mt-6 prose-h2:mb-3
                    prose-h3:text-base prose-h3:mt-5 prose-h3:mb-2"
                  dangerouslySetInnerHTML={{ __html: job.description_html }}
                />
              ) : hasDescription ? (
                <div className="text-sm text-zinc-300 leading-relaxed whitespace-pre-wrap">
                  {job.description}
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-zinc-800 flex items-center justify-center">
                    <Layers className="w-6 h-6 text-zinc-600" />
                  </div>
                  <p className="text-sm text-zinc-500">No description available</p>
                  {job.source_url && (
                    <a
                      href={job.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 mt-2 text-sm text-blue-400 hover:text-blue-300 transition-colors"
                    >
                      View full listing
                      <ArrowUpRight className="w-3.5 h-3.5" />
                    </a>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Requirements */}
          {job.requirements && job.requirements.length > 0 && (
            <div className="rounded-2xl bg-zinc-900/50 border border-zinc-800 overflow-hidden">
              <div className="px-6 py-4 border-b border-zinc-800/50">
                <h2 className="text-base font-semibold text-zinc-100 flex items-center gap-2">
                  <Target className="w-4 h-4 text-blue-400" />
                  Requirements
                </h2>
              </div>
              <div className="px-6 py-5">
                <ul className="space-y-3">
                  {job.requirements.map((req, i) => (
                    <li key={i} className="flex items-start gap-3 text-sm text-zinc-300">
                      <CircleDot className="w-4 h-4 text-blue-400/60 mt-0.5 flex-shrink-0" />
                      <span className="leading-relaxed">{req}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* Responsibilities */}
          {job.responsibilities && job.responsibilities.length > 0 && (
            <div className="rounded-2xl bg-zinc-900/50 border border-zinc-800 overflow-hidden">
              <div className="px-6 py-4 border-b border-zinc-800/50">
                <h2 className="text-base font-semibold text-zinc-100 flex items-center gap-2">
                  <Briefcase className="w-4 h-4 text-emerald-400" />
                  Responsibilities
                </h2>
              </div>
              <div className="px-6 py-5">
                <ul className="space-y-3">
                  {job.responsibilities.map((resp, i) => (
                    <li key={i} className="flex items-start gap-3 text-sm text-zinc-300">
                      <ChevronRight className="w-4 h-4 text-emerald-400/60 mt-0.5 flex-shrink-0" />
                      <span className="leading-relaxed">{resp}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* Qualifications */}
          {job.qualifications && job.qualifications.length > 0 && (
            <div className="rounded-2xl bg-zinc-900/50 border border-zinc-800 overflow-hidden">
              <div className="px-6 py-4 border-b border-zinc-800/50">
                <h2 className="text-base font-semibold text-zinc-100 flex items-center gap-2">
                  <GraduationCap className="w-4 h-4 text-amber-400" />
                  Qualifications
                </h2>
              </div>
              <div className="px-6 py-5">
                <ul className="space-y-3">
                  {job.qualifications.map((qual, i) => (
                    <li key={i} className="flex items-start gap-3 text-sm text-zinc-300">
                      <CircleDot className="w-4 h-4 text-amber-400/60 mt-0.5 flex-shrink-0" />
                      <span className="leading-relaxed">{qual}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* Nice to Have */}
          {job.nice_to_have && job.nice_to_have.length > 0 && (
            <div className="rounded-2xl bg-zinc-900/50 border border-zinc-800 overflow-hidden">
              <div className="px-6 py-4 border-b border-zinc-800/50">
                <h2 className="text-base font-semibold text-zinc-100 flex items-center gap-2">
                  <Star className="w-4 h-4 text-purple-400" />
                  Nice to Have
                </h2>
              </div>
              <div className="px-6 py-5">
                <ul className="space-y-3">
                  {job.nice_to_have.map((item, i) => (
                    <li key={i} className="flex items-start gap-3 text-sm text-zinc-300">
                      <Star className="w-4 h-4 text-purple-400/60 mt-0.5 flex-shrink-0" />
                      <span className="leading-relaxed">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>

        {/* Right Column - Sidebar */}
        <div className="space-y-5">
          {/* Match Analysis Card */}
          {matchScore > 0 && (
            <div className="rounded-2xl bg-zinc-900/50 border border-zinc-800 overflow-hidden">
              <div className="px-5 py-4 border-b border-zinc-800/50">
                <h3 className="text-sm font-semibold text-zinc-100 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-blue-400" />
                  Match Analysis
                </h3>
              </div>
              <div className="p-5 space-y-4">
                {/* Score Bar */}
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs font-medium text-zinc-500 uppercase tracking-wider">Overall Score</span>
                    <span className={cn("text-xl font-bold tabular-nums", scoreColors.text)}>
                      {matchScore}%
                    </span>
                  </div>
                  <div className="w-full bg-zinc-800 rounded-full h-2 overflow-hidden">
                    <div
                      className={cn("h-full rounded-full transition-all duration-500", scoreColors.bar)}
                      style={{ width: `${matchScore}%` }}
                    />
                  </div>
                </div>

                {job.match_reasoning && (
                  <p className="text-xs text-zinc-400 leading-relaxed p-3 rounded-lg bg-zinc-800/50 border border-zinc-800">
                    {job.match_reasoning}
                  </p>
                )}

                {/* Strengths */}
                {job.strengths && job.strengths.length > 0 && (
                  <div>
                    <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest mb-2">Strengths</p>
                    <ul className="space-y-1.5">
                      {job.strengths.map((s, i) => (
                        <li key={i} className="flex items-start gap-2 text-xs">
                          <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-emerald-400" />
                          <span className="text-zinc-300">{s}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Gaps */}
                {job.gaps && job.gaps.length > 0 && (
                  <div>
                    <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest mb-2">Gaps</p>
                    <ul className="space-y-1.5">
                      {job.gaps.map((g, i) => (
                        <li key={i} className="flex items-start gap-2 text-xs">
                          <AlertCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-amber-400" />
                          <span className="text-zinc-300">{g}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Skills Card */}
          {(requiredSkills.length > 0 || preferredSkills.length > 0) && (
            <div className="rounded-2xl bg-zinc-900/50 border border-zinc-800 overflow-hidden">
              <div className="px-5 py-4 border-b border-zinc-800/50">
                <h3 className="text-sm font-semibold text-zinc-100 flex items-center gap-2">
                  <Award className="w-4 h-4 text-blue-400" />
                  Skills
                </h3>
              </div>
              <div className="p-5 space-y-4">
                {requiredSkills.length > 0 && (
                  <div>
                    <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest mb-2.5">Required</p>
                    <div className="flex flex-wrap gap-1.5">
                      {requiredSkills.map((skill) => {
                        const isMatched = job.matched_skills?.some(
                          (ms) => ms.toLowerCase() === skill.toLowerCase()
                        );
                        return (
                          <span
                            key={skill}
                            className={cn(
                              "inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg border font-medium",
                              isMatched
                                ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                                : "border-zinc-700/50 bg-zinc-800/50 text-zinc-400"
                            )}
                          >
                            {isMatched && <CheckCircle2 className="w-3 h-3" />}
                            {skill}
                          </span>
                        );
                      })}
                    </div>
                  </div>
                )}
                {preferredSkills.length > 0 && (
                  <div>
                    <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest mb-2.5">Preferred</p>
                    <div className="flex flex-wrap gap-1.5">
                      {preferredSkills.map((skill) => (
                        <span key={skill} className="text-xs px-2.5 py-1 rounded-lg border border-zinc-800 bg-zinc-800/30 text-zinc-500">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {job.missing_skills && job.missing_skills.length > 0 && (
                  <div>
                    <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest mb-2.5">Skills Gap</p>
                    <div className="flex flex-wrap gap-1.5">
                      {job.missing_skills.map((skill) => (
                        <span key={skill} className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg border border-red-500/20 bg-red-500/5 text-red-400">
                          <XCircle className="w-3 h-3" />
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Compensation Card */}
          {salary && (
            <div className="rounded-2xl bg-zinc-900/50 border border-zinc-800 overflow-hidden">
              <div className="px-5 py-4 border-b border-zinc-800/50">
                <h3 className="text-sm font-semibold text-zinc-100 flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-emerald-400" />
                  Compensation
                </h3>
              </div>
              <div className="p-5">
                <div className="text-center py-3 px-4 rounded-xl bg-emerald-500/5 border border-emerald-500/10">
                  <p className="text-xl font-bold text-emerald-400">{salary}</p>
                  {job.salary_currency && (
                    <p className="text-xs text-zinc-500 mt-1">{job.salary_currency} per year</p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Benefits */}
          {job.benefits && job.benefits.length > 0 && (
            <div className="rounded-2xl bg-zinc-900/50 border border-zinc-800 overflow-hidden">
              <div className="px-5 py-4 border-b border-zinc-800/50">
                <h3 className="text-sm font-semibold text-zinc-100 flex items-center gap-2">
                  <Star className="w-4 h-4 text-amber-400" />
                  Benefits
                </h3>
              </div>
              <div className="p-5">
                <ul className="space-y-2">
                  {job.benefits.map((benefit, i) => (
                    <li key={i} className="flex items-start gap-2.5 text-xs text-zinc-300">
                      <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 text-emerald-400 flex-shrink-0" />
                      <span>{benefit}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* Company Info */}
          {(job.company || job.company_size || job.company_industry) && (
            <div className="rounded-2xl bg-zinc-900/50 border border-zinc-800 overflow-hidden">
              <div className="px-5 py-4 border-b border-zinc-800/50">
                <h3 className="text-sm font-semibold text-zinc-100 flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-zinc-400" />
                  Company
                </h3>
              </div>
              <div className="p-5">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-zinc-800/80 rounded-xl flex items-center justify-center border border-zinc-700/50">
                    {job.company_logo ? (
                      <img src={job.company_logo} alt="" className="w-7 h-7 rounded-lg object-contain" />
                    ) : (
                      <span className="text-sm font-bold text-zinc-400">
                        {(job.company || "J").charAt(0)}
                      </span>
                    )}
                  </div>
                  <div>
                    <p className="font-medium text-sm text-zinc-200">{job.company}</p>
                    {job.company_industry && (
                      <p className="text-xs text-zinc-500 mt-0.5">{job.company_industry}</p>
                    )}
                  </div>
                </div>
                {job.company_size && (
                  <div className="mt-3 flex items-center gap-2 text-xs text-zinc-500 pl-[52px]">
                    <Users className="w-3.5 h-3.5" />
                    {job.company_size}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
