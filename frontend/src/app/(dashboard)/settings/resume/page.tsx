'use client';

import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { ResumeUploader } from '@/components/settings/resume-uploader';
import { ResumeList } from '@/components/settings/resume-list';

export default function ResumeSettingsPage() {
  return (
    <div className="max-w-2xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          href="/settings"
          className="p-2 rounded-xl hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-foreground tracking-tight">Resume</h1>
          <p className="text-muted-foreground text-sm mt-1">Upload and manage your resumes</p>
        </div>
      </div>
      <div className="space-y-6">
        <ResumeUploader />
        <ResumeList />
      </div>
    </div>
  );
}
