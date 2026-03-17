'use client';

import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

interface SetupStatus {
  resumeUploaded: boolean;
  preferencesSet: boolean;
  linkedinConnected: boolean;
  isComplete: boolean;
  isLoading: boolean;
}

export function useSetupStatus(): SetupStatus {
  const { data: resumes, isLoading: loadingResumes } = useQuery({
    queryKey: ['resumes'],
    queryFn: () => api.get('/resumes/').then((r) => r.data),
    retry: false,
  });

  const { data: prefs, isLoading: loadingPrefs } = useQuery({
    queryKey: ['preferences'],
    queryFn: () => api.get('/preferences/').then((r) => r.data),
    retry: false,
  });

  const { data: credentials, isLoading: loadingCreds } = useQuery({
    queryKey: ['credentials'],
    queryFn: () => api.get('/credentials/').then((r) => r.data),
    retry: false,
  });

  const resumeUploaded = Array.isArray(resumes) ? resumes.length > 0 : (resumes?.items?.length > 0 || false);
  const preferencesSet = !!(prefs?.desired_titles?.length > 0);
  const linkedinConnected = Array.isArray(credentials) ? credentials.some((c: any) => c.platform === 'linkedin') : false;
  const isLoading = loadingResumes || loadingPrefs || loadingCreds;
  const isComplete = resumeUploaded && preferencesSet && linkedinConnected;

  return { resumeUploaded, preferencesSet, linkedinConnected, isComplete, isLoading };
}
