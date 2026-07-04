// Sticky section nav (pills) for the four sections. Scrollspy via
// IntersectionObserver; clicking a pill smooth-scrolls to that section (and
// scroll-behavior is disabled under prefers-reduced-motion in styles.css).

import { useEffect, useState } from "react";
import type { SectionKey } from "../types";

interface NavItem {
  key: SectionKey;
  label: string;
  count?: string;
}

export function SectionNav({ items }: { items: NavItem[] }) {
  const [active, setActive] = useState<SectionKey>(items[0].key);

  useEffect(() => {
    const sections = items
      .map((i) => document.getElementById(i.key))
      .filter((el): el is HTMLElement => el != null);
    if (sections.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
        if (visible[0]) setActive(visible[0].target.id as SectionKey);
      },
      { rootMargin: "-88px 0px -55% 0px", threshold: [0.1, 0.5, 1] },
    );
    sections.forEach((s) => observer.observe(s));
    return () => observer.disconnect();
  }, [items]);

  const go = (key: SectionKey) => {
    document.getElementById(key)?.scrollIntoView({ behavior: "smooth", block: "start" });
    setActive(key);
  };

  return (
    <nav className="mech-nav" aria-label="Project sections">
      <div className="mech-nav__track">
        {items.map((item) => (
          <button
            key={item.key}
            type="button"
            className="mech-nav__pill"
            aria-current={active === item.key}
            onClick={() => go(item.key)}
          >
            {item.label}
            {item.count && <span className="mech-nav__count">{item.count}</span>}
          </button>
        ))}
      </div>
    </nav>
  );
}
