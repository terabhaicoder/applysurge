'use client';

import { FileUp } from 'lucide-react';
import { ResumeUploader } from '@/components/settings/resume-uploader';
import { ResumeList } from '@/components/settings/resume-list';

export default function ResumePage() {
  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <div className="flex items-center gap-3 mb-1">
          <div className="w-9 h-9 rounded-lg bg-violet-500/10 flex items-center justify-center">
            <FileUp className="w-4 h-4 text-violet-400" />
          </div>
          <h1 className="text-2xl font-bold text-foreground tracking-tight">Resume</h1>
        </div>
        <p className="text-muted-foreground text-sm mt-1 ml-12">Upload and manage your resumes for applications</p>
      </div>
      <div className="space-y-6">
        <ResumeUploader />
        <ResumeList />
      </div>
    </div>
  );
}
