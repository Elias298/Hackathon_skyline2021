/**
 * LebanonMap – A hand-crafted SVG map of Lebanon's governorates.
 *
 * Each region is a <path> drawn to approximate the real shape.
 * Regions are colored according to the value passed via `data` prop.
 *
 * The component uses a sequential color scale from light to saturated.
 */
import { useState, useMemo } from "react";
import "./LebanonMap.css";

/* ── Region path data (simplified outlines) ───────────────────── */
interface RegionPath {
  id: string;
  name: string;
  d: string; // SVG path
  labelX: number;
  labelY: number;
}

const REGIONS: RegionPath[] = [
  {
    id: "akkar",
    name: "Akkar",
    d: "M60,10 L100,8 L115,25 L110,55 L85,60 L60,45 Z",
    labelX: 85,
    labelY: 35,
  },
  {
    id: "north",
    name: "North",
    d: "M85,60 L110,55 L130,70 L135,100 L110,110 L80,95 L75,70 Z",
    labelX: 105,
    labelY: 85,
  },
  {
    id: "baalbek_hermel",
    name: "Baalbek-Hermel",
    d: "M130,70 L170,30 L200,60 L195,140 L160,170 L135,150 L135,100 Z",
    labelX: 163,
    labelY: 105,
  },
  {
    id: "mount_lebanon",
    name: "Mount Lebanon",
    d: "M75,110 L110,110 L135,150 L130,190 L105,210 L75,200 L65,160 L60,130 Z",
    labelX: 95,
    labelY: 160,
  },
  {
    id: "beirut",
    name: "Beirut",
    d: "M60,130 L75,125 L78,140 L70,150 L58,145 Z",
    labelX: 67,
    labelY: 138,
  },
  {
    id: "beqaa",
    name: "Beqaa",
    d: "M135,150 L160,170 L175,210 L165,250 L140,250 L120,230 L130,190 Z",
    labelX: 148,
    labelY: 210,
  },
  {
    id: "south",
    name: "South",
    d: "M65,200 L105,210 L120,230 L125,265 L100,285 L70,275 L55,240 Z",
    labelX: 90,
    labelY: 250,
  },
  {
    id: "nabatieh",
    name: "Nabatieh",
    d: "M125,265 L140,250 L165,250 L170,280 L145,310 L115,300 L100,285 Z",
    labelX: 138,
    labelY: 285,
  },
];

/* ── Colour helpers ───────────────────────────────────────────── */
const PALETTE = [
  "#e8f4f8",
  "#b3dce6",
  "#7ec4d4",
  "#49acc2",
  "#2698b0",
  "#0d7f98",
  "#066073",
  "#044450",
];

function colorForValue(value: number, max: number): string {
  if (max === 0) return PALETTE[0];
  const idx = Math.min(
    Math.floor((value / max) * (PALETTE.length - 1)),
    PALETTE.length - 1,
  );
  return PALETTE[idx];
}

/* ── Alias mapping (API region names → map ids) ───────────────── */
const ALIAS: Record<string, string> = {
  Akkar: "akkar",
  "North Lebanon": "north",
  North: "north",
  "Baalbek-Hermel": "baalbek_hermel",
  Baalbek: "baalbek_hermel",
  "Mount Lebanon": "mount_lebanon",
  Beirut: "beirut",
  Beqaa: "beqaa",
  "Bekaa": "beqaa",
  South: "south",
  "South Lebanon": "south",
  Nabatieh: "nabatieh",
  Nabatiyeh: "nabatieh",
};

function resolveId(apiName: string): string {
  return ALIAS[apiName] ?? apiName.toLowerCase().replace(/[\s-]+/g, "_");
}

/* ── Component ────────────────────────────────────────────────── */
interface Props {
  /** Map of region display-name → count */
  data: Record<string, number>;
  onRegionClick?: (regionName: string) => void;
  selectedRegion?: string | null;
}

export default function LebanonMap({ data, onRegionClick, selectedRegion }: Props) {
  const [hovered, setHovered] = useState<string | null>(null);

  // Resolve data keyed by internal id
  const resolved = useMemo(() => {
    const m: Record<string, { name: string; value: number }> = {};
    for (const [name, value] of Object.entries(data)) {
      m[resolveId(name)] = { name, value };
    }
    return m;
  }, [data]);

  const maxVal = useMemo(
    () => Math.max(1, ...Object.values(resolved).map((r) => r.value)),
    [resolved],
  );

  return (
    <div className="lebanon-map-wrapper">
      <svg viewBox="30 0 200 330" className="lebanon-map-svg">
        {REGIONS.map((r) => {
          const info = resolved[r.id];
          const value = info?.value ?? 0;
          const fill = colorForValue(value, maxVal);
          const isSelected = selectedRegion
            ? resolveId(selectedRegion) === r.id
            : false;
          const isHovered = hovered === r.id;

          return (
            <g
              key={r.id}
              className={`map-region ${isSelected ? "selected" : ""} ${isHovered ? "hovered" : ""}`}
              onClick={() => onRegionClick?.(info?.name ?? r.name)}
              onMouseEnter={() => setHovered(r.id)}
              onMouseLeave={() => setHovered(null)}
            >
              <path d={r.d} fill={fill} />
              <text x={r.labelX} y={r.labelY} className="region-label">
                {r.name}
              </text>
              {(isHovered || isSelected) && (
                <text
                  x={r.labelX}
                  y={r.labelY + 14}
                  className="region-value"
                >
                  {value.toLocaleString()}
                </text>
              )}
            </g>
          );
        })}
      </svg>

      {/* Legend */}
      <div className="map-legend">
        <span className="legend-label">0</span>
        <div className="legend-bar">
          {PALETTE.map((c) => (
            <span key={c} style={{ background: c }} />
          ))}
        </div>
        <span className="legend-label">{maxVal.toLocaleString()}</span>
      </div>
    </div>
  );
}
