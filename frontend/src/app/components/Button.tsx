import { Link } from "react-router-dom";
import type { ReactNode } from "react";
import styles from "./Button.module.css";

interface ButtonProps {
  variant?: "primary" | "secondary";
  size?: "sm" | "md";
  /** When set, renders as a router <Link>; otherwise a <button>. */
  to?: string;
  onClick?: () => void;
  type?: "button" | "submit";
  block?: boolean;
  children: ReactNode;
  className?: string;
}

/** The one button (§16.1): red primary with its glow, or a quiet secondary.
 *  Renders as a link or a button depending on whether `to` is given. */
export function Button({
  variant = "primary",
  size = "md",
  to,
  onClick,
  type = "button",
  block = false,
  children,
  className = "",
}: ButtonProps) {
  const cls = `${styles.btn} ${styles[variant]} ${styles[size]} ${block ? styles.block : ""} ${className}`;
  return to ? (
    <Link to={to} className={cls}>
      {children}
    </Link>
  ) : (
    <button type={type} className={cls} onClick={onClick}>
      {children}
    </button>
  );
}
