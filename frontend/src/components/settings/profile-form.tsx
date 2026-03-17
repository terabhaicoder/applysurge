"use client";

import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { profileSchema, ProfileFormData } from "@/lib/validations";
import { api } from "@/lib/api";
import { useToast } from "@/providers/toast-provider";
import { useAuthStore } from "@/stores/auth-store";

export function ProfileForm() {
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingData, setIsLoadingData] = useState(true);
  const { addToast } = useToast();
  const { user } = useAuthStore();
  const { register, handleSubmit, formState: { errors, isDirty }, reset } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      full_name: "",
      headline: "",
      summary: "",
      location: "",
      phone: "",
      linkedin_url: "",
      github_url: "",
      portfolio_url: "",
      current_company: "",
      current_title: "",
      years_of_experience: undefined,
    },
  });

  // Load existing profile data on mount
  useEffect(() => {
    const loadProfile = async () => {
      try {
        setIsLoadingData(true);
        const [profileRes] = await Promise.all([
          api.get("/profile/").catch(() => ({ data: null })),
        ]);

        const profile = profileRes.data;

        reset({
          full_name: user?.full_name || "",
          headline: profile?.headline || "",
          summary: profile?.summary || "",
          location: profile?.location || "",
          phone: profile?.phone || "",
          linkedin_url: profile?.linkedin_url || "",
          github_url: profile?.github_url || "",
          portfolio_url: profile?.portfolio_url || "",
          current_company: profile?.current_company || "",
          current_title: profile?.current_title || "",
          years_of_experience: profile?.years_of_experience ?? undefined,
        });
      } catch (error) {
        console.error("Failed to load profile:", error);
      } finally {
        setIsLoadingData(false);
      }
    };

    loadProfile();
  }, [user, reset]);

  const onSubmit = async (data: ProfileFormData) => {
    setIsLoading(true);
    try {
      // Only send fields that the backend ProfileUpdate schema accepts
      const profileData = {
        headline: data.headline || null,
        summary: data.summary || null,
        phone: data.phone || null,
        location: data.location || null,
        current_title: data.current_title || null,
        current_company: data.current_company || null,
        linkedin_url: data.linkedin_url || null,
        github_url: data.github_url || null,
        portfolio_url: data.portfolio_url || null,
        years_of_experience: data.years_of_experience ?? null,
      };

      // Update profile (use trailing slash to avoid 307 redirect)
      await api.patch("/profile/", profileData);

      // Update user's full_name if changed
      if (data.full_name && data.full_name !== user?.full_name) {
        await api.patch("/users/me", { full_name: data.full_name });
      }

      addToast({ title: "Profile saved successfully", variant: "success" });
    } catch (error: any) {
      console.error("Profile save error:", error);
      addToast({
        title: "Failed to save profile",
        description: error.response?.data?.detail || "Please try again",
        variant: "error"
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoadingData) {
    return (
      <div className="max-w-2xl space-y-6">
        <Card>
          <CardContent className="p-6">
            <div className="animate-pulse space-y-4">
              <div className="h-4 bg-secondary rounded w-1/4"></div>
              <div className="h-10 bg-secondary rounded"></div>
              <div className="h-4 bg-secondary rounded w-1/4"></div>
              <div className="h-10 bg-secondary rounded"></div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="max-w-2xl space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Personal Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="full_name">Full Name</Label>
              <Input id="full_name" {...register("full_name")} />
              {errors.full_name && <p className="text-sm text-red-600">{errors.full_name.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="phone">Phone</Label>
              <Input id="phone" {...register("phone")} />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="headline">Headline</Label>
            <Input id="headline" placeholder="e.g., Senior Software Engineer" {...register("headline")} />
          </div>

          <div className="space-y-2">
            <Label htmlFor="summary">Summary</Label>
            <Textarea id="summary" placeholder="Brief professional summary..." {...register("summary")} />
          </div>

          <div className="space-y-2">
            <Label htmlFor="location">Location</Label>
            <Input id="location" placeholder="e.g., San Francisco, CA" {...register("location")} />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="current_company">Current Company</Label>
              <Input id="current_company" {...register("current_company")} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="current_title">Current Title</Label>
              <Input id="current_title" {...register("current_title")} />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="years_of_experience">Years of Experience</Label>
            <Input
              id="years_of_experience"
              type="number"
              min={0}
              max={50}
              placeholder="e.g., 3"
              {...register("years_of_experience", { valueAsNumber: true })}
            />
            {errors.years_of_experience && (
              <p className="text-sm text-red-600">{errors.years_of_experience.message}</p>
            )}
            <p className="text-xs text-muted-foreground">
              Used for job filtering. The agent will only show jobs requiring{" "}
              <span className="font-medium text-foreground">&minus;1</span> to{" "}
              <span className="font-medium text-foreground">+2</span> years of your experience.
              {" "}For example, with 3 years you'll see jobs asking for 2&ndash;5 years.
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Social Links</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="linkedin_url">LinkedIn URL</Label>
            <Input id="linkedin_url" placeholder="https://linkedin.com/in/..." {...register("linkedin_url")} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="github_url">GitHub URL</Label>
            <Input id="github_url" placeholder="https://github.com/..." {...register("github_url")} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="portfolio_url">Portfolio URL</Label>
            <Input id="portfolio_url" placeholder="https://..." {...register("portfolio_url")} />
          </div>
        </CardContent>
      </Card>

      <Button type="submit" disabled={!isDirty || isLoading}>
        {isLoading ? "Saving..." : "Save Changes"}
      </Button>
    </form>
  );
}
