import type { ReactNode } from "react";

interface Props {
  title: string;
  right?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function Card({ title, right, children, className = "" }: Props) {
  return (
    <section className={`card ${className}`}>
      <div className="card-header">
        <h3 className="card-title">{title}</h3>
        {right && <div className="card-right">{right}</div>}
      </div>
      <div className="card-body">{children}</div>
    </section>
  );
}

export function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  );
}
