// Photo data layer (§11 Photos, D4). Upload is multipart, so it uses a direct
// `fetch` (FormData) rather than the JSON openapi-fetch client; list comes with
// the hydrated project (`project.photos`), and the bytes are served by the
// out-of-schema byte route `GET /photos/{id}/content` (never in schema.d.ts, so
// we build the URL here rather than reading it off a generated type).

import { api } from "../../../api/client";
import type { PhotoRead } from "../types";

/** `<img>` src for a photo's bytes (out-of-schema byte route, §11). Same-origin;
 *  the Vite dev server proxies `/photos` to the API. */
export function photoSrc(photoId: number): string {
  return `/photos/${photoId}/content`;
}

/** POST /projects/{id}/photos (multipart) → the created PhotoRead. */
export async function uploadPhoto(
  projectId: number,
  file: File,
  opts?: { caption?: string; stepId?: number },
): Promise<PhotoRead> {
  const form = new FormData();
  form.append("file", file);
  if (opts?.caption) form.append("caption", opts.caption);
  if (opts?.stepId != null) form.append("step_id", String(opts.stepId));

  const res = await fetch(`/projects/${projectId}/photos`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error("Could not upload that photo.");
  return (await res.json()) as PhotoRead;
}

/** DELETE /photos/{id} — removes the row and the stored object. */
export async function deletePhoto(photoId: number): Promise<void> {
  const { error } = await api.DELETE("/photos/{photo_id}", {
    params: { path: { photo_id: photoId } },
  });
  if (error) throw new Error("Could not remove that photo.");
}
