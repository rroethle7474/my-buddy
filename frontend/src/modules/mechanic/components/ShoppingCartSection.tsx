// Shopping cart (§1.1) — consumables to buy, with a running cost total.
// Renders off the hydrated `materials[]`; the `checked` toggle is a live-ish
// mutation (PATCH /projects/{id}/materials/{mid}) via the data hook.

import type { MaterialRead } from "../types";
import { money, moneyTotal, quantity } from "../format";
import { color } from "../tokens";
import { Checkbox, SectionHead } from "./ui";

export function ShoppingCartSection({
  materials,
  onToggle,
}: {
  materials: MaterialRead[];
  onToggle: (materialId: number, checked: boolean) => void;
}) {
  const total = materials.reduce((s, m) => s + m.est_cost_usd, 0);
  const remaining = materials
    .filter((m) => !m.checked)
    .reduce((s, m) => s + m.est_cost_usd, 0);
  const gotCount = materials.filter((m) => m.checked).length;

  return (
    <section className="mech-section" id="shopping" aria-labelledby="shopping-h">
      <SectionHead
        id="shopping-h"
        icon="🛒"
        iconBg={color.goldTint}
        iconFg={color.goldInk}
        title="Shopping cart"
        sub={`${materials.length} consumables · ${gotCount} in your cart`}
      />
      <div className="mech-card">
        <div className="mech-list">
          {materials.map((m) => (
            <div
              key={m.id}
              className={m.checked ? "mech-row mech-row--checked" : "mech-row"}
            >
              <Checkbox
                checked={m.checked}
                onChange={(c) => onToggle(m.id, c)}
                label={`Mark ${m.name} as bought`}
              />
              <div className="mech-row__body">
                <div className="mech-row__top">
                  <span className="mech-row__name">{m.name}</span>
                  <span
                    className={
                      m.est_cost_usd === 0
                        ? "mech-row__cost mech-row__cost--free"
                        : "mech-row__cost"
                    }
                  >
                    {money(m.est_cost_usd)}
                  </span>
                </div>
                <div className="mech-row__meta">{quantity(m.quantity, m.unit)}</div>
                {m.where_to_find && (
                  <div className="mech-row__where">
                    <span aria-hidden="true">📍</span>
                    {m.where_to_find}
                  </div>
                )}
                {m.notes && <div className="mech-row__note">{m.notes}</div>}
              </div>
            </div>
          ))}
        </div>
        <div className="mech-total">
          <span className="mech-total__label">
            {gotCount > 0
              ? `${moneyTotal(remaining)} left to buy`
              : "Estimated total"}
          </span>
          <span className="mech-total__value">{moneyTotal(total)}</span>
        </div>
      </div>
    </section>
  );
}
