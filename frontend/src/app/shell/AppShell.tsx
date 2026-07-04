import { Outlet, ScrollRestoration } from "react-router-dom";
import { TopNav } from "./TopNav";
import { Footer } from "./Footer";
import styles from "./AppShell.module.css";

/**
 * The my-buddy shell (ARCHITECTURE.md §10, frontend/src/app): persistent nav +
 * footer wrapping the routed page. Every screen renders inside this frame, so
 * the module registry, brand, and safety disclaimer stay consistent app-wide.
 */
export function AppShell() {
  return (
    <>
      <TopNav />
      <main className={styles.main}>
        <Outlet />
      </main>
      <Footer />
      <ScrollRestoration />
    </>
  );
}
