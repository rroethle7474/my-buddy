// Tool list (§1.2 / §8) — the three-bucket model: consumables live in the
// Shopping cart section; here we render the other two buckets computed by the
// shop diff (§8): tools you already own (auto-checked) and tools to acquire
// (with cost). `owned`/`acquire` come from the diff; `checked` is the in-hand /
// acquired toggle. Moving a tool between buckets = PATCH …/tools/{tid}.

import type { ToolRead } from "../types";
import { money, moneyTotal } from "../format";
import { color } from "../tokens";
import { Badge, Checkbox, SectionHead } from "./ui";

function ToolRow({
  tool,
  onToggle,
  onOwn,
}: {
  tool: ToolRead;
  onToggle: (toolId: number, checked: boolean) => void;
  onOwn?: (toolId: number) => void;
}) {
  return (
    <div className={tool.checked ? "mech-row mech-row--checked" : "mech-row"}>
      <Checkbox
        checked={tool.checked}
        green={tool.owned}
        onChange={(c) => onToggle(tool.id, c)}
        label={
          tool.owned ? `Mark ${tool.name} as ready` : `Mark ${tool.name} as acquired`
        }
      />
      <div className="mech-row__body">
        <div className="mech-row__top">
          <span className="mech-row__name">
            {tool.name}
            {!tool.essential && (
              <span style={{ marginLeft: 8 }}>
                <Badge fg={color.muted3} bg={color.surface3}>
                  optional
                </Badge>
              </span>
            )}
          </span>
          {tool.acquire && (
            <span
              className={
                tool.est_cost_usd === 0
                  ? "mech-row__cost mech-row__cost--free"
                  : "mech-row__cost"
              }
            >
              {money(tool.est_cost_usd)}
            </span>
          )}
        </div>
        {tool.notes && <div className="mech-row__note">{tool.notes}</div>}
        {tool.alternatives && (
          <div className="mech-row__note">
            <strong style={{ color: color.muted2 }}>Or: </strong>
            {tool.alternatives}
          </div>
        )}
        {tool.acquire && onOwn && (
          <button
            type="button"
            className="mech-own-btn"
            onClick={() => onOwn(tool.id)}
          >
            ✓ I have this now
          </button>
        )}
      </div>
    </div>
  );
}

export function ToolListSection({
  tools,
  onToggle,
  onOwn,
}: {
  tools: ToolRead[];
  onToggle: (toolId: number, checked: boolean) => void;
  onOwn: (toolId: number) => void;
}) {
  const owned = tools.filter((t) => t.owned);
  const acquire = tools.filter((t) => t.acquire);
  const acquireTotal = acquire.reduce((s, t) => s + t.est_cost_usd, 0);

  return (
    <section className="mech-section" id="tools" aria-labelledby="tools-h">
      <SectionHead
        id="tools-h"
        icon="🧰"
        iconBg={color.blueTint}
        iconFg={color.blue}
        title="Tools"
        sub={`${owned.length} you own · ${acquire.length} to get`}
      />
      <div className="mech-card">
        {owned.length > 0 && (
          <div className="mech-bucket">
            <div className="mech-bucket__head">
              <span className="mech-bucket__title" style={{ color: color.green }}>
                ✓ You already have
              </span>
            </div>
            <p className="mech-bucket__hint">
              Matched against your My&nbsp;Shop inventory — check each off as you
              gather it.
            </p>
            <div className="mech-list">
              {owned.map((t) => (
                <ToolRow key={t.id} tool={t} onToggle={onToggle} />
              ))}
            </div>
          </div>
        )}

        {acquire.length > 0 && (
          <div className="mech-bucket">
            <div className="mech-bucket__head">
              <span className="mech-bucket__title" style={{ color: color.red }}>
                Tools to acquire
              </span>
            </div>
            <p className="mech-bucket__hint">
              You don't own these yet. Marking one “I have this now” adds it to My
              Shop for future projects.
            </p>
            <div className="mech-list">
              {acquire.map((t) => (
                <ToolRow key={t.id} tool={t} onToggle={onToggle} onOwn={onOwn} />
              ))}
            </div>
            <div className="mech-total">
              <span className="mech-total__label">To acquire</span>
              <span className="mech-total__value">{moneyTotal(acquireTotal)}</span>
            </div>
          </div>
        )}

        {owned.length === 0 && acquire.length === 0 && (
          <div className="mech-empty">No tools needed for this build.</div>
        )}
      </div>
      <p className="mech-bucket__hint" style={{ padding: "10px 4px 0" }}>
        Consumables (wood, screws, finish) are in the{" "}
        <a href="#shopping" style={{ color: color.blue, fontWeight: 600 }}>
          Shopping cart
        </a>
        .
      </p>
    </section>
  );
}
