import "./KpiCards.css";

interface KpiItem {
  label: string;
  value: number | string;
  icon: string;
  color: string;
}

interface Props {
  items: KpiItem[];
}

export default function KpiCards({ items }: Props) {
  return (
    <div className="kpi-grid">
      {items.map((k) => (
        <div key={k.label} className="kpi-card" style={{ borderTopColor: k.color }}>
          <span className="kpi-icon">{k.icon}</span>
          <div className="kpi-body">
            <span className="kpi-value">{typeof k.value === "number" ? k.value.toLocaleString() : k.value}</span>
            <span className="kpi-label">{k.label}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
