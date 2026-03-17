'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Sparkles,
  SlidersHorizontal,
  Link2,
  Rocket,
  ChevronRight,
  ChevronLeft,
  Plus,
  X,
  Shield,
  Check,
  Eye,
  EyeOff,
  Loader2,
} from 'lucide-react';
import { Mascot } from '@/components/ui/mascot';
import { LogoFull } from '@/components/ui/logo';
import api from '@/lib/api';
import { cn } from '@/lib/utils';
import { useToast } from '@/providers/toast-provider';
import Link from 'next/link';

/* -------------------------------------------------------------------------- */
/*  Constants                                                                 */
/* -------------------------------------------------------------------------- */

const SETUP_DISMISSED_KEY = 'applysurge:setup_dismissed';

const STEPS = [
  { label: 'Welcome', icon: Sparkles },
  { label: 'Preferences', icon: SlidersHorizontal },
  { label: 'LinkedIn', icon: Link2 },
  { label: 'Ready!', icon: Rocket },
] as const;

const REMOTE_OPTIONS = [
  { value: 'remote', label: 'Remote Only' },
  { value: 'hybrid', label: 'Hybrid' },
  { value: 'onsite', label: 'On-site' },
  { value: 'any', label: 'Any' },
] as const;

/* -------------------------------------------------------------------------- */
/*  Helper: Tag Input                                                         */
/* -------------------------------------------------------------------------- */

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

  const removeTag = (tag: string) => {
    onChange(tags.filter((t) => t !== tag));
  };

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              addTag();
            }
          }}
          placeholder={placeholder}
          className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-white/30 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all"
        />
        <button
          type="button"
          onClick={addTag}
          disabled={!input.trim()}
          className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-primary/20 text-primary hover:bg-primary/30 disabled:opacity-30 disabled:cursor-not-allowed transition-all text-sm font-medium"
        >
          <Plus className="w-4 h-4" />
          Add
        </button>
      </div>
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {tags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary/15 text-primary text-sm font-medium border border-primary/20"
            >
              {tag}
              <button
                type="button"
                onClick={() => removeTag(tag)}
                className="hover:text-white transition-colors"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Main Wizard Page                                                          */
/* -------------------------------------------------------------------------- */

export default function SetupPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  /* -- shared state -------------------------------------------------------- */
  const [currentStep, setCurrentStep] = useState(0);
  const [direction, setDirection] = useState<'forward' | 'back'>('forward');

  /* -- step 1: preferences ------------------------------------------------- */
  const [desiredTitles, setDesiredTitles] = useState<string[]>([]);
  const [desiredLocations, setDesiredLocations] = useState<string[]>([]);
  const [remotePreference, setRemotePreference] = useState('any');
  const [minMatchScore, setMinMatchScore] = useState(65);
  const [preferencesSet, setPreferencesSet] = useState(false);

  /* -- step 2: linkedin ---------------------------------------------------- */
  const [linkedinEmail, setLinkedinEmail] = useState('');
  const [linkedinPassword, setLinkedinPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [linkedinConnected, setLinkedinConnected] = useState(false);

  /* -- mutations ----------------------------------------------------------- */
  const prefsMutation = useMutation({
    mutationFn: async () => {
      await api.put('/preferences/', {
        desired_titles: desiredTitles,
        desired_locations: desiredLocations,
        remote_preference: remotePreference,
        min_match_score: minMatchScore,
      });
    },
    onSuccess: () => {
      setPreferencesSet(true);
      queryClient.invalidateQueries({ queryKey: ['preferences'] });
      addToast({ title: 'Preferences saved', variant: 'success' });
    },
    onError: () => {
      addToast({ title: 'Failed to save preferences', variant: 'error' });
    },
  });

  const linkedinMutation = useMutation({
    mutationFn: async () => {
      await api.post('/credentials/linkedin', {
        username: linkedinEmail,
        password: linkedinPassword,
      });
    },
    onSuccess: () => {
      setLinkedinConnected(true);
      queryClient.invalidateQueries({ queryKey: ['credentials'] });
      addToast({ title: 'LinkedIn connected', variant: 'success' });
    },
    onError: () => {
      addToast({ title: 'Failed to connect LinkedIn', variant: 'error' });
    },
  });

  /* -- navigation ---------------------------------------------------------- */
  const dismissAndGo = useCallback(() => {
    localStorage.setItem(SETUP_DISMISSED_KEY, '1');
    router.push('/dashboard');
  }, [router]);

  const goNext = useCallback(() => {
    setDirection('forward');
    setCurrentStep((s) => Math.min(s + 1, STEPS.length - 1));
  }, []);

  const goBack = useCallback(() => {
    setDirection('back');
    setCurrentStep((s) => Math.max(s - 1, 0));
  }, []);

  const handleSkip = useCallback(() => {
    goNext();
  }, [goNext]);

  /* -- step actions -------------------------------------------------------- */
  const handlePreferencesSave = useCallback(() => {
    if (!preferencesSet) {
      prefsMutation.mutate();
    } else {
      goNext();
    }
  }, [preferencesSet, prefsMutation, goNext]);

  const handleLinkedinConnect = useCallback(() => {
    if (!linkedinConnected) {
      linkedinMutation.mutate();
    } else {
      goNext();
    }
  }, [linkedinConnected, linkedinMutation, goNext]);

  /* -- step completeness --------------------------------------------------- */
  const isStepComplete = (step: number) => {
    switch (step) {
      case 0:
        return true; // Welcome is always "complete"
      case 1:
        return preferencesSet;
      case 2:
        return linkedinConnected;
      case 3:
        return true;
      default:
        return false;
    }
  };

  const canAdvance = (step: number) => {
    switch (step) {
      case 0:
        return true; // Welcome can always advance
      case 1:
        return desiredTitles.length > 0 || preferencesSet;
      case 2:
        return (linkedinEmail.trim() !== '' && linkedinPassword.trim() !== '') || linkedinConnected;
      case 3:
        return true;
      default:
        return false;
    }
  };

  const handleNextAction = () => {
    switch (currentStep) {
      case 0:
        goNext();
        break;
      case 1:
        handlePreferencesSave();
        break;
      case 2:
        handleLinkedinConnect();
        break;
      case 3:
        dismissAndGo();
        break;
    }
  };

  const getNextLabel = () => {
    if (currentStep === 3) return 'Go to Dashboard';
    if (currentStep === 0) return "Let's Go";
    if (currentStep === 1 && !preferencesSet) return 'Save & Continue';
    if (currentStep === 1 && preferencesSet) return 'Continue';
    if (currentStep === 2 && !linkedinConnected) return 'Connect & Continue';
    if (currentStep === 2 && linkedinConnected) return 'Continue';
    return 'Next';
  };

  const isLoading = prefsMutation.isPending || linkedinMutation.isPending;

  /* ---------------------------------------------------------------------- */
  /*  Render                                                                 */
  /* ---------------------------------------------------------------------- */

  return (
    <div className="fixed inset-0 z-50 bg-background overflow-y-auto">
      {/* Background glow */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-[-20%] left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-primary/5 rounded-full blur-[120px]" />
      </div>

      <div className="relative min-h-screen flex flex-col items-center px-4 py-8 sm:py-12">
        {/* Logo */}
        <div className="w-full max-w-2xl mb-10">
          <Link href="/dashboard" onClick={() => localStorage.setItem(SETUP_DISMISSED_KEY, '1')}>
            <LogoFull variant="onDark" iconSize={24} textClassName="text-lg" />
          </Link>
        </div>

        {/* Step indicator */}
        <div className="w-full max-w-2xl mb-10">
          <div className="flex items-center justify-between">
            {STEPS.map((step, idx) => {
              const Icon = step.icon;
              const isActive = idx === currentStep;
              const isDone = idx < currentStep || isStepComplete(idx);

              return (
                <div key={step.label} className="flex flex-col items-center flex-1">
                  <div className="flex items-center w-full">
                    {/* Connector line (left) */}
                    {idx > 0 && (
                      <div
                        className={cn(
                          'flex-1 h-[2px] transition-colors duration-300',
                          idx <= currentStep ? 'bg-primary/60' : 'bg-white/10'
                        )}
                      />
                    )}

                    {/* Step circle */}
                    <button
                      onClick={() => {
                        if (idx < currentStep) {
                          setDirection('back');
                          setCurrentStep(idx);
                        }
                      }}
                      disabled={idx > currentStep}
                      className={cn(
                        'relative flex items-center justify-center w-10 h-10 rounded-full border-2 transition-all duration-300 flex-shrink-0',
                        isActive &&
                          'border-primary bg-primary/20 text-primary scale-110 shadow-lg shadow-primary/20',
                        isDone && !isActive && 'border-primary/60 bg-primary/10 text-primary/80',
                        !isActive && !isDone && 'border-white/15 bg-white/5 text-white/30',
                        idx < currentStep && 'cursor-pointer hover:scale-105',
                        idx > currentStep && 'cursor-not-allowed'
                      )}
                    >
                      {isDone && !isActive ? (
                        <Check className="w-4 h-4" />
                      ) : (
                        <Icon className="w-4 h-4" />
                      )}
                    </button>

                    {/* Connector line (right) */}
                    {idx < STEPS.length - 1 && (
                      <div
                        className={cn(
                          'flex-1 h-[2px] transition-colors duration-300',
                          idx < currentStep ? 'bg-primary/60' : 'bg-white/10'
                        )}
                      />
                    )}
                  </div>

                  {/* Label */}
                  <span
                    className={cn(
                      'mt-2.5 text-xs font-medium transition-colors duration-300',
                      isActive ? 'text-primary' : isDone ? 'text-white/50' : 'text-white/25'
                    )}
                  >
                    {step.label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Step content */}
        <div className="w-full max-w-2xl flex-1">
          <div
            key={currentStep}
            className={cn(
              'animate-in fade-in duration-300',
              direction === 'forward' ? 'slide-in-from-right-4' : 'slide-in-from-left-4'
            )}
          >
            {/* ---- Step 0: Welcome ---- */}
            {currentStep === 0 && (
              <div className="space-y-8 text-center py-6">
                <div className="flex justify-center">
                  <Mascot mood="idle" size="xl" />
                </div>

                <div className="space-y-3">
                  <h1 className="text-3xl sm:text-4xl font-bold text-white">
                    Welcome to <span className="text-gradient">Apply Surge</span>
                  </h1>
                  <p className="text-white/50 max-w-md mx-auto text-lg leading-relaxed">
                    Let&apos;s get you set up in under 2 minutes. We&apos;ll configure your
                    job preferences and connect your LinkedIn account so the agent can start
                    applying for you.
                  </p>
                </div>

                <div className="flex flex-col items-center gap-3 pt-2">
                  <div className="grid grid-cols-3 gap-4 max-w-sm w-full text-left">
                    {[
                      { num: '1', text: 'Set your job preferences' },
                      { num: '2', text: 'Connect LinkedIn' },
                      { num: '3', text: 'Start applying' },
                    ].map((item) => (
                      <div key={item.num} className="flex flex-col items-center text-center gap-2 p-3 rounded-xl bg-white/[0.03] border border-white/5">
                        <span className="text-primary font-bold text-lg">{item.num}</span>
                        <span className="text-white/50 text-xs">{item.text}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* ---- Step 1: Preferences ---- */}
            {currentStep === 1 && (
              <div className="space-y-6">
                <div className="text-center space-y-2">
                  <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-primary/15 text-primary mb-2">
                    <SlidersHorizontal className="w-7 h-7" />
                  </div>
                  <h1 className="text-2xl font-bold text-white">Set Your Preferences</h1>
                  <p className="text-white/50 max-w-md mx-auto">
                    Tell us what kind of roles you&apos;re looking for so we can find the best matches.
                  </p>
                </div>

                <div className="space-y-5">
                  {/* Job titles */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-white/70">
                      Desired Job Titles <span className="text-primary">*</span>
                    </label>
                    <TagInput
                      tags={desiredTitles}
                      onChange={setDesiredTitles}
                      placeholder="e.g. Software Engineer, Product Manager..."
                    />
                  </div>

                  {/* Locations */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-white/70">
                      Preferred Locations
                    </label>
                    <TagInput
                      tags={desiredLocations}
                      onChange={setDesiredLocations}
                      placeholder="e.g. San Francisco, New York, Remote..."
                    />
                  </div>

                  {/* Remote preference */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-white/70">
                      Work Style
                    </label>
                    <div className="grid grid-cols-4 gap-2">
                      {REMOTE_OPTIONS.map((opt) => (
                        <button
                          key={opt.value}
                          type="button"
                          onClick={() => setRemotePreference(opt.value)}
                          className={cn(
                            'px-3 py-2.5 rounded-xl text-sm font-medium transition-all border',
                            remotePreference === opt.value
                              ? 'bg-primary/20 border-primary/40 text-primary'
                              : 'bg-white/5 border-white/10 text-white/50 hover:bg-white/10 hover:text-white/70'
                          )}
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Match score slider */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium text-white/70">
                        Minimum Match Score
                      </label>
                      <span className="text-sm font-bold text-primary">{minMatchScore}%</span>
                    </div>
                    <input
                      type="range"
                      min={30}
                      max={95}
                      step={5}
                      value={minMatchScore}
                      onChange={(e) => setMinMatchScore(Number(e.target.value))}
                      className="w-full accent-primary h-2 bg-white/10 rounded-full appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:bg-primary [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:shadow-lg [&::-webkit-slider-thumb]:shadow-primary/30 [&::-webkit-slider-thumb]:cursor-pointer"
                    />
                    <div className="flex justify-between text-xs text-white/25">
                      <span>More jobs</span>
                      <span>Better matches</span>
                    </div>
                  </div>
                </div>

                {preferencesSet && (
                  <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-green-500/10 border border-green-500/20 text-green-400 text-sm">
                    <Check className="w-4 h-4" />
                    Preferences saved successfully
                  </div>
                )}
              </div>
            )}

            {/* ---- Step 2: LinkedIn ---- */}
            {currentStep === 2 && (
              <div className="space-y-6">
                <div className="text-center space-y-2">
                  <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-primary/15 text-primary mb-2">
                    <Link2 className="w-7 h-7" />
                  </div>
                  <h1 className="text-2xl font-bold text-white">Connect LinkedIn</h1>
                  <p className="text-white/50 max-w-md mx-auto">
                    Link your LinkedIn account so we can apply to jobs on your behalf using Easy
                    Apply.
                  </p>
                </div>

                {linkedinConnected ? (
                  <div className="flex flex-col items-center gap-4 py-6">
                    <div className="flex items-center justify-center w-16 h-16 rounded-full bg-green-500/15 text-green-400">
                      <Check className="w-8 h-8" />
                    </div>
                    <div className="text-center">
                      <p className="text-white font-medium">LinkedIn Connected</p>
                      <p className="text-white/40 text-sm mt-1">{linkedinEmail}</p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-white/70">LinkedIn Email</label>
                      <input
                        type="email"
                        value={linkedinEmail}
                        onChange={(e) => setLinkedinEmail(e.target.value)}
                        placeholder="you@example.com"
                        className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-white/30 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all"
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium text-white/70">LinkedIn Password</label>
                      <div className="relative">
                        <input
                          type={showPassword ? 'text' : 'password'}
                          value={linkedinPassword}
                          onChange={(e) => setLinkedinPassword(e.target.value)}
                          placeholder="Your LinkedIn password"
                          className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 pr-11 text-sm text-white placeholder:text-white/30 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all"
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60 transition-colors"
                        >
                          {showPassword ? (
                            <EyeOff className="w-4 h-4" />
                          ) : (
                            <Eye className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                    </div>

                    <div className="flex items-start gap-2.5 px-4 py-3 rounded-xl bg-white/[0.03] border border-white/5 text-white/40 text-xs leading-relaxed">
                      <Shield className="w-4 h-4 mt-0.5 flex-shrink-0 text-primary/60" />
                      <span>
                        Your credentials are encrypted and stored securely. They&apos;re only used to
                        automate Easy Apply on your behalf and are never shared with third parties.
                      </span>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ---- Step 3: Ready ---- */}
            {currentStep === 3 && (
              <div className="space-y-8 text-center">
                <div className="flex justify-center">
                  <Mascot mood="celebrating" size="xl" />
                </div>

                <div className="space-y-2">
                  <h1 className="text-3xl font-bold text-white">You&apos;re All Set!</h1>
                  <p className="text-white/50 max-w-md mx-auto">
                    Apply Surge is ready to start finding and applying to jobs for you.
                  </p>
                </div>

                <div className="max-w-sm mx-auto space-y-3 text-left">
                  <div
                    className={cn(
                      'flex items-center gap-3 px-4 py-3 rounded-xl border',
                      preferencesSet
                        ? 'bg-green-500/10 border-green-500/20'
                        : 'bg-white/[0.03] border-white/10'
                    )}
                  >
                    <div
                      className={cn(
                        'flex items-center justify-center w-8 h-8 rounded-lg',
                        preferencesSet
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-white/10 text-white/30'
                      )}
                    >
                      {preferencesSet ? (
                        <Check className="w-4 h-4" />
                      ) : (
                        <SlidersHorizontal className="w-4 h-4" />
                      )}
                    </div>
                    <div>
                      <p
                        className={cn(
                          'text-sm font-medium',
                          preferencesSet ? 'text-green-400' : 'text-white/40'
                        )}
                      >
                        Preferences
                      </p>
                      <p className="text-xs text-white/30">
                        {preferencesSet
                          ? `${desiredTitles.length} title${desiredTitles.length !== 1 ? 's' : ''}, ${remotePreference}`
                          : 'Skipped'}
                      </p>
                    </div>
                  </div>

                  <div
                    className={cn(
                      'flex items-center gap-3 px-4 py-3 rounded-xl border',
                      linkedinConnected
                        ? 'bg-green-500/10 border-green-500/20'
                        : 'bg-white/[0.03] border-white/10'
                    )}
                  >
                    <div
                      className={cn(
                        'flex items-center justify-center w-8 h-8 rounded-lg',
                        linkedinConnected
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-white/10 text-white/30'
                      )}
                    >
                      {linkedinConnected ? (
                        <Check className="w-4 h-4" />
                      ) : (
                        <Link2 className="w-4 h-4" />
                      )}
                    </div>
                    <div>
                      <p
                        className={cn(
                          'text-sm font-medium',
                          linkedinConnected ? 'text-green-400' : 'text-white/40'
                        )}
                      >
                        LinkedIn
                      </p>
                      <p className="text-xs text-white/30">
                        {linkedinConnected ? linkedinEmail : 'Skipped'}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Bottom navigation */}
        <div className="w-full max-w-2xl mt-8 pt-6 border-t border-white/5">
          <div className="flex items-center justify-between">
            {/* Back button */}
            <div>
              {currentStep > 0 && currentStep < 3 && (
                <button
                  onClick={goBack}
                  className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-medium text-white/50 hover:text-white/80 hover:bg-white/5 transition-all"
                >
                  <ChevronLeft className="w-4 h-4" />
                  Back
                </button>
              )}
            </div>

            {/* Center: skip link */}
            <div>
              {currentStep === 0 ? (
                <button
                  onClick={dismissAndGo}
                  className="text-sm text-white/25 hover:text-white/50 transition-colors"
                >
                  Skip to Dashboard
                </button>
              ) : currentStep < 3 ? (
                <button
                  onClick={handleSkip}
                  className="text-sm text-white/25 hover:text-white/50 transition-colors"
                >
                  Skip this step
                </button>
              ) : null}
            </div>

            {/* Next / action button */}
            <div>
              <button
                onClick={handleNextAction}
                disabled={(!canAdvance(currentStep) && currentStep < 3) || isLoading}
                className={cn(
                  'flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold transition-all',
                  currentStep === 3
                    ? 'bg-primary text-white hover:bg-primary/90 hover:shadow-lg hover:shadow-primary/25 hover:scale-[1.02]'
                    : 'bg-primary text-white hover:bg-primary/90',
                  'disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:scale-100 disabled:hover:shadow-none'
                )}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    {getNextLabel()}
                    {currentStep < 3 ? (
                      <ChevronRight className="w-4 h-4" />
                    ) : (
                      <Rocket className="w-4 h-4" />
                    )}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
