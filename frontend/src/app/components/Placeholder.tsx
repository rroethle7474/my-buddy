import type { ReactNode } from "react";
import { Mascot } from "../shell/Mascot";
import styles from "./Placeholder.module.css";

/** A centered, on-brand panel used for not-found and for the routes that
 *  mechanic-ui (agent D) will fill in later. */
export function Placeholder({
  title,
  body,
  children,
}: {
  title: string;
  body: string;
  children?: ReactNode;
}) {
  return (
    <div className={styles.wrap}>
      <Mascot height={150} title="" className={styles.mascot} />
      <h1 className={styles.title}>{title}</h1>
      <p className={styles.body}>{body}</p>
      {children && <div className={styles.actions}>{children}</div>}
    </div>
  );
}
