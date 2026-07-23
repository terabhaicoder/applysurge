'use client';

import { useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  FileUp,
  SlidersHorizontal,
  Link2,
  Rocket,
  Plus,
  X,
  Shield,
  Check,
  Eye,
  EyeOff,
  Loader2,
  Upload,
  File,
  ChevronRight,
  User,
} from 'lucide-react';
import { LogoFull } from '@/components/ui/logo';
import api from '@/lib/api';
import { cn } from '@/lib/utils';
import { useToast } from '@/providers/toast-provider';
import Link from 'next/link';

const SETUP_DISMISSED_KEY = 'applysurge:setup_dismissed';

const REMOTE_OPTIONS = [
  { value: 'remote', label: 'Remote Only' },
  { value: 'hybrid', label: 'Hybrid' },
  { value: 'onsite', label: 'On-site' },
  { value: 'any', label: 'Any' },
] as const;

/* ---------- Tag Input --------------------------------------------------- */

function TagInput({
  tags,
  onChange,
  placeholder,
}: {
  tags: string[];
  onChange: (tags: string[]) => void;
  placeholder: string;
}) {
  const [input, setInput] = useState('');

  const addTag = () => {
    const trimmed = input.trim();
    if (trimmed && !tags.includes(trimmed)) {
      onChange([...tags, trimmed]);
    }
    setInput('');
  };

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') { e.preventDefault(); addTag(); }
          }}
          placeholder={placeholder}
          className="flex-1 bg-secondary border border-border/50 rounded-xl px-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50 transition-all"
        />
        <button
          type="button"
          onClick={addTag}
          disabled={!input.trim()}
          className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-primary/10 text-primary hover:bg-primary/20 disabled:opacity-30 disabled:cursor-not-allowed transition-all text-sm font-medium"
        >
          <Plus className="w-4 h-4" />
          Add
        </button>
      </div>
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {tags.map((tag) => (
            <span key={tag} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary/10 text-primary text-sm font-medium border border-primary/20">
              {tag}
              <button type="button" onClick={() => onChange(tags.filter((t) => t !== tag))} className="hover:text-primary/60 transition-colors">
                <X className="w-3.5 h-3.5" />
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

/* ---------- Section wrapper --------------------------------------------- */

function SetupSection({
  number,
  title,
  description,
  icon: Icon,
  done,
  children,
}: {
  number: number;
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  done: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-card rounded-2xl border border-border/50 overflow-hidden">
      <div className="flex items-center gap-4 px-6 py-5 border-b border-border/30">
        <div className={cn(
          'w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 transition-colors',
          done ? 'bg-emerald-500/10' : 'bg-primary/10'
        )}>
          {done ? <Check className="w-5 h-5 text-emerald-500" /> : <Icon className="w-5 h-5 text-primary" />}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-muted-foreground/60 uppercase tracking-wider">Step {number}</span>
            {done && <span className="text-[10px] font-medium text-emerald-500 bg-emerald-500/10 px-2 py-0.5 rounded-full">Done</span>}
          </div>
          <h3 className="font-semibold text-foreground text-lg">{title}</h3>
        </div>
      </div>
      <div className="px-6 py-5">
        <p className="text-sm text-muted-foreground mb-5">{description}</p>
        {children}
      </div>
    </div>
  );
}

/* ---------- Main Page --------------------------------------------------- */

export default function SetupPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

  /* -- resume state ------------------------------------------------------ */
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [resumeUploaded, setResumeUploaded] = useState(false);

  const { data: existingResumes } = useQuery({
    queryKey: ['resumes'],
    queryFn: () => api.get('/resumes/').then((r) => r.data),
  });
  const hasResume = resumeUploaded || (Array.isArray(existingResumes) ? existingResumes.length > 0 : (existingResumes?.items?.length > 0));

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', file.name.replace(/\.[^/.]+$/, ''));
      return api.post('/resumes/', formData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] });
      setResumeUploaded(true);
      addToast({ title: 'Resume uploaded', variant: 'success' });
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to upload resume';
      addToast({ title: message, variant: 'error' });
      setUploadedFileName(null);
    },
  });

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFileName(file.name);
      uploadMutation.mutate(file);
    }
  };

  /* -- preferences state ------------------------------------------------- */
  const [desiredTitles, setDesiredTitles] = useState<string[]>([]);
  const [desiredLocations, setDesiredLocations] = useState<string[]>([]);
  const [remotePreference, setRemotePreference] = useState('any');
  const [minMatchScore, setMinMatchScore] = useState(65);
  const [preferencesSet, setPreferencesSet] = useState(false);

  const prefsMutation = useMutation({
    mutationFn: () =>
      api.put('/preferences/', {
        desired_titles: desiredTitles,
        desired_locations: desiredLocations,
        remote_preference: remotePreference,
        min_match_score: minMatchScore,
      }),
    onSuccess: () => {
      setPreferencesSet(true);
      queryClient.invalidateQueries({ queryKey: ['preferences'] });
      addToast({ title: 'Preferences saved', variant: 'success' });
    },
    onError: () => addToast({ title: 'Failed to save preferences', variant: 'error' }),
  });

  /* -- linkedin state ---------------------------------------------------- */
  const [linkedinEmail, setLinkedinEmail] = useState('');
  const [linkedinPassword, setLinkedinPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [linkedinConnected, setLinkedinConnected] = useState(false);

  const { data: existingCreds } = useQuery({
    queryKey: ['credentials'],
    queryFn: () => api.get('/credentials/').then((r) => r.data),
  });
  const hasLinkedIn = linkedinConnected || (Array.isArray(existingCreds) && existingCreds.some((c: any) => c.platform === 'linkedin'));

  const linkedinMutation = useMutation({
    mutationFn: () =>
      api.post('/credentials/linkedin', { username: linkedinEmail, password: linkedinPassword }),
    onSuccess: () => {
      setLinkedinConnected(true);
      queryClient.invalidateQueries({ queryKey: ['credentials'] });
      addToast({ title: 'LinkedIn connected', variant: 'success' });
    },
    onError: () => addToast({ title: 'Failed to connect LinkedIn', variant: 'error' }),
  });

  /* -- profile state ----------------------------------------------------- */
  const [currentTitle, setCurrentTitle] = useState('');
  const [yearsOfExperience, setYearsOfExperience] = useState('');
  const [currentCompany, setCurrentCompany] = useState('');
  const [profileSet, setProfileSet] = useState(false);

  const { data: existingProfile } = useQuery({
    queryKey: ['profile'],
    queryFn: () => api.get('/profile/').then((r) => r.data),
  });
  const hasProfile = profileSet || Boolean(existingProfile?.current_title && existingProfile?.years_of_experience != null);

  const profileMutation = useMutation({
    mutationFn: () =>
      api.patch('/profile/', {
        current_title: currentTitle || null,
        years_of_experience: yearsOfExperience ? Number(yearsOfExperience) : null,
        current_company: currentCompany || null,
      }),
    onSuccess: () => {
      setProfileSet(true);
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      addToast({ title: 'Profile saved', variant: 'success' });
    },
    onError: () => addToast({ title: 'Failed to save profile', variant: 'error' }),
  });

  /* -- finish ------------------------------------------------------------ */
  const dismissAndGo = useCallback(() => {
    localStorage.setItem(SETUP_DISMISSED_KEY, '1');
    router.push('/dashboard');
  }, [router]);

  const allDone = hasResume && preferencesSet && hasLinkedIn;

  return (
    <div className="fixed inset-0 z-50 bg-background overflow-y-auto">
      {/* Background glow */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-[-10%] left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-primary/5 rounded-full blur-[120px]" />
      </div>

      <div className="relative min-h-screen flex flex-col items-center px-4 py-8 sm:py-12">
        {/* Logo */}
        <div className="w-full max-w-2xl mb-8">
          <Link href="/dashboard" onClick={() => localStorage.setItem(SETUP_DISMISSED_KEY, '1')}>
            <LogoFull iconSize={24} textClassName="text-lg" />
          </Link>
        </div>

        {/* Header */}
        <div className="w-full max-w-2xl text-center mb-10">
          <h1 className="text-3xl sm:text-4xl font-bold text-foreground">
            Get started with <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-500 to-violet-500">Apply Surge</span>
          </h1>
          <p className="text-muted-foreground mt-3 max-w-md mx-auto">
            Complete these 4 steps and your AI agent will start finding and applying to LinkedIn jobs for you.
          </p>
        </div>

        {/* Setup sections */}
        <div className="w-full max-w-2xl space-y-5 flex-1">

          {/* Step 1: Resume */}
          <SetupSection
            number={1}
            title="Upload Your Resume"
            description="Your resume is attached to LinkedIn Easy Apply applications automatically."
            icon={FileUp}
            done={hasResume}
          >
            {hasResume && !uploadMutation.isPending ? (
              <div className="flex items-center gap-3 p-3 bg-emerald-500/5 border border-emerald-500/20 rounded-xl">
                <File className="w-5 h-5 text-emerald-500" />
                <span className="text-sm text-foreground font-medium">
                  {uploadedFileName || 'Resume uploaded'}
                </span>
                <Check className="w-4 h-4 text-emerald-500 ml-auto" />
              </div>
            ) : uploadMutation.isPending ? (
              <div className="flex items-center justify-center gap-2 py-8 text-muted-foreground">
                <Loader2 className="w-5 h-5 animate-spin" />
                <span className="text-sm">Uploading {uploadedFileName}...</span>
              </div>
            ) : (
              <>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.doc,.docx"
                  className="hidden"
                  onChange={handleFileSelect}
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full border-2 border-dashed border-border hover:border-primary/40 rounded-xl p-8 text-center transition-all hover:bg-primary/[0.02] group"
                >
                  <Upload className="w-8 h-8 text-muted-foreground/60 group-hover:text-primary/60 mx-auto mb-2 transition-colors" />
                  <p className="text-sm font-medium text-foreground">Drop your resume here or click to browse</p>
                  <p className="text-xs text-muted-foreground mt-1">PDF or DOC, max 10MB</p>
                </button>
              </>
            )}
          </SetupSection>

          {/* Step 2: Preferences */}
          <SetupSection
            number={2}
            title="Set Job Preferences"
            description="Tell us what roles you're looking for so the agent finds the best matches."
            icon={SlidersHorizontal}
            done={preferencesSet}
          >
            <div className="space-y-5">
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">
                  Desired Job Titles <span className="text-primary">*</span>
                </label>
                <TagInput tags={desiredTitles} onChange={setDesiredTitles} placeholder="e.g. Software Engineer, Product Manager..." />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Preferred Locations</label>
                <TagInput tags={desiredLocations} onChange={setDesiredLocations} placeholder="e.g. Bangalore, Remote, New York..." />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Work Style</label>
                <div className="grid grid-cols-4 gap-2">
                  {REMOTE_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setRemotePreference(opt.value)}
                      className={cn(
                        'px-3 py-2.5 rounded-xl text-sm font-medium transition-all border',
                        remotePreference === opt.value
                          ? 'bg-primary/10 border-primary/30 text-primary'
                          : 'bg-secondary border-border/50 text-muted-foreground hover:bg-secondary/80 hover:text-foreground'
                      )}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-foreground">Minimum Match Score</label>
                  <span className="text-sm font-bold text-primary">{minMatchScore}%</span>
                </div>
                <input
                  type="range"
                  min={30}
                  max={95}
                  step={5}
                  value={minMatchScore}
                  onChange={(e) => setMinMatchScore(Number(e.target.value))}
                  className="w-full accent-primary h-2 bg-secondary rounded-full appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:bg-primary [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:shadow-lg [&::-webkit-slider-thumb]:shadow-primary/30 [&::-webkit-slider-thumb]:cursor-pointer"
                />
                <div className="flex justify-between text-xs text-muted-foreground/60">
                  <span>More jobs</span>
                  <span>Better matches</span>
                </div>
              </div>

              {!preferencesSet ? (
                <button
                  onClick={() => prefsMutation.mutate()}
                  disabled={prefsMutation.isPending || desiredTitles.length === 0}
                  className="w-full py-2.5 bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-medium rounded-xl flex items-center justify-center gap-2 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {prefsMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                  Save Preferences
                </button>
              ) : (
                <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-emerald-500/5 border border-emerald-500/20 text-emerald-500 text-sm">
                  <Check className="w-4 h-4" />
                  Preferences saved
                </div>
              )}
            </div>
          </SetupSection>

          {/* Step 3: LinkedIn */}
          <SetupSection
            number={3}
            title="Connect LinkedIn"
            description="Link your LinkedIn account so the agent can apply to jobs via Easy Apply."
            icon={Link2}
            done={hasLinkedIn}
          >
            {hasLinkedIn ? (
              <div className="flex items-center gap-3 p-3 bg-emerald-500/5 border border-emerald-500/20 rounded-xl">
                <Check className="w-5 h-5 text-emerald-500" />
                <span className="text-sm text-foreground font-medium">LinkedIn connected</span>
                {linkedinEmail && <span className="text-xs text-muted-foreground ml-auto">{linkedinEmail}</span>}
              </div>
            ) : (
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">LinkedIn Email</label>
                  <input
                    type="email"
                    value={linkedinEmail}
                    onChange={(e) => setLinkedinEmail(e.target.value)}
                    placeholder="you@example.com"
                    className="w-full bg-secondary border border-border/50 rounded-xl px-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50 transition-all"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">LinkedIn Password</label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={linkedinPassword}
                      onChange={(e) => setLinkedinPassword(e.target.value)}
                      placeholder="Your LinkedIn password"
                      className="w-full bg-secondary border border-border/50 rounded-xl px-4 py-2.5 pr-11 text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50 transition-all"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <div className="flex items-start gap-2.5 px-4 py-3 rounded-xl bg-amber-500/5 border border-amber-500/15 text-muted-foreground text-xs leading-relaxed">
                  <Shield className="w-4 h-4 mt-0.5 flex-shrink-0 text-amber-500/60" />
                  Your credentials are encrypted and stored securely. They are only used to automate Easy Apply on your behalf.
                </div>

                <button
                  onClick={() => linkedinMutation.mutate()}
                  disabled={linkedinMutation.isPending || !linkedinEmail.trim() || !linkedinPassword.trim()}
                  className="w-full py-2.5 bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-medium rounded-xl flex items-center justify-center gap-2 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {linkedinMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                  Connect LinkedIn
                </button>
              </div>
            )}
          </SetupSection>

          {/* Step 4: Profile */}
          <SetupSection
            number={4}
            title="Your Profile"
            description="Your title and experience help the agent answer screening questions and match you to the right roles."
            icon={User}
            done={hasProfile}
          >
            {hasProfile ? (
              <div className="flex items-center gap-3 p-3 bg-emerald-500/5 border border-emerald-500/20 rounded-xl">
                <Check className="w-5 h-5 text-emerald-500" />
                <span className="text-sm text-foreground font-medium">Profile saved</span>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">
                    Current Title <span className="text-primary">*</span>
                  </label>
                  <input
                    type="text"
                    value={currentTitle}
                    onChange={(e) => setCurrentTitle(e.target.value)}
                    placeholder="e.g. Software Engineer"
                    className="w-full bg-secondary border border-border/50 rounded-xl px-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50 transition-all"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">
                    Years of Experience <span className="text-primary">*</span>
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={50}
                    value={yearsOfExperience}
                    onChange={(e) => setYearsOfExperience(e.target.value)}
                    placeholder="e.g. 3"
                    className="w-full bg-secondary border border-border/50 rounded-xl px-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50 transition-all"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">
                    Current Company <span className="text-xs text-muted-foreground font-normal">(optional)</span>
                  </label>
                  <input
                    type="text"
                    value={currentCompany}
                    onChange={(e) => setCurrentCompany(e.target.value)}
                    placeholder="e.g. Acme Inc."
                    className="w-full bg-secondary border border-border/50 rounded-xl px-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50 transition-all"
                  />
                </div>

                <button
                  onClick={() => profileMutation.mutate()}
                  disabled={profileMutation.isPending || !currentTitle.trim() || !yearsOfExperience.trim()}
                  className="w-full py-2.5 bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-medium rounded-xl flex items-center justify-center gap-2 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {profileMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                  Save Profile
                </button>
              </div>
            )}
          </SetupSection>
        </div>

        {/* Bottom CTA */}
        <div className="w-full max-w-2xl mt-8 pt-6 border-t border-border/30">
          <div className="flex items-center justify-between">
            <button
              onClick={dismissAndGo}
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Skip to Dashboard
            </button>

            <button
              onClick={dismissAndGo}
              className={cn(
                'flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold transition-all',
                allDone
                  ? 'bg-gradient-to-r from-indigo-500 to-violet-500 text-white hover:from-indigo-600 hover:to-violet-600 shadow-lg shadow-indigo-500/20 hover:scale-[1.02]'
                  : 'bg-primary/10 text-primary hover:bg-primary/20'
              )}
            >
              {allDone ? 'Go to Dashboard' : 'Continue to Dashboard'}
              {allDone ? <Rocket className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
