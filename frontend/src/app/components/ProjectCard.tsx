import { Link } from "react-router-dom";
import type { ProjectSummary } from "../../api/hooks";
import type { ModuleDef } from "../modules/registry";
import { projectPath } from "../modules/registry";
import { StatusPill } from "./StatusPill";
import { formatShortDate } from "../lib/format";
import styles from "./ProjectCard.module.css";

interface ProjectCardProps {
  project: ProjectSummary;
  /** Resolved from project.module_id; undefined ⇒ neutral, non-linked card. */
  module?: ModuleDef;
  /** "home" = flat chip + summary (1a); "module" = glyph header + meta (1c). */
  variant?: "home" | "module";
}

export function ProjectCard({ project, module, variant = "home" }: ProjectCardProps) {
  const to = module ? projectPath(module, project.slug) : undefined;

  const inner =
    variant === "module" ? (
      <>
        <div
          className={styles.glyph}
          style={{
            background: module
              ? `linear-gradient(135deg, ${module.accentTint}, ${module.accentTint2})`
              : "var(--surface-3)",
          }}
          aria-hidden="true"
        >
          {module?.glyph ?? "🛠️"}
        </div>
        <div className={styles.body}>
          <h3 className={styles.title}>{project.name}</h3>
          <StatusPill status={project.status} />
          <div className={styles.meta}>Added {formatShortDate(project.created_at)}</div>
        </div>
      </>
    ) : (
      <div className={styles.bodyFlat}>
        <div className={styles.topRow}>
          <span className={styles.moduleChip} style={{ color: module?.accent, background: module?.accentTint }}>
            {module?.name ?? "Project"}
          </span>
          <StatusPill status={project.status} />
        </div>
        <h3 className={styles.title}>{project.name}</h3>
        {project.summary && <p className={styles.summary}>{project.summary}</p>}
      </div>
    );

  const cls = `${styles.card} ${variant === "module" ? styles.cardModule : styles.cardHome}`;

  return to ? (
    <Link to={to} className={cls}>
      {inner}
    </Link>
  ) : (
    <div className={cls}>{inner}</div>
  );
}
