import { BrandMark } from "./BrandMark";
import styles from "./Footer.module.css";

/**
 * Global footer. Carries the standing safety disclaimer (§16.4) — every
 * generated plan adds its own emphasized cautions, but the reassurance lives
 * here app-wide so it's never absent.
 */
export function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={styles.row}>
        <div className={styles.brand}>
          <BrandMark size={22} />
          <span className={styles.wordmark}>My Buddy</span>
        </div>
        <nav className={styles.links} aria-label="Footer">
          <span>About</span>
          <span>Modules</span>
          <span>Privacy</span>
        </nav>
        <span className={styles.copy}>© 2026 My Buddy</span>
      </div>
      <p className={styles.disclaimer}>
        My Buddy can make mistakes — double-check load ratings and anything that
        bears weight before you build.
      </p>
    </footer>
  );
}
