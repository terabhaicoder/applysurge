"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { FileText, Star, Trash2, Download, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { useToast } from "@/providers/toast-provider";
import { formatDate } from "@/lib/utils";

interface Resume {
  id: string;
  title: string;
  file_name: string;
  file_url: string;
  is_default: boolean;
  created_at: string;
}

export function ResumeList() {
  const { addToast } = useToast();
  const queryClient = useQueryClient();

  const { data: resumes, isLoading } = useQuery({
    queryKey: ["resumes"],
    queryFn: () => api.get<Resume[]>("/resumes/").then((r) => r.data),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/resumes/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resumes"] });
      addToast({ title: "Resume deleted", variant: "success" });
    },
    onError: () => {
      addToast({ title: "Failed to delete resume", variant: "error" });
    },
  });

  const setPrimaryMutation = useMutation({
    mutationFn: (id: string) => api.patch(`/resumes/${id}`, { is_default: true }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resumes"] });
      addToast({ title: "Primary resume updated", variant: "success" });
    },
    onError: () => {
      addToast({ title: "Failed to update primary resume", variant: "error" });
    },
  });

  const handleDownload = async (resume: Resume) => {
    try {
      const response = await api.get(`/resumes/${resume.id}/download`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", resume.file_name);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch {
      addToast({ title: "Failed to download resume", variant: "error" });
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Your Resumes</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8 text-muted-foreground">
            <Loader2 className="w-5 h-5 animate-spin mr-2" />
            Loading resumes...
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Your Resumes</CardTitle>
      </CardHeader>
      <CardContent>
        {!resumes || resumes.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <FileText className="w-12 h-12 mx-auto mb-2 text-border" />
            <p>No resumes uploaded yet</p>
            <p className="text-sm">Upload your first resume above</p>
          </div>
        ) : (
          <div className="space-y-3">
            {resumes.map((resume) => (
              <div key={resume.id} className="flex items-center justify-between p-3 bg-secondary rounded-lg">
                <div className="flex items-center gap-3">
                  <FileText className="w-8 h-8 text-blue-600" />
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium text-foreground">{resume.title || resume.file_name}</p>
                      {resume.is_default && <Badge variant="info" className="text-xs">Primary</Badge>}
                    </div>
                    <p className="text-xs text-muted-foreground">Uploaded {formatDate(resume.created_at)}</p>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  {!resume.is_default && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      title="Set as primary"
                      onClick={() => setPrimaryMutation.mutate(resume.id)}
                      disabled={setPrimaryMutation.isPending}
                    >
                      <Star className="w-4 h-4 text-muted-foreground" />
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    title="Download"
                    onClick={() => handleDownload(resume)}
                  >
                    <Download className="w-4 h-4 text-muted-foreground" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-red-500 hover:text-red-600 hover:bg-red-50"
                    title="Delete"
                    onClick={() => deleteMutation.mutate(resume.id)}
                    disabled={deleteMutation.isPending}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
