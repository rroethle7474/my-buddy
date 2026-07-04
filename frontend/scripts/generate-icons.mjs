// Rasterize the PWA icons from public/buddy-icon.svg (ARCHITECTURE.md §16.4).
// Run: npm run gen:icons  (regenerate whenever buddy-icon.svg changes).
// sharp is a dev-only dependency; the generated PNGs are committed so the app
// ships without a build step needing sharp.
import sharp from "sharp";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const pub = join(dirname(fileURLToPath(import.meta.url)), "..", "public");
const src = join(pub, "buddy-icon.svg");

const targets = [
  { name: "pwa-192x192.png", size: 192 },
  { name: "pwa-512x512.png", size: 512 },
  { name: "maskable-512x512.png", size: 512 },
  { name: "apple-touch-icon.png", size: 180 },
];

for (const { name, size } of targets) {
  await sharp(src, { density: 384 })
    .resize(size, size, { fit: "cover" })
    .png()
    .toFile(join(pub, name));
  console.log(`✓ ${name} (${size}×${size})`);
}
