// Display formatters for the mechanic sections. Read-only presentation only —
// the backend is the source of truth for money (stored as cents/Decimal, §14);
// the API hands us plain USD numbers, which we format here.

/** `$45`, `$0` (free), or `$12.50` when there are cents. */
export function money(usd: number): string {
  if (usd === 0) return "Free";
  const hasCents = Math.round(usd * 100) % 100 !== 0;
  return usd.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: hasCents ? 2 : 0,
    maximumFractionDigits: 2,
  });
}

/** Plain `$45` total (never "Free") for running cost lines. */
export function moneyTotal(usd: number): string {
  const hasCents = Math.round(usd * 100) % 100 !== 0;
  return usd.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: hasCents ? 2 : 0,
    maximumFractionDigits: 2,
  });
}

/** `15 min`, `1 hr`, `1 hr 30 min`. */
export function minutes(total: number): string {
  if (total < 60) return `${total} min`;
  const hrs = Math.floor(total / 60);
  const mins = total % 60;
  const h = `${hrs} hr`;
  return mins ? `${h} ${mins} min` : h;
}

/** Sum est_time_minutes across steps into a friendly total. */
export function totalTime(steps: { est_time_minutes: number }[]): string {
  return minutes(steps.reduce((sum, s) => sum + s.est_time_minutes, 0));
}

/** `1 panel`, `2 panels`, `3 ft` — quantity + unit, pluralized simply. */
export function quantity(qty: number, unit: string): string {
  const u = qty === 1 || unit.endsWith("s") ? unit : `${unit}s`;
  return `${qty} ${u}`;
}
