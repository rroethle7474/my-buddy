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
      <span>{resource.title}</span>
      <span className="mech-resource__arrow" aria-hidden="true">
        ↗
      </span>
    </a>
  );
}

export function ResearchSection({ topics }: { topics: ResearchTopicRead[] }) {
  return (
    <section className="mech-section" id="research" aria-labelledby="research-h">
      <SectionHead
        id="research-h"
        icon="🔎"
        iconBg={color.greenTint}
        iconFg={color.green}
        title="Research first"
        sub={`${topics.length} things worth a look before you start`}
      />
      <div className="mech-card">
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
              ) : (
                <span className="mech-resource--empty">
                  Resources are still being gathered for this topic.
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
