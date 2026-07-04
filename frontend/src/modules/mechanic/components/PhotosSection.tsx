// Progress photos (§5) — the visual half of the learning journal. Upload a shot
// (with an optional caption), see them in a gallery, remove one. Bytes are served
// by the out-of-schema byte route (see api/photos.ts); upload is multipart.

import { useRef, useState, type ChangeEvent } from "react";
import type { PhotoRead } from "../types";
import { color } from "../tokens";
import { SectionHead } from "./ui";
import { photoSrc } from "../api/photos";

export function PhotosSection({
  photos,
  onUpload,
  onDelete,
}: {
  photos: PhotoRead[];
  onUpload: (file: File, caption?: string) => Promise<void>;
  onDelete: (photoId: number) => Promise<void>;
}) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [caption, setCaption] = useState("");
  const [uploading, setUploading] = useState(false);

  async function onPick(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = ""; // let the same file be re-picked later
    if (!file) return;
    setUploading(true);
    try {
      await onUpload(file, caption.trim() || undefined);
      setCaption("");
    } catch {
      // the hook surfaces the failure as a toast; keep the caption draft
    } finally {
      setUploading(false);
    }
  }

  return (
    <section className="mech-section" id="photos" aria-labelledby="photos-h">
      <SectionHead
        id="photos-h"
        icon="📸"
        iconBg={color.blueTint}
        iconFg={color.blue}
        title="Progress photos"
        sub={
          photos.length
            ? `${photos.length} snapped so far`
            : "Snap your build as you go — before, during, and the finished piece."
        }
      />
      <div className="mech-card">
        <div className="mech-photos__upload">
          <input
            className="mech-retro__input"
            type="text"
            placeholder="Add a caption (optional)"
            value={caption}
            onChange={(e) => setCaption(e.target.value)}
          />
          <input
            ref={fileRef}
            className="mech-photos__file"
            type="file"
            accept="image/*"
            capture="environment"
            onChange={onPick}
            aria-label="Choose a photo to upload"
          />
          <button
            type="button"
            className="mech-btn mech-btn--primary"
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
          >
            {uploading ? "Uploading…" : "📷 Add a photo"}
          </button>
        </div>

        {photos.length === 0 ? (
          <div className="mech-empty">
            No photos yet — your progress shots will show up here.
          </div>
        ) : (
          <div className="mech-photos__grid">
            {photos.map((photo) => (
              <figure key={photo.id} className="mech-photo">
                <img
                  className="mech-photo__img"
                  src={photoSrc(photo.id)}
                  alt={photo.caption ?? "Progress photo"}
                  loading="lazy"
                />
                <button
                  type="button"
                  className="mech-photo__del"
                  onClick={() => onDelete(photo.id)}
                  aria-label="Remove photo"
                >
                  ✕
                </button>
                {photo.caption && (
                  <figcaption className="mech-photo__cap">{photo.caption}</figcaption>
                )}
              </figure>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
