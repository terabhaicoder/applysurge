"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { Eye, EyeOff, Loader2, Check } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { registerSchema, RegisterFormData } from "@/lib/validations";

export function RegisterForm() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const { register: registerUser } = useAuth();

  const { register, handleSubmit, formState: { errors }, watch } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const password = watch("password", "");
  const passwordChecks = [
    { label: "8+ characters", met: password.length >= 8 },
    { label: "Contains number", met: /\d/.test(password) },
  ];

  const onSubmit = async (data: RegisterFormData) => {
    setIsLoading(true);
    setError("");
    try {
      await registerUser(data);
    } catch (err: unknown) {
      const apiError = err as { response?: { data?: { detail?: string } } };
      setError(apiError?.response?.data?.detail || "Registration failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {error && (
          <div className="bg-destructive/5 border border-destructive/15 text-destructive px-4 py-3 rounded-xl text-sm">
            {error}
          </div>
        )}

        <div className="space-y-1.5">
          <label htmlFor="full_name" className="block text-sm font-medium text-foreground">
            Full Name
          </label>
          <input
            id="full_name"
            placeholder="John Doe"
            className="w-full h-11 bg-background border border-border rounded-xl px-4 text-sm text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/40 transition-all duration-200"
            {...register("full_name")}
          />
          {errors.full_name && (
            <p className="text-xs text-destructive mt-1">{errors.full_name.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <label htmlFor="email" className="block text-sm font-medium text-foreground">
            Email
          </label>
          <input
            id="email"
            type="email"
            placeholder="you@example.com"
            className="w-full h-11 bg-background border border-border rounded-xl px-4 text-sm text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/40 transition-all duration-200"
            {...register("email")}
          />
          {errors.email && (
            <p className="text-xs text-destructive mt-1">{errors.email.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <label htmlFor="password" className="block text-sm font-medium text-foreground">
            Password
          </label>
          <div className="relative">
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              placeholder="Min 8 characters"
              className="w-full h-11 bg-background border border-border rounded-xl px-4 pr-10 text-sm text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/40 transition-all duration-200"
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
          {password.length > 0 && (
            <div className="flex items-center gap-3 mt-2">
              {passwordChecks.map((check, i) => (
                <div key={i} className="flex items-center gap-1.5">
                  <div className={`w-3.5 h-3.5 rounded-full flex items-center justify-center transition-colors ${check.met ? 'bg-indigo-500/20' : 'bg-muted'}`}>
                    {check.met && <Check className="w-2 h-2 text-indigo-500" />}
                  </div>
                  <span className={`text-[11px] transition-colors ${check.met ? 'text-muted-foreground' : 'text-muted-foreground/50'}`}>
                    {check.label}
                  </span>
                </div>
              ))}
            </div>
          )}
          {errors.password && (
            <p className="text-xs text-destructive mt-1">{errors.password.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <label htmlFor="confirm_password" className="block text-sm font-medium text-foreground">
            Confirm Password
          </label>
          <input
            id="confirm_password"
            type="password"
            placeholder="Confirm your password"
            className="w-full h-11 bg-background border border-border rounded-xl px-4 text-sm text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/40 transition-all duration-200"
            {...register("confirm_password")}
          />
          {errors.confirm_password && (
            <p className="text-xs text-destructive mt-1">{errors.confirm_password.message}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full h-11 bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-600 hover:to-violet-600 text-white rounded-xl text-sm font-semibold transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 mt-6 shadow-sm"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Creating account...
            </>
          ) : (
            "Create Account"
          )}
        </button>

        <p className="text-[11px] text-muted-foreground/60 text-center leading-relaxed">
          By creating an account, you agree to our{" "}
          <span className="text-muted-foreground hover:text-foreground cursor-pointer transition-colors">Terms</span>
          {" "}&{" "}
          <span className="text-muted-foreground hover:text-foreground cursor-pointer transition-colors">Privacy Policy</span>
        </p>
      </form>

      <p className="text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link href="/login" className="text-primary hover:text-primary/80 font-medium transition-colors">
          Sign in
        </Link>
      </p>
    </div>
  );
}
