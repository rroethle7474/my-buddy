interface BrandMarkProps {
  size?: number;
}

/**
 * The My Buddy logo mark: a rounded square split red/blue — the two primary
 * brand colors (§16.1). Recolors from the tokens by construction.
 */
export function BrandMark({ size = 30 }: BrandMarkProps) {
  return (
    <span
      aria-hidden="true"
      style={{
        width: size,
        height: size,
        borderRadius: Math.round(size * 0.3),
        background:
          "linear-gradient(135deg, var(--red) 0 50%, var(--blue) 50% 100%)",
        flex: "0 0 auto",
        display: "block",
      }}
    />
  );
}
