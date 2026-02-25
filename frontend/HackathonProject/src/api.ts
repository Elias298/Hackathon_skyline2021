/**
 * API service – talks to the FastAPI analytics backend.
 * Base URL defaults to the Vite env var VITE_BACKEND_URL or localhost:8000.
 */

const BASE = import.meta.env.VITE_BACKEND_URL ?? "http://localhost:8000";

async function get<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(`${BASE}${path}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v) url.searchParams.set(k, v);
    });
  }
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
  return res.json() as Promise<T>;
}

/* ── Types ─────────────────────────────────────────────────────── */

export interface SummaryData {
  success: boolean;
  total_users: number;
  total_responses: number;
  total_surveys: number;
  active_surveys: number;
}

export interface RegionData {
  success: boolean;
  data: Record<string, number>;
  total_users: number;
}

export interface CityData {
  success: boolean;
  data: Record<string, number>;
}

export interface TopicData {
  success: boolean;
  data: Record<string, number>;
  total_responses: number;
}

export interface TimePoint {
  date: string;
  count: number;
}
export interface OverTimeData {
  success: boolean;
  data: TimePoint[];
  granularity: string;
}

export interface StatusData {
  success: boolean;
  data: Record<string, number>;
}

export interface UtmData {
  success: boolean;
  data: Record<string, number>;
}

export interface SurveyListItem {
  id: string;
  title: string;
  slug: string;
  is_active: boolean;
}
export interface SurveyListData {
  success: boolean;
  data: SurveyListItem[];
}

export interface ResponsesPerSurveyItem {
  survey_id: string;
  title: string;
  count: number;
}
export interface ResponsesPerSurveyData {
  success: boolean;
  data: ResponsesPerSurveyItem[];
}

/* ── Fetch helpers ─────────────────────────────────────────────── */

export const fetchSummary = () => get<SummaryData>("/api/analytics/summary");

export const fetchUsersByRegion = () =>
  get<RegionData>("/api/analytics/users/by-region");

export const fetchUsersByCity = (region?: string) =>
  get<CityData>("/api/analytics/users/by-city", region ? { region } : undefined);

export const fetchUsersByTopic = (region?: string) =>
  get<TopicData>("/api/analytics/users/by-topic", region ? { region } : undefined);

export const fetchResponsesOverTime = (
  surveyId?: string,
  granularity: string = "day",
) =>
  get<OverTimeData>("/api/analytics/responses/over-time", {
    granularity,
    ...(surveyId ? { survey_id: surveyId } : {}),
  });

export const fetchResponsesByStatus = (surveyId?: string) =>
  get<StatusData>(
    "/api/analytics/responses/by-status",
    surveyId ? { survey_id: surveyId } : undefined,
  );

export const fetchUtmSources = () =>
  get<UtmData>("/api/analytics/users/by-utm-source");

export const fetchUtmCampaigns = () =>
  get<UtmData>("/api/analytics/users/by-utm-campaign");

export const fetchSurveysList = () =>
  get<SurveyListData>("/api/analytics/surveys");

export const fetchResponsesPerSurvey = () =>
  get<ResponsesPerSurveyData>("/api/analytics/responses/per-survey");
