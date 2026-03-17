"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Mail, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import api from "@/lib/api";

export default function VerifyEmailPage() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const { verifyEmail } = useAuth();
  const [status, setStatus] = useState<"pending" | "success" | "error">("pending");

  useEffect(() => {
    if (token) {
      verifyEmail(token)
        .then(() => setStatus("success"))
        .catch(() => setStatus("error"));
    }
  }, [token, verifyEmail]);

  if (token && status === "pending") {
    return (
      <div className="text-center">
        <div className="w-16 h-16 bg-secondary border border-border rounded-2xl flex items-center justify-center mx-auto mb-5">
          <Loader2 className="w-7 h-7 text-primary animate-spin" />
        </div>
        <h2 className="font-display text-2xl font-bold text-foreground mb-2">Verifying...</h2>
        <p className="text-muted-foreground text-sm">Please wait while we verify your email.</p>
      </div>
    );
  }

  if (token && status === "success") {
    return (
      <div className="text-center">
        <div className="w-16 h-16 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl flex items-center justify-center mx-auto mb-5">
          <CheckCircle2 className="w-7 h-7 text-emerald-500" />
        </div>
        <h2 className="font-display text-2xl font-bold text-foreground mb-2">Email Verified!</h2>
        <p className="text-muted-foreground text-sm mb-8">Your email has been successfully verified. You can now sign in.</p>
        <Link
          href="/login"
          className="inline-flex items-center justify-center h-11 bg-primary hover:bg-primary/90 text-primary-foreground rounded-xl px-8 text-sm font-bold transition-all duration-200"
        >
          Sign In
        </Link>
      </div>
    );
  }

  if (token && status === "error") {
    return (
      <div className="text-center">
        <div className="w-16 h-16 bg-destructive/10 border border-destructive/20 rounded-2xl flex items-center justify-center mx-auto mb-5">
          <XCircle className="w-7 h-7 text-destructive" />
        </div>
        <h2 className="font-display text-2xl font-bold text-foreground mb-2">Verification Failed</h2>
        <p className="text-muted-foreground text-sm mb-8">The verification link may have expired or is invalid.</p>
        <Link
          href="/login"
          className="inline-flex items-center justify-center h-11 bg-secondary border border-border hover:bg-secondary/80 rounded-xl px-8 text-sm font-medium text-foreground transition-all duration-200"
        >
          Back to Sign In
        </Link>
      </div>
    );
  }

  return (
    <div className="text-center">
      <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center mx-auto mb-5">
        <Mail className="w-7 h-7 text-primary" />
      </div>
      <h2 className="font-display text-2xl font-bold text-foreground mb-2">Check your email</h2>
      <p className="text-muted-foreground text-sm mb-6 leading-relaxed max-w-xs mx-auto">
        We&apos;ve sent a verification link to your email address. Please click the link to verify your account.
      </p>
      <p className="text-sm text-muted-foreground">
        Didn&apos;t receive the email?{" "}
        <button
          onClick={() => {
            api.post("/auth/resend-verification").then(() => {
              alert("Verification email resent. Please check your inbox.");
            }).catch(() => {
              alert("Failed to resend verification email. Please try again.");
            });
          }}
          className="text-primary hover:text-primary/80 font-medium transition-colors"
        >
          Resend verification
        </button>
      </p>
      <div className="mt-8 pt-6 border-t border-border">
        <Link href="/login" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
          Back to sign in
        </Link>
      </div>
    </div>
  );
}
