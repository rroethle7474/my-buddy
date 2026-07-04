import type { ProjectStatus } from "../../api/hooks";
import styles from "./StatusPill.module.css";

// DB status (§5) → the user-facing labels/colors from the mock.
const MAP: Record<ProjectStatus, { label: string; cls: string }> = {
  planning: { label: "Draft", cls: styles.draft },
  active: { label: "In progress", cls: styles.active },
  complete: { label: "Done", cls: styles.done },
};

export function StatusPill({ status }: { status: ProjectStatus }) {
  const s = MAP[status] ?? MAP.planning;
  return <span className={`${styles.pill} ${s.cls}`}>{s.label}</span>;
}
