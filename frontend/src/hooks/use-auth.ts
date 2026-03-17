"use client";

import { useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { setTokens, clearTokens } from "@/lib/auth";
import api from "@/lib/api";
import { ROUTES } from "@/lib/constants";
import { LoginFormData, RegisterFormData } from "@/lib/validations";
import { User } from "@/types/user";
import { AuthTokens } from "@/types/api";

const SETUP_DISMISSED_KEY = "applysurge:setup_dismissed";

async function checkSetupComplete(): Promise<boolean> {
  // If user previously dismissed setup, don't show it again
  if (typeof window !== "undefined" && localStorage.getItem(SETUP_DISMISSED_KEY)) {
    return true;
  }

  try {
    const [resumes, prefs, creds] = await Promise.all([
      api.get("/resumes/").then((r) => r.data).catch(() => []),
      api.get("/preferences/").then((r) => r.data).catch(() => null),
      api.get("/credentials/").then((r) => r.data).catch(() => []),
    ]);

    const hasResume = Array.isArray(resumes) ? resumes.length > 0 : (resumes?.items?.length > 0);
    const hasPrefs = prefs?.desired_titles?.length > 0;
    const hasLinkedIn = Array.isArray(creds) && creds.some((c: any) => c.platform === "linkedin");

    return !!(hasResume && hasPrefs && hasLinkedIn);
  } catch {
    // If checking fails, don't block — go to dashboard
    return true;
  }
}

export function useAuth() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, setUser, setLoading, logout: storeLogout } = useAuthStore();

  const login = useCallback(async (data: LoginFormData) => {
    const response = await api.post<AuthTokens>("/auth/login", data);
    setTokens(response.data);
    const userResponse = await api.get<User>("/auth/me");
    setUser(userResponse.data);

    const setupDone = await checkSetupComplete();
    router.push(setupDone ? ROUTES.DASHBOARD : ROUTES.SETUP);
  }, [router, setUser]);

  const register = useCallback(async (data: RegisterFormData) => {
    await api.post("/auth/register", {
      email: data.email,
      password: data.password,
      full_name: data.full_name,
    });
    router.push(ROUTES.VERIFY_EMAIL);
  }, [router]);

  const logout = useCallback(async () => {
    // Stop agent before clearing auth (best-effort, don't block logout)
    try {
      await api.post("/agent/stop");
    } catch {
      // Ignore - agent might not be running or auth already stale
    }
    clearTokens();
    storeLogout();
    router.push(ROUTES.LOGIN);
  }, [router, storeLogout]);

  const fetchUser = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get<User>("/auth/me");
      setUser(response.data);
    } catch {
      setUser(null);
    }
  }, [setUser, setLoading]);

  const googleLogin = useCallback(async (credential: string) => {
    const response = await api.post<AuthTokens>("/auth/google", { id_token: credential });
    setTokens(response.data);
    const userResponse = await api.get<User>("/auth/me");
    setUser(userResponse.data);

    const setupDone = await checkSetupComplete();
    router.push(setupDone ? ROUTES.DASHBOARD : ROUTES.SETUP);
  }, [router, setUser]);

  const forgotPassword = useCallback(async (email: string) => {
    await api.post("/auth/forgot-password", { email });
  }, []);

  const resetPassword = useCallback(async (token: string, password: string) => {
    await api.post("/auth/reset-password", { token, new_password: password });
    router.push(ROUTES.LOGIN);
  }, [router]);

  const verifyEmail = useCallback(async (token: string) => {
    await api.get(`/auth/verify-email/${token}`);
  }, []);

  return {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    fetchUser,
    googleLogin,
    forgotPassword,
    resetPassword,
    verifyEmail,
  };
}
