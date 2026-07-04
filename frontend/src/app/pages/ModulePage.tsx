import { Link } from "react-router-dom";
import { useProjects } from "../../api/hooks";
import { moduleBySlug, newProjectPath } from "../modules/registry";
import { Button } from "../components/Button";
import { ProjectCard } from "../components/ProjectCard";
import { SkeletonGrid, ErrorState, EmptyState } from "../components/states";
import { NotFound } from "./NotFound";
import styles from "./ModulePage.module.css";

/** A module page (mock 1c — "My Mechanic"): start-new panel + past projects.
 *  Registry-driven so it renders for any module, not just mechanic (§15). */
export function ModulePage({ moduleSlug }: { moduleSlug: string }) {
  const module = moduleBySlug(moduleSlug);
  const projectsQ = useProjects({ module: moduleSlug });

  if (!module) return <NotFound />;

  const projects = projectsQ.data ?? [];
  const newPath = newProjectPath(module);

  return (
    <div className={styles.page}>
      <div className={styles.breadcrumb}>
        <div className={styles.crumbs}>
          <Link to="/" className={styles.back} aria-label="Back to home">
            ‹
          </Link>
          <Link to="/" className={styles.crumbHome}>
            My Buddy
          </Link>
          <span className={styles.slash}>/</span>
          <span className={styles.crumbCurrent}>{module.name}</span>
        </div>
        <Button to={newPath} size="sm">
          + New project
        </Button>
      </div>

      <header className={styles.hero}>
        <span className={styles.eyebrow}>Module</span>
        <h1 className={styles.title}>{module.name}</h1>
        <p className={styles.tagline}>{module.tagline}</p>
      </header>

      <section className={styles.startPanel}>
        <div className={styles.startText}>
          <h2 className={styles.startTitle}>Start a new project</h2>
          <p className={styles.startBody}>
            Tell My Buddy what you want to build. You'll chat it through together,
            then get a materials list and step-by-step plan you can keep.
          </p>
        </div>
        <Button to={newPath}>Start a new project →</Button>
      </section>

      <section className={styles.projects}>
        <div className={styles.sectionHead}>
          <h2 className={styles.sectionTitle}>Your {module.name.replace(/^My /, "").toLowerCase()} projects</h2>
          {projectsQ.isSuccess && projects.length > 0 && (
            <span className={styles.count}>
              {projects.length} {projects.length === 1 ? "project" : "projects"}
            </span>
          )}
        </div>

        {projectsQ.isLoading ? (
          <SkeletonGrid count={3} />
        ) : projectsQ.isError ? (
          <ErrorState
            message="Couldn't load these projects."
            onRetry={() => projectsQ.refetch()}
          />
        ) : projects.length === 0 ? (
          <EmptyState
            title="Nothing here yet"
            body="Your first build is one chat away. Start a new project and My Buddy will plan it with you."
            action={<Button to={newPath}>Start a new project →</Button>}
          />
        ) : (
          <div className={styles.grid}>
            {projects.map((p) => (
              <ProjectCard key={p.id} project={p} module={module} variant="module" />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
