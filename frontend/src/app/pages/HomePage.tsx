import { useMemo } from "react";
import { useProjects, useModules } from "../../api/hooks";
import { availableModules, moduleBySlug } from "../modules/registry";
import type { ModuleDef } from "../modules/registry";
import { Mascot } from "../shell/Mascot";
import { Button } from "../components/Button";
import { ProjectCard } from "../components/ProjectCard";
import { SkeletonGrid, ErrorState, EmptyState } from "../components/states";
import styles from "./HomePage.module.css";

/** Homepage — "Spotlight" (mock 1a): mascot hero + your projects grid. */
export function HomePage() {
  const projectsQ = useProjects();
  const modulesQ = useModules();
  const primary = availableModules[0];

  // Resolve each project's module_id → registry def (for chip + link target).
  const moduleById = useMemo(() => {
    const map = new Map<number, ModuleDef>();
    for (const bm of modulesQ.data ?? []) {
      const def = moduleBySlug(bm.slug);
      if (def) map.set(bm.id, def);
    }
    return map;
  }, [modulesQ.data]);

  const projects = projectsQ.data ?? [];

  return (
    <div className={styles.page}>
      <section className={styles.hero}>
        <span className={styles.eyebrow}>Your handy childhood pal</span>
        <h1 className={styles.headline}>Let's build something together.</h1>
        <p className={styles.sub}>
          Pick a module, describe what you're making, and My Buddy walks you
          through it — start to finished plans.
        </p>

        <div className={styles.mascotPanel}>
          <span className={styles.rainbow} aria-hidden="true" />
          <Mascot height={322} className={styles.mascot} title="Buddy, waving hello" />
        </div>

        {primary && (
          <Button to={`/${primary.routeSlug}`} className={styles.cta}>
            Open {primary.name} →
          </Button>
        )}
      </section>

      <section className={styles.projects}>
        <div className={styles.sectionHead}>
          <h2 className={styles.sectionTitle}>Your projects</h2>
          {projectsQ.isSuccess && projects.length > 0 && (
            <span className={styles.count}>{projects.length} total</span>
          )}
        </div>

        {projectsQ.isLoading ? (
          <SkeletonGrid count={4} />
        ) : projectsQ.isError ? (
          <ErrorState
            message="Couldn't load your projects."
            onRetry={() => projectsQ.refetch()}
          />
        ) : projects.length === 0 ? (
          <EmptyState
            title="No projects yet"
            body="Start with My Mechanic — tell My Buddy what you want to build and you'll get a materials list and a step-by-step plan."
            action={
              primary && <Button to={`/${primary.routeSlug}`}>Open {primary.name} →</Button>
            }
          />
        ) : (
          <div className={styles.grid}>
            {projects.map((p) => (
              <ProjectCard
                key={p.id}
                project={p}
                module={moduleById.get(p.module_id)}
                variant="home"
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
