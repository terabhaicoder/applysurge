"use client";

import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { setTokens } from "@/lib/auth";
import { useAuthStore } from "@/stores/auth-store";
import api from "@/lib/api";
import { User } from "@/types/user";
import { Loader2 } from "lucide-react";

function AuthCallbackPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setUser } = useAuthStore();

  useEffect(() => {
    const handleCallback = async () => {
      const accessToken = searchParams.get("access_token");
      const refreshToken = searchParams.get("refresh_token");
      const expiresIn = searchParams.get("expires_in");
      const error = searchParams.get("error");

      if (error) {
        router.push(`/login?error=${encodeURIComponent(error)}`);
        return;
      }

      if (!accessToken || !refreshToken) {
        router.push("/login?error=missing_tokens");
        return;
      }

      try {
        // Store tokens
        setTokens({
          access_token: accessToken,
          refresh_token: refreshToken,
          expires_in: parseInt(expiresIn || "1800", 10),
          token_type: "bearer",
        });

        // Fetch user data
        const userResponse = await api.get<User>("/auth/me");
        setUser(userResponse.data);

        // Redirect to dashboard
        router.push("/dashboard");
      } catch (err) {
        console.error("Auth callback error:", err);
        router.push("/login?error=auth_failed");
      }
    };

    handleCallback();
  }, [searchParams, router, setUser]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary mx-auto mb-4" />
        <p className="text-muted-foreground">Completing sign in...</p>
      </div>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>}>
      <AuthCallbackPageContent />
    </Suspense>
  );
}
