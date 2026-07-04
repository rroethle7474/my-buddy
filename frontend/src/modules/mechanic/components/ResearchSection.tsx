// Research-first (§1.4) — topics to review before starting, each with links to
// learning resources. `resources[]` is populated by the web-search pass (§7.2)
// and may arrive empty; we render an honest empty state until it's filled.

import type { ResearchResource, ResearchTopicRead } from "../types";
import { color } from "../tokens";
import { SectionHead } from "./ui";

const TYPE_ICON: Record<string, string> = {
  video: "▶",
  article: "📄",
  guide: "📘",
  doc: "📄",
};

function ResourceLink({ resource }: { resource: ResearchResource }) {
  const icon = TYPE_ICON[resource.type?.toLowerCase()] ?? "🔗";
  return (
    <a
      className="mech-resource"
      href={resource.url}
      target="_blank"
      rel="noopener noreferrer"
    >
      <span className="mech-resource__type" aria-hidden="true">
        {icon}
      </span>
      <span>
        {resource.title}
        {/* shown only in the print/PDF copy so paper links are followable */}
        <span className="mech-resource__url">{resource.url}</span>
      </span>
      <span className="mech-resource__arrow" aria-hidden="true">
        ↗
      </span>
    </a>
  );
}

export function ResearchSection({
  topics,
  loading = false,
  error = false,
  onRefresh,
}: {
  topics: ResearchTopicRead[];
  /** The research web-search pass (§7.2) is still running — show a gentle
   *  "gathering" state on topics whose resources haven't landed yet. */
  loading?: boolean;
  /** The last refresh failed — offer a retry instead of spinning forever. */
  error?: boolean;
  /** Fire (or re-fire) the refresh. Always an explicit action: a refresh runs
   *  real (billed) web searches, so it must never re-run silently on load. */
  onRefresh?: () => void;
}) {
  // Any topic still without resources needs a retry path — not just the
  // all-empty case. Under the chunked refresh (F1.4, Option B) a partial fill
  // returns some topics filled and some empty, so gate on `some`, not `every`.
  const anyUnfilled = topics.some((t) => t.resources.length === 0);
  const someFilled = topics.some((t) => t.resources.length > 0);
  const showAction = !loading && onRefresh !== undefined && (error || anyUnfilled);

  return (
    <section className="mech-section" id="research" aria-labelledby="research-h">
      <SectionHead
        id="research-h"
        icon="🔎"
        iconBg={color.greenTint}
        iconFg={color.green}
        title="Research first"
        sub={
          loading
            ? "Finding good resources for you…"
            : error
              ? "We couldn't fetch resources just now"
              : `${topics.length} things worth a look before you start`
        }
      />
      <div className="mech-card">
        {showAction && (
          <div className="mech-research-cta" role={error ? "alert" : undefined}>
            <span>
              {error
                ? "The resource search didn't make it through — it may be busy."
                : someFilled
                  ? "Some topics still need resources."
                  : "Resources haven't been gathered for this build yet."}
            </span>
            <button
              type="button"
              className="mech-btn mech-btn--primary mech-btn--sm"
              onClick={onRefresh}
            >
              {error ? "Try again" : someFilled ? "Find the rest" : "Find resources"}
            </button>
          </div>
        )}
        {topics.length === 0 && (
          <div className="mech-empty">No research topics for this build.</div>
        )}
        {topics.map((topic) => (
          <div key={topic.id} className="mech-topic">
            <div className="mech-topic__title">{topic.topic}</div>
            <div className="mech-topic__why">{topic.why}</div>
            <div className="mech-resources">
              {topic.resources.length > 0 ? (
                topic.resources.map((r, i) => (
                  <ResourceLink key={`${topic.id}-${i}`} resource={r} />
                ))
              ) : loading ? (
                <span className="mech-resource--loading">
                  <span className="mech-spinner" aria-hidden="true" /> Finding good
                  resources…
                </span>
              ) : (
                <span className="mech-resource--empty">
                  No resources gathered yet.
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
