"use client";

import { RegisterForm } from "@/components/auth/register-form";

export default function RegisterPage() {
  return (
    <div>
      <div className="mb-8 text-center">
        <h1 className="font-display text-2xl font-bold text-foreground tracking-tight">
          Create your account
        </h1>
        <p className="text-muted-foreground mt-1.5 text-sm">
          Get started with Apply Surge today
        </p>
      </div>
      <RegisterForm />
    </div>
  );
}
