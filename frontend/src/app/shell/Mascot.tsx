import { useId } from "react";
import type { CSSProperties } from "react";

interface MascotProps {
  /** Rendered height in px (viewBox is 260×320). */
  height?: number;
  className?: string;
  style?: CSSProperties;
  /** Accessible name. Decorative uses can pass "" to hide from a11y tree. */
  title?: string;
}

/**
 * Buddy — the maker-bot mascot and the app's one memorable element
 * (ARCHITECTURE.md §16.4). An original character (red body, blue cap, gold
 * heart badge, rainbow collar, freckles), inlined as SVG so it scales from a
 * hero down to an icon and recolors from the tokens. The idle bob lives on
 * `.buddy` / `.buddy__shadow` (global.css) and is gated behind
 * prefers-reduced-motion.
 */
export function Mascot({ height = 322, className, style, title = "Buddy" }: MascotProps) {
  const raw = useId();
  const uid = raw.replace(/:/g, ""); // keep ids clean for url(#…) refs
  const clipId = `collarClip-${uid}`;
  const titleId = `buddyTitle-${uid}`;
  const decorative = title === "";

  return (
    <svg
      viewBox="0 0 260 320"
      height={height}
      className={className}
      style={style}
      role="img"
      aria-hidden={decorative || undefined}
      aria-labelledby={decorative ? undefined : titleId}
    >
      {!decorative && <title id={titleId}>{title}</title>}
      <clipPath id={clipId}>
        <rect x="96" y="146" width="68" height="16" rx="8" />
      </clipPath>

      {/* ground shadow */}
      <ellipse className="buddy__shadow" cx="130" cy="302" rx="64" ry="11" fill="#1b1b19" />

      <g className="buddy">
        {/* feet */}
        <rect x="90" y="262" width="30" height="30" rx="13" fill="#2e7cc2" />
        <rect x="140" y="262" width="30" height="30" rx="13" fill="#2e7cc2" />
        <rect x="90" y="285" width="30" height="7" rx="3.5" fill="#eaf2fb" />
        <rect x="140" y="285" width="30" height="7" rx="3.5" fill="#eaf2fb" />

        {/* torso */}
        <rect x="76" y="150" width="108" height="120" rx="42" fill="#de3b2c" />
        <rect x="90" y="162" width="34" height="20" rx="10" fill="#ffffff" opacity="0.14" />

        {/* arms + mitt hands */}
        <path d="M84 174 Q70 202 66 232" stroke="#de3b2c" strokeWidth="26" strokeLinecap="round" fill="none" />
        <path d="M176 174 Q198 150 206 120" stroke="#de3b2c" strokeWidth="26" strokeLinecap="round" fill="none" />
        <circle cx="66" cy="234" r="15" fill="#f7f7f3" stroke="#1b1b19" strokeWidth="2.5" />
        <circle cx="206" cy="118" r="15" fill="#f7f7f3" stroke="#1b1b19" strokeWidth="2.5" />

        {/* rainbow collar */}
        <g clipPath={`url(#${clipId})`}>
          <rect x="96" y="146" width="12" height="16" fill="#de3b2c" />
          <rect x="108" y="146" width="12" height="16" fill="#e8722e" />
          <rect x="120" y="146" width="12" height="16" fill="#edc24c" />
          <rect x="132" y="146" width="12" height="16" fill="#2e8b57" />
          <rect x="144" y="146" width="12" height="16" fill="#2e7cc2" />
          <rect x="156" y="146" width="12" height="16" fill="#7a5ea8" />
        </g>

        {/* gold heart badge */}
        <rect x="100" y="187" width="60" height="44" rx="12" fill="#edc24c" stroke="#1b1b19" strokeWidth="2.5" />
        <path
          d="M130 219 C123 213 117 208 117 202.5 C117 198 120.5 195 124.5 195 C127 195 129 196.5 130 198.5 C131 196.5 133 195 135.5 195 C139.5 195 143 198 143 202.5 C143 208 137 213 130 219 Z"
          fill="#de3b2c"
        />

        {/* head */}
        <rect x="80" y="100" width="12" height="26" rx="6" fill="#2e7cc2" />
        <rect x="168" y="100" width="12" height="26" rx="6" fill="#2e7cc2" />
        <rect x="88" y="70" width="84" height="82" rx="28" fill="#f7f7f3" stroke="#1b1b19" strokeWidth="3" />

        {/* cheeks + freckles */}
        <circle cx="101" cy="126" r="8" fill="#de3b2c" opacity="0.22" />
        <circle cx="159" cy="126" r="8" fill="#de3b2c" opacity="0.22" />
        <g fill="#1b1b19" opacity="0.4">
          <circle cx="99" cy="123" r="1.1" />
          <circle cx="104" cy="121" r="1.1" />
          <circle cx="102" cy="127" r="1.1" />
          <circle cx="161" cy="123" r="1.1" />
          <circle cx="156" cy="121" r="1.1" />
          <circle cx="158" cy="127" r="1.1" />
        </g>

        {/* eyes */}
        <ellipse cx="113" cy="108" rx="8" ry="10" fill="#1b1b19" />
        <ellipse cx="147" cy="108" rx="8" ry="10" fill="#1b1b19" />
        <circle cx="116" cy="104" r="2.6" fill="#ffffff" />
        <circle cx="150" cy="104" r="2.6" fill="#ffffff" />

        {/* smile */}
        <path d="M118 130 Q130 140 142 130" stroke="#1b1b19" strokeWidth="3" fill="none" strokeLinecap="round" />

        {/* cap */}
        <path d="M97 75 Q130 38 163 75 Z" fill="#2e7cc2" />
        <ellipse cx="150" cy="77" rx="24" ry="7" fill="#2e7cc2" />
        <path d="M99 74 Q130 58 161 74" stroke="#256aa8" strokeWidth="4" fill="none" strokeLinecap="round" />
        <rect x="128.4" y="43" width="3.2" height="14" rx="1.6" fill="#1b1b19" />
        <circle cx="130" cy="41" r="5" fill="#edc24c" stroke="#1b1b19" strokeWidth="1.5" />
      </g>
    </svg>
  );
}
