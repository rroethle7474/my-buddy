// Small shared building blocks for the mechanic sections. Presentational only;
// all styling lives in styles.css (§16.1 tokens).

import type { ReactNode } from "react";

export function Checkbox({
  checked,
  onChange,
  label,
  green,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: string;
  green?: boolean;
}) {
  return (
    <input
      type="checkbox"
      className={green ? "mech-check mech-check--green" : "mech-check"}
      checked={checked}
      aria-label={label}
      onChange={(e) => onChange(e.target.checked)}
    />
  );
}

export function Badge({
  children,
  fg,
  bg,
}: {
  children: ReactNode;
  fg: string;
  bg: string;
}) {
  return (
    <span className="mech-badge" style={{ color: fg, background: bg }}>
      {children}
    </span>
  );
}

export function Chip({
  children,
  outline,
}: {
  children: ReactNode;
  outline?: boolean;
}) {
  return (
    <span className={outline ? "mech-chip mech-chip--outline" : "mech-chip"}>
      {children}
    </span>
  );
}

export function SectionHead({
  icon,
  iconBg,
  iconFg,
  title,
  sub,
  id,
}: {
  icon: string;
  iconBg: string;
  iconFg: string;
  title: string;
  sub: string;
  id?: string;
}) {
  return (
    <div className="mech-section-head" id={id}>
      <div
        className="mech-section-head__icon"
        style={{ background: iconBg, color: iconFg }}
        aria-hidden="true"
      >
        {icon}
      </div>
      <div className="mech-section-head__titles">
        <h2 className="mech-h2">{title}</h2>
        <span className="mech-section-head__sub">{sub}</span>
      </div>
    </div>
  );
}
