"use client";

import { LoginForm } from "@/components/auth/login-form";

export default function LoginPage() {
  return (
    <div>
      <div className="mb-8 text-center">
        <h1 className="font-display text-2xl font-bold text-foreground tracking-tight">
          Welcome back
        </h1>
        <p className="text-muted-foreground mt-1.5 text-sm">
          Sign in to your account to continue
        </p>
      </div>
      <LoginForm />
    </div>
  );
}
