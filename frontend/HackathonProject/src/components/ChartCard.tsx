import type { ReactNode } from "react";
import "./ChartCard.css";

interface Props {
  title: string;
  children: ReactNode;
  /** Extra element rendered in the card header, e.g. a filter dropdown */
  action?: ReactNode;
  className?: string;
}

export default function ChartCard({ title, children, action, className }: Props) {
  return (
    <div className={`chart-card ${className ?? ""}`}>
      <div className="chart-card-header">
        <h3 className="chart-card-title">{title}</h3>
        {action && <div className="chart-card-action">{action}</div>}
      </div>
      <div className="chart-card-body">{children}</div>
    </div>
  );
}
