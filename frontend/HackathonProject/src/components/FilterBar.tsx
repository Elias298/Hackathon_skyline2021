import "./FilterBar.css";

export interface FilterOption {
  value: string;
  label: string;
}

interface SelectProps {
  id: string;
  label: string;
  value: string;
  options: FilterOption[];
  onChange: (v: string) => void;
}

export function FilterSelect({ id, label, value, options, onChange }: SelectProps) {
  return (
    <div className="filter-item">
      <label htmlFor={id} className="filter-label">
        {label}
      </label>
      <select
        id={id}
        className="filter-select"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}

interface BarProps {
  children: React.ReactNode;
}

export default function FilterBar({ children }: BarProps) {
  return <div className="filter-bar">{children}</div>;
}
