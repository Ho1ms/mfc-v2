import { getToken } from "@/api/client";

export interface UploadedFile {
  id: number;
  url: string;
  name: string;
  mime: string;
  size_bytes: number;
}

export async function uploadFile(file: File): Promise<UploadedFile> {
  const fd = new FormData();
  fd.append("file", file);

  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  console.log("VITE FILE URL", import.meta.env.VITE_API_URL);

  const res = await fetch(`${import.meta.env.VITE_API_URL}/api/files`, {
    method: "POST",
    headers,
    body: fd,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Upload failed (${res.status})`);
  }
  return res.json();
}

export function formatBytes(n: number): string {
  if (n < 1024) return `${n} Б`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} КБ`;
  return `${(n / (1024 * 1024)).toFixed(1)} МБ`;
}

export function isImageMime(mime?: string | null): boolean {
  return Boolean(mime && mime.startsWith("image/"));
}
