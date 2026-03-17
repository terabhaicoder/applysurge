"use client";

import { useState, useEffect, FormEvent } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { X, Plus, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { JOB_TYPES, EXPERIENCE_LEVELS } from "@/lib/constants";
import { api } from "@/lib/api";
import { useToast } from "@/providers/toast-provider";

interface Preferences {
  desired_titles: string[];
  desired_locations: string[];
  remote_preference: string;
  min_salary: number | null;
  max_salary: number | null;
  job_types: string[];
  experience_levels: string[];
  excluded_companies: string[];
  excluded_keywords: string[];
}

const defaultPrefs: Preferences = {
  desired_titles: [],
  desired_locations: [],
  remote_preference: "any",
  min_salary: null,
  max_salary: null,
  job_types: [],
  experience_levels: [],
  excluded_companies: [],
  excluded_keywords: [],
};

export function PreferencesForm() {
  const { addToast } = useToast();
  const queryClient = useQueryClient();

  const [prefs, setPrefs] = useState<Preferences>(defaultPrefs);
  const [titleInput, setTitleInput] = useState("");
  const [locationInput, setLocationInput] = useState("");
  const [companyInput, setCompanyInput] = useState("");
  const [keywordInput, setKeywordInput] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["preferences"],
    queryFn: () => api.get<Preferences>("/preferences/").then((r) => r.data),
  });

  useEffect(() => {
    if (data) {
      setPrefs({
        desired_titles: data.desired_titles || [],
        desired_locations: data.desired_locations || [],
        remote_preference: data.remote_preference || "any",
        min_salary: data.min_salary ?? null,
        max_salary: data.max_salary ?? null,
        job_types: data.job_types || [],
        experience_levels: data.experience_levels || [],
        excluded_companies: data.excluded_companies || [],
        excluded_keywords: data.excluded_keywords || [],
      });
    }
  }, [data]);

  const saveMutation = useMutation({
    mutationFn: (payload: Partial<Preferences>) =>
      api.put("/preferences/", payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["preferences"] });
      addToast({ title: "Preferences saved", variant: "success" });
    },
    onError: (error: any) => {
      const message =
        error?.response?.data?.detail || "Failed to save preferences";
      addToast({ title: message, variant: "error" });
    },
  });

  const toggleListItem = (
    field: keyof Pick<
      Preferences,
      "job_types" | "experience_levels"
    >,
    value: string
  ) => {
    setPrefs((prev) => {
      const list = prev[field];
      return {
        ...prev,
        [field]: list.includes(value)
          ? list.filter((v) => v !== value)
          : [...list, value],
      };
    });
  };

  const addToList = (
    field: keyof Pick<
      Preferences,
      "desired_titles" | "desired_locations" | "excluded_companies" | "excluded_keywords"
    >,
    value: string,
    setter: (v: string) => void
  ) => {
    const trimmed = value.trim();
    if (!trimmed) return;
    setPrefs((prev) => {
      if (prev[field].includes(trimmed)) return prev;
      return { ...prev, [field]: [...prev[field], trimmed] };
    });
    setter("");
  };

  const removeFromList = (
    field: keyof Pick<
      Preferences,
      "desired_titles" | "desired_locations" | "excluded_companies" | "excluded_keywords"
    >,
    value: string
  ) => {
    setPrefs((prev) => ({
      ...prev,
      [field]: prev[field].filter((v) => v !== value),
    }));
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    saveMutation.mutate(prefs);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12 text-muted-foreground">
        <Loader2 className="w-5 h-5 animate-spin mr-2" />
        Loading preferences...
      </div>
    );
  }

  return (
    <form className="max-w-2xl space-y-6" onSubmit={onSubmit}>
      {/* Desired Titles */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Desired Job Titles</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <Input
              value={titleInput}
              onChange={(e) => setTitleInput(e.target.value)}
              placeholder="e.g., Software Engineer"
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addToList("desired_titles", titleInput, setTitleInput);
                }
              }}
            />
            <Button
              type="button"
              variant="outline"
              size="icon"
              onClick={() =>
                addToList("desired_titles", titleInput, setTitleInput)
              }
            >
              <Plus className="w-4 h-4" />
            </Button>
          </div>
          {prefs.desired_titles.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {prefs.desired_titles.map((title) => (
                <Badge key={title} variant="secondary" className="gap-1">
                  {title}
                  <button
                    type="button"
                    onClick={() => removeFromList("desired_titles", title)}
                  >
                    <X className="w-3 h-3" />
                  </button>
                </Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Job Types */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Job Type Preferences</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {Object.entries(JOB_TYPES).map(([key, label]) => (
            <div key={key} className="flex items-center gap-2">
              <Checkbox
                id={`type-${key}`}
                checked={prefs.job_types.includes(key)}
                onCheckedChange={() => toggleListItem("job_types", key)}
              />
              <Label htmlFor={`type-${key}`} className="text-sm font-normal">
                {label}
              </Label>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Experience Levels */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Experience Level</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {Object.entries(EXPERIENCE_LEVELS).map(([key, label]) => (
            <div key={key} className="flex items-center gap-2">
              <Checkbox
                id={`level-${key}`}
                checked={prefs.experience_levels.includes(key)}
                onCheckedChange={() =>
                  toggleListItem("experience_levels", key)
                }
              />
              <Label htmlFor={`level-${key}`} className="text-sm font-normal">
                {label}
              </Label>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Locations & Salary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Location & Salary</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Preferred Locations</Label>
            <div className="flex gap-2">
              <Input
                value={locationInput}
                onChange={(e) => setLocationInput(e.target.value)}
                placeholder="e.g., San Francisco"
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addToList(
                      "desired_locations",
                      locationInput,
                      setLocationInput
                    );
                  }
                }}
              />
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={() =>
                  addToList(
                    "desired_locations",
                    locationInput,
                    setLocationInput
                  )
                }
              >
                <Plus className="w-4 h-4" />
              </Button>
            </div>
            {prefs.desired_locations.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {prefs.desired_locations.map((loc) => (
                  <Badge key={loc} variant="secondary" className="gap-1">
                    {loc}
                    <button
                      type="button"
                      onClick={() =>
                        removeFromList("desired_locations", loc)
                      }
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </div>
          <div className="flex items-center justify-between">
            <Label>Remote Only</Label>
            <Switch
              checked={prefs.remote_preference === "remote"}
              onCheckedChange={(checked) =>
                setPrefs((prev) => ({
                  ...prev,
                  remote_preference: checked ? "remote" : "any",
                }))
              }
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Min Salary</Label>
              <Input
                type="number"
                placeholder="e.g., 100000"
                value={prefs.min_salary ?? ""}
                onChange={(e) =>
                  setPrefs((prev) => ({
                    ...prev,
                    min_salary: e.target.value
                      ? parseInt(e.target.value, 10)
                      : null,
                  }))
                }
              />
            </div>
            <div className="space-y-2">
              <Label>Max Salary</Label>
              <Input
                type="number"
                placeholder="e.g., 200000"
                value={prefs.max_salary ?? ""}
                onChange={(e) =>
                  setPrefs((prev) => ({
                    ...prev,
                    max_salary: e.target.value
                      ? parseInt(e.target.value, 10)
                      : null,
                  }))
                }
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Excluded Companies */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Excluded Companies</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <Input
              value={companyInput}
              onChange={(e) => setCompanyInput(e.target.value)}
              placeholder="e.g., Company A"
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addToList(
                    "excluded_companies",
                    companyInput,
                    setCompanyInput
                  );
                }
              }}
            />
            <Button
              type="button"
              variant="outline"
              size="icon"
              onClick={() =>
                addToList(
                  "excluded_companies",
                  companyInput,
                  setCompanyInput
                )
              }
            >
              <Plus className="w-4 h-4" />
            </Button>
          </div>
          {prefs.excluded_companies.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {prefs.excluded_companies.map((co) => (
                <Badge key={co} variant="secondary" className="gap-1">
                  {co}
                  <button
                    type="button"
                    onClick={() => removeFromList("excluded_companies", co)}
                  >
                    <X className="w-3 h-3" />
                  </button>
                </Badge>
              ))}
            </div>
          )}
          <p className="text-xs text-muted-foreground">
            Companies to exclude from applications
          </p>
        </CardContent>
      </Card>

      {/* Excluded Keywords */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Excluded Keywords</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <Input
              value={keywordInput}
              onChange={(e) => setKeywordInput(e.target.value)}
              placeholder="e.g., unpaid, volunteer"
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addToList(
                    "excluded_keywords",
                    keywordInput,
                    setKeywordInput
                  );
                }
              }}
            />
            <Button
              type="button"
              variant="outline"
              size="icon"
              onClick={() =>
                addToList(
                  "excluded_keywords",
                  keywordInput,
                  setKeywordInput
                )
              }
            >
              <Plus className="w-4 h-4" />
            </Button>
          </div>
          {prefs.excluded_keywords.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {prefs.excluded_keywords.map((kw) => (
                <Badge key={kw} variant="secondary" className="gap-1">
                  {kw}
                  <button
                    type="button"
                    onClick={() => removeFromList("excluded_keywords", kw)}
                  >
                    <X className="w-3 h-3" />
                  </button>
                </Badge>
              ))}
            </div>
          )}
          <p className="text-xs text-muted-foreground">
            Job listings containing these keywords will be excluded
          </p>
        </CardContent>
      </Card>

      <Button type="submit" disabled={saveMutation.isPending}>
        {saveMutation.isPending ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin mr-2" />
            Saving...
          </>
        ) : (
          "Save Preferences"
        )}
      </Button>
    </form>
  );
}
