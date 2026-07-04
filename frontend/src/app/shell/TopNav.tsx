import { Link, NavLink } from "react-router-dom";
import { modules } from "../modules/registry";
import { BrandMark } from "./BrandMark";
import styles from "./TopNav.module.css";

/**
 * The shell's top navigation (matches mock 1a): brand on the left, module links
 * on the right. Available modules are links (active state on the current
 * route); coming-soon modules are muted labels, capped by a "more soon" pill.
 * Registry-driven, so a new module appears here without touching this file.
 */
export function TopNav() {
  return (
    <header className={styles.nav}>
      <Link to="/" className={styles.brand}>
        <BrandMark />
        <span className={styles.wordmark}>My Buddy</span>
      </Link>

      <nav className={styles.links} aria-label="Modules">
        {modules.map((m) =>
          m.status === "available" ? (
            <NavLink
              key={m.slug}
              to={`/${m.routeSlug}`}
              className={({ isActive }) =>
                `${styles.moduleLink} ${isActive ? styles.moduleLinkActive : ""}`
              }
            >
              {m.name}
            </NavLink>
          ) : (
            <span key={m.slug} className={styles.moduleSoon} aria-disabled="true">
              {m.name}
            </span>
          ),
        )}
        <span className={styles.moreSoon}>more soon</span>
      </nav>
    </header>
  );
}
