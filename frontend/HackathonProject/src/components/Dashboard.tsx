import { useState, useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
  AreaChart,
  Area,
  CartesianGrid,
} from "recharts";

import {
  fetchSummary,
  fetchUsersByRegion,
  fetchUsersByTopic,
  fetchResponsesOverTime,
  fetchResponsesByStatus,
  fetchUtmSources,
  fetchResponsesPerSurvey,
  fetchSurveysList,
  fetchUsersByCity,
} from "../api";
import { useAsync } from "../hooks";

import KpiCards from "./KpiCards";
import ChartCard from "./ChartCard";
import LebanonMap from "./LebanonMap";
import FilterBar, { FilterSelect } from "./FilterBar";
import { Loader, ErrorBox } from "./StatusOverlay";

import "./Dashboard.css";

/* ── Colour palettes ──────────────────────────────────────────── */
const BAR_COLORS = ["#0d7f98", "#2698b0", "#49acc2", "#7ec4d4", "#b3dce6"];
const PIE_COLORS = ["#0d7f98", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6", "#ec4899"];
const AREA_GRADIENT = ["#0d7f98", "#b3dce6"];
const TOPIC_COLORS = ["#6366f1", "#f59e0b", "#10b981", "#ef4444", "#0ea5e9"];

/* helper: dict → array for Recharts */
function dictToArr(d: Record<string, number>) {
  return Object.entries(d).map(([name, value]) => ({ name, value }));
}

export default function Dashboard() {
  /* ── Filters ─────────────────────────────────────────────────── */
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null);
  const [granularity, setGranularity] = useState("day");
  const [surveyFilter, setSurveyFilter] = useState("");

  /* ── Data fetching ───────────────────────────────────────────── */
  const summary = useAsync(fetchSummary, []);
  const regions = useAsync(fetchUsersByRegion, []);
  const topics = useAsync(
    () => fetchUsersByTopic(selectedRegion ?? undefined),
    [selectedRegion],
  );
  const overTime = useAsync(
    () => fetchResponsesOverTime(surveyFilter || undefined, granularity),
    [surveyFilter, granularity],
  );
  const statuses = useAsync(
    () => fetchResponsesByStatus(surveyFilter || undefined),
    [surveyFilter],
  );
  const utmSources = useAsync(fetchUtmSources, []);
  const perSurvey = useAsync(fetchResponsesPerSurvey, []);
  const surveys = useAsync(fetchSurveysList, []);
  const cities = useAsync(
    () => fetchUsersByCity(selectedRegion ?? undefined),
    [selectedRegion],
  );

  /* ── Derived ─────────────────────────────────────────────────── */
  const regionData = useMemo(
    () => (regions.data?.data ? dictToArr(regions.data.data) : []),
    [regions.data],
  );
  const topicData = useMemo(
    () => (topics.data?.data ? dictToArr(topics.data.data) : []),
    [topics.data],
  );
  const statusData = useMemo(
    () => (statuses.data?.data ? dictToArr(statuses.data.data) : []),
    [statuses.data],
  );
  const utmData = useMemo(
    () => (utmSources.data?.data ? dictToArr(utmSources.data.data) : []),
    [utmSources.data],
  );
  const cityData = useMemo(
    () => (cities.data?.data ? dictToArr(cities.data.data) : []),
    [cities.data],
  );

  const surveyOptions = useMemo(() => {
    const opts = [{ value: "", label: "All Surveys" }];
    if (surveys.data?.data) {
      surveys.data.data.forEach((s) =>
        opts.push({ value: s.id, label: s.title }),
      );
    }
    return opts;
  }, [surveys.data]);

  const regionOptions = useMemo(() => {
    const opts = [{ value: "", label: "All Regions" }];
    if (regions.data?.data) {
      Object.keys(regions.data.data).forEach((r) =>
        opts.push({ value: r, label: r }),
      );
    }
    return opts;
  }, [regions.data]);

  /* ── Handle region click on the map ─────────────────────────── */
  function handleRegionClick(name: string) {
    setSelectedRegion((prev) => (prev === name ? null : name));
  }

  /* ── Render ──────────────────────────────────────────────────── */
  return (
    <div className="dashboard">
      {/* ── KPI row ─────────────────────────────────────────────── */}
      {summary.loading ? (
        <Loader text="Loading summary…" />
      ) : summary.error ? (
        <ErrorBox message={summary.error} />
      ) : summary.data ? (
        <KpiCards
          items={[
            {
              label: "Total Users",
              value: summary.data.total_users,
              icon: "👥",
              color: "#0d7f98",
            },
            {
              label: "Total Responses",
              value: summary.data.total_responses,
              icon: "📝",
              color: "#f59e0b",
            },
            {
              label: "Surveys",
              value: summary.data.total_surveys,
              icon: "📊",
              color: "#10b981",
            },
            {
              label: "Active Surveys",
              value: summary.data.active_surveys,
              icon: "🟢",
              color: "#6366f1",
            },
          ]}
        />
      ) : null}

      {/* ── Filters ─────────────────────────────────────────────── */}
      <FilterBar>
        <FilterSelect
          id="f-region"
          label="Region"
          value={selectedRegion ?? ""}
          options={regionOptions}
          onChange={(v) => setSelectedRegion(v || null)}
        />
        <FilterSelect
          id="f-survey"
          label="Survey"
          value={surveyFilter}
          options={surveyOptions}
          onChange={setSurveyFilter}
        />
        <FilterSelect
          id="f-granularity"
          label="Time Granularity"
          value={granularity}
          options={[
            { value: "day", label: "Daily" },
            { value: "week", label: "Weekly" },
            { value: "month", label: "Monthly" },
          ]}
          onChange={setGranularity}
        />
      </FilterBar>

      {/* ── Main grid ───────────────────────────────────────────── */}
      <div className="dashboard-grid">
        {/* ── MAP ──────────────── */}
        <ChartCard title="Users by Region" className="span-map">
          {regions.loading ? (
            <Loader />
          ) : regions.error ? (
            <ErrorBox message={regions.error} />
          ) : (
            <LebanonMap
              data={regions.data?.data ?? {}}
              onRegionClick={handleRegionClick}
              selectedRegion={selectedRegion}
            />
          )}
        </ChartCard>

        {/* ── BAR: Region breakdown ──────── */}
        <ChartCard title="Users per Region">
          {regions.loading ? (
            <Loader />
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={regionData} layout="vertical" margin={{ left: 10 }}>
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={110}
                  tick={{ fontSize: 11 }}
                />
                <Tooltip />
                <Bar dataKey="value" radius={[0, 6, 6, 0]}>
                  {regionData.map((_, i) => (
                    <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* ── PIE: Topics ──────── */}
        <ChartCard
          title={`Users by Topic${selectedRegion ? ` – ${selectedRegion}` : ""}`}
        >
          {topics.loading ? (
            <Loader />
          ) : topicData.length === 0 ? (
            <span className="no-data">No topic data</span>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={topicData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  innerRadius={40}
                  paddingAngle={3}
                  label={({ name, percent }) =>
                    `${name.split(" ")[0]} ${(percent * 100).toFixed(0)}%`
                  }
                  labelLine={false}
                >
                  {topicData.map((_, i) => (
                    <Cell key={i} fill={TOPIC_COLORS[i % TOPIC_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend
                  verticalAlign="bottom"
                  wrapperStyle={{ fontSize: "0.72rem" }}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* ── AREA: Responses Over Time ──────── */}
        <ChartCard title="Responses Over Time" className="span-wide">
          {overTime.loading ? (
            <Loader />
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={overTime.data?.data ?? []}>
                <defs>
                  <linearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={AREA_GRADIENT[0]} stopOpacity={0.4} />
                    <stop offset="100%" stopColor={AREA_GRADIENT[1]} stopOpacity={0.05} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="count"
                  stroke={AREA_GRADIENT[0]}
                  fill="url(#areaFill)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* ── PIE: Submission Status ──────── */}
        <ChartCard title="Submission Status">
          {statuses.loading ? (
            <Loader />
          ) : statusData.length === 0 ? (
            <span className="no-data">No status data</span>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={statusData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={85}
                  label={({ name, percent }) =>
                    `${name} ${(percent * 100).toFixed(0)}%`
                  }
                >
                  {statusData.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: "0.75rem" }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* ── BAR: Responses per Survey ──────── */}
        <ChartCard title="Responses per Survey">
          {perSurvey.loading ? (
            <Loader />
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={perSurvey.data?.data ?? []}>
                <XAxis
                  dataKey="title"
                  tick={{ fontSize: 10 }}
                  interval={0}
                  angle={-25}
                  textAnchor="end"
                  height={60}
                />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {(perSurvey.data?.data ?? []).map((_, i) => (
                    <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* ── BAR: UTM Sources ──────── */}
        <ChartCard title="Traffic Sources (UTM)">
          {utmSources.loading ? (
            <Loader />
          ) : utmData.length === 0 ? (
            <span className="no-data">No UTM data</span>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={utmData}>
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="value" radius={[6, 6, 0, 0]} fill="#f59e0b" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* ── BAR: Cities (filtered by region) ──────── */}
        <ChartCard
          title={`Users by City${selectedRegion ? ` – ${selectedRegion}` : ""}`}
        >
          {cities.loading ? (
            <Loader />
          ) : cityData.length === 0 ? (
            <span className="no-data">Select a region or no city data</span>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={cityData} layout="vertical" margin={{ left: 10 }}>
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={100}
                  tick={{ fontSize: 11 }}
                />
                <Tooltip />
                <Bar dataKey="value" radius={[0, 6, 6, 0]} fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>
    </div>
  );
}
