import type { ReactNode } from "react";
import { Button } from "./Button";
import styles from "./states.module.css";

/** Shimmer placeholders while a projects query is in flight. */
export function SkeletonGrid({ count = 4 }: { count?: number }) {
  return (
    <div className={styles.grid} aria-hidden="true">
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className={styles.skeleton} />
      ))}
    </div>
  );
}

/** Friendly load error — says what happened and offers a retry (§16.5). */
export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className={styles.panel} role="alert">
      <div className={styles.emoji}>😕</div>
      <p className={styles.title}>{message}</p>
      <p className={styles.body}>
        You may be offline, or My Buddy's backend isn't up yet. Your saved work is
        safe.
      </p>
      {onRetry && (
        <Button variant="secondary" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}

/** Empty state that invites the next action (§16.5). */
export function EmptyState({
  title,
  body,
  action,
}: {
  title: string;
  body: string;
  action?: ReactNode;
}) {
  return (
    <div className={styles.panel}>
      <div className={styles.emoji}>🧰</div>
      <p className={styles.title}>{title}</p>
      <p className={styles.body}>{body}</p>
      {action}
    </div>
  );
}
