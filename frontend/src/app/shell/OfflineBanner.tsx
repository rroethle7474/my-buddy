import { useEffect, useState } from "react";
import styles from "./OfflineBanner.module.css";

/**
 * A slim connectivity banner (§9). When offline, reads still work (served from
 * the runtime cache), so we reassure rather than alarm — and set expectations
 * that changes need a connection (offline mutation replay is deferred).
 */
export function OfflineBanner() {
  const [online, setOnline] = useState(() =>
    typeof navigator === "undefined" ? true : navigator.onLine,
  );

  useEffect(() => {
    const goOnline = () => setOnline(true);
    const goOffline = () => setOnline(false);
    window.addEventListener("online", goOnline);
    window.addEventListener("offline", goOffline);
    return () => {
      window.removeEventListener("online", goOnline);
      window.removeEventListener("offline", goOffline);
    };
  }, []);

  if (online) return null;

  return (
    <div className={styles.banner} role="status">
      You're offline — you can still read your saved projects. You'll need a
      connection to make changes.
    </div>
  );
}
