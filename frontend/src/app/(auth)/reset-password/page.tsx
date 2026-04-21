"use client";

import { Suspense, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { CheckCircle2, XCircle, Eye, EyeOff, Loader2 } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { resetPasswordSchema, ResetPasswordFormData } from "@/lib/validations";

function ResetPasswordPageContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [status, setStatus] = useState<"form" | "success" | "error">("form");
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const { resetPassword } = useAuth();

  const { register, handleSubmit, formState: { errors } } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
  });

  const onSubmit = async (data: ResetPasswordFormData) => {
    if (!token) {
      setStatus("error");
      return;
    }
    setIsLoading(true);
    try {
      await resetPassword(token, data.password);
      setStatus("success");
    } catch {
      setStatus("error");
    } finally {
      setIsLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="text-center">
        <div className="w-16 h-16 bg-destructive/10 border border-destructive/20 rounded-2xl flex items-center justify-center mx-auto mb-5">
          <XCircle className="w-7 h-7 text-destructive" />
        </div>
        <h2 className="font-display text-2xl font-bold text-foreground mb-2">Invalid Link</h2>
        <p className="text-muted-foreground text-sm mb-8">This password reset link is invalid or has expired.</p>
        <Link
          href="/forgot-password"
          className="inline-flex items-center justify-center h-11 bg-secondary border border-border hover:bg-secondary/80 rounded-xl px-8 text-sm font-medium text-foreground transition-all duration-200"
        >
          Request New Link
        </Link>
      </div>
    );
  }

  if (status === "success") {
    return (
      <div className="text-center">
        <div className="w-16 h-16 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl flex items-center justify-center mx-auto mb-5">
          <CheckCircle2 className="w-7 h-7 text-emerald-500" />
        </div>
        <h2 className="font-display text-2xl font-bold text-foreground mb-2">Password Reset!</h2>
        <p className="text-muted-foreground text-sm mb-8">Your password has been successfully updated.</p>
        <Link
          href="/login"
          className="inline-flex items-center justify-center h-11 bg-primary hover:bg-primary/90 text-primary-foreground rounded-xl px-8 text-sm font-bold transition-all duration-200"
        >
          Sign In
        </Link>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="text-center">
        <div className="w-16 h-16 bg-destructive/10 border border-destructive/20 rounded-2xl flex items-center justify-center mx-auto mb-5">
          <XCircle className="w-7 h-7 text-destructive" />
        </div>
        <h2 className="font-display text-2xl font-bold text-foreground mb-2">Reset Failed</h2>
        <p className="text-muted-foreground text-sm mb-8">Something went wrong. The link may have expired.</p>
        <Link
          href="/forgot-password"
          className="inline-flex items-center justify-center h-11 bg-secondary border border-border hover:bg-secondary/80 rounded-xl px-8 text-sm font-medium text-foreground transition-all duration-200"
        >
          Request New Link
        </Link>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="font-display text-3xl font-bold text-foreground tracking-tight">Set new password</h1>
        <p className="text-muted-foreground mt-2 text-sm">Choose a strong password for your account</p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="space-y-1.5">
          <label htmlFor="password" className="block text-xs font-medium text-muted-foreground uppercase tracking-wider">
            New Password
          </label>
          <div className="relative">
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              placeholder="Min 8 characters"
              className="w-full h-11 bg-secondary/50 border border-border rounded-xl px-4 pr-10 text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:border-primary/40 focus:ring-1 focus:ring-primary/20 transition-all duration-200 hover:border-border/80"
              {...register("password")}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
          {errors.password && (
            <p className="text-xs text-destructive mt-1">{errors.password.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <label htmlFor="confirm_password" className="block text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Confirm Password
          </label>
          <input
            id="confirm_password"
            type="password"
            placeholder="Confirm your password"
            className="w-full h-11 bg-secondary/50 border border-border rounded-xl px-4 text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:border-primary/40 focus:ring-1 focus:ring-primary/20 transition-all duration-200 hover:border-border/80"
            {...register("confirm_password")}
          />
          {errors.confirm_password && (
            <p className="text-xs text-destructive mt-1">{errors.confirm_password.message}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full h-11 bg-primary hover:bg-primary/90 text-primary-foreground rounded-xl text-sm font-bold transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 mt-6"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Resetting...
            </>
          ) : (
            "Reset Password"
          )}
        </button>
      </form>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><Loader2 className="w-4 h-4 animate-spin text-primary" /></div>}>
      <ResetPasswordPageContent />
    </Suspense>
  );
}
