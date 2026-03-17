"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { FileUpload } from "@/components/common/file-upload";
import { useToast } from "@/providers/toast-provider";
import { api } from "@/lib/api";
import { Loader2 } from "lucide-react";

export function ResumeUploader() {
  const [uploadedFile, setUploadedFile] = useState<string | null>(null);
  const { addToast } = useToast();
  const queryClient = useQueryClient();

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("title", file.name.replace(/\.[^/.]+$/, "")); // Remove extension for title
      return api.post("/resumes/", formData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resumes"] });
      addToast({ title: "Resume uploaded successfully", variant: "success" });
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || "Failed to upload resume";
      addToast({ title: message, variant: "error" });
      setUploadedFile(null);
    },
  });

  const handleDrop = (files: File[]) => {
    if (files.length > 0) {
      const file = files[0];
      setUploadedFile(file.name);
      uploadMutation.mutate(file);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Upload Resume</CardTitle>
        <CardDescription>Upload your resume in PDF or DOC format. Max file size: 10MB.</CardDescription>
      </CardHeader>
      <CardContent>
        {uploadMutation.isPending ? (
          <div className="flex items-center justify-center py-8 gap-2 text-muted-foreground">
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>Uploading {uploadedFile}...</span>
          </div>
        ) : (
          <FileUpload
            onDrop={handleDrop}
            currentFile={uploadedFile || undefined}
            onRemove={() => setUploadedFile(null)}
            label="Drop your resume here or click to browse"
            description="PDF or DOC, max 10MB"
          />
        )}
      </CardContent>
    </Card>
  );
}
