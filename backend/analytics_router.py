"""
Analytics router for user statistics endpoints.
"""

import logging
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from utils.db_wrapper import (
    get_users_collection,
    get_responses_collection,
    get_survey_collection,
    search_users,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


# ── Summary KPI card ───────────────────────────────────────────────
@router.get("/summary")
async def get_dashboard_summary() -> dict[str, Any]:
    """Return high-level KPIs for the dashboard header cards."""
    try:
        users_col = get_users_collection()
        responses_col = get_responses_collection()
        surveys_col = get_survey_collection()

        total_users = await users_col.count_documents({})
        total_responses = await responses_col.count_documents({})
        total_surveys = await surveys_col.count_documents({})
        active_surveys = await surveys_col.count_documents({"is_active": True})

        return {
            "success": True,
            "total_users": total_users,
            "total_responses": total_responses,
            "total_surveys": total_surveys,
            "active_surveys": active_surveys,
        }
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── User search ────────────────────────────────────────────────
@router.get("/users/search")
async def search_users_endpoint(
    q: str = Query("", description="Search by phone, name, or email"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
) -> dict[str, Any]:
    """Search users by phone number, name, or email."""
    if not q or len(q.strip()) < 2:
        return {"success": True, "data": [], "message": "Query too short (min 2 chars)"}
    try:
        results = await search_users(q.strip(), limit=limit)
        return {"success": True, "data": results, "total": len(results)}
    except Exception as e:
        logger.error(f"Error searching users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Total users (kept for backwards compat) ───────────────────────
@router.get("/users/total")
async def get_total_users() -> dict[str, Any]:
    try:
        users_collection = get_users_collection()
        total = await users_collection.count_documents({})
        return {"success": True, "total": total}
    except Exception as e:
        logger.error(f"Error getting total users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Users by region ───────────────────────────────────────────────
@router.get("/users/by-region")
async def get_users_by_region() -> dict[str, Any]:
    try:
        users_collection = get_users_collection()
        pipeline = [
            {"$unwind": "$geo_region"},
            {"$group": {"_id": "$geo_region", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        result = await users_collection.aggregate(pipeline).to_list(length=None)
        region_counts = {item["_id"]: item["count"] for item in result if item["_id"]}
        total_users = await users_collection.count_documents(
            {"geo_region": {"$exists": True, "$ne": []}}
        )
        return {"success": True, "data": region_counts, "total_users": total_users}
    except Exception as e:
        logger.error(f"Error getting users by region: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Users by city ─────────────────────────────────────────────────
@router.get("/users/by-city")
async def get_users_by_city(
    region: Optional[str] = Query(None, description="Filter by region"),
) -> dict[str, Any]:
    try:
        users_collection = get_users_collection()
        match_stage: dict[str, Any] = {}
        if region:
            match_stage["geo_region"] = region
        pipeline: list[dict[str, Any]] = []
        if match_stage:
            pipeline.append({"$match": match_stage})
        pipeline += [
            {"$unwind": "$geo_city"},
            {"$group": {"_id": "$geo_city", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        result = await users_collection.aggregate(pipeline).to_list(length=None)
        city_counts = {item["_id"]: item["count"] for item in result if item["_id"]}
        return {"success": True, "data": city_counts}
    except Exception as e:
        logger.error(f"Error getting users by city: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Users by topic / training track ──────────────────────────────
@router.get("/users/by-topic")
async def get_users_by_topic(
    region: Optional[str] = Query(None),
) -> dict[str, Any]:
    try:
        responses_collection = get_responses_collection()

        match_stage: dict[str, Any] = {
            "responses.training_track": {"$exists": True, "$ne": None}
        }
        if region:
            match_stage["geo_region"] = region

        pipeline = [
            {"$match": match_stage},
            {"$group": {"_id": "$responses.training_track", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        result = await responses_collection.aggregate(pipeline).to_list(length=None)

        topic_labels = {
            "oracle_technical_leadership": "Technical Leadership (Oracle)",
            "lebanon_coding": "Lebanon Coding",
            "microsoft_ai_academy": "AI Academy (Microsoft)",
            "digital_literacy": "Digital Literacy & Inclusion",
            "national_cybersecurity": "National Cybersecurity",
        }
        topic_counts = {}
        for item in result:
            if item["_id"]:
                label = topic_labels.get(item["_id"], item["_id"])
                topic_counts[label] = item["count"]

        total_responses = await responses_collection.count_documents(match_stage)
        return {
            "success": True,
            "data": topic_counts,
            "total_responses": total_responses,
        }
    except Exception as e:
        logger.error(f"Error getting users by topic: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Responses over time (for line / area chart) ──────────────────
@router.get("/responses/over-time")
async def get_responses_over_time(
    survey_id: Optional[str] = Query(None),
    granularity: str = Query("day", pattern="^(day|week|month)$"),
) -> dict[str, Any]:
    """Return response counts bucketed by day/week/month."""
    try:
        responses_collection = get_responses_collection()

        match_stage: dict[str, Any] = {}
        if survey_id:
            match_stage["survey_id"] = survey_id

        date_fmt = {
            "day": "%Y-%m-%d",
            "week": "%Y-W%V",
            "month": "%Y-%m",
        }

        pipeline: list[dict[str, Any]] = []
        if match_stage:
            pipeline.append({"$match": match_stage})
        pipeline += [
            {
                "$group": {
                    "_id": {"$dateToString": {"format": date_fmt[granularity], "date": "$created_at"}},
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        result = await responses_collection.aggregate(pipeline).to_list(length=None)
        data = [{"date": r["_id"], "count": r["count"]} for r in result if r["_id"]]
        return {"success": True, "data": data, "granularity": granularity}
    except Exception as e:
        logger.error(f"Error getting responses over time: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Submission status breakdown (pie chart) ───────────────────────
@router.get("/responses/by-status")
async def get_responses_by_status(
    survey_id: Optional[str] = Query(None),
) -> dict[str, Any]:
    try:
        responses_collection = get_responses_collection()
        match_stage: dict[str, Any] = {}
        if survey_id:
            match_stage["survey_id"] = survey_id

        pipeline: list[dict[str, Any]] = []
        if match_stage:
            pipeline.append({"$match": match_stage})
        pipeline += [
            {"$group": {"_id": "$submission_status", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        result = await responses_collection.aggregate(pipeline).to_list(length=None)
        data = {r["_id"]: r["count"] for r in result if r["_id"]}
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Error getting responses by status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── UTM source breakdown (bar chart) ─────────────────────────────
@router.get("/users/by-utm-source")
async def get_users_by_utm_source() -> dict[str, Any]:
    try:
        users_collection = get_users_collection()
        pipeline = [
            {"$unwind": "$utm_source"},
            {"$group": {"_id": "$utm_source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        result = await users_collection.aggregate(pipeline).to_list(length=None)
        data = {r["_id"]: r["count"] for r in result if r["_id"]}
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Error getting users by UTM source: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── UTM campaign breakdown ───────────────────────────────────────
@router.get("/users/by-utm-campaign")
async def get_users_by_utm_campaign() -> dict[str, Any]:
    try:
        users_collection = get_users_collection()
        pipeline = [
            {"$unwind": "$utm_campaign"},
            {"$group": {"_id": "$utm_campaign", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        result = await users_collection.aggregate(pipeline).to_list(length=None)
        data = {r["_id"]: r["count"] for r in result if r["_id"]}
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Error getting users by UTM campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Surveys list ─────────────────────────────────────────────────
@router.get("/surveys")
async def get_surveys_list() -> dict[str, Any]:
    """Return a compact list of all surveys (id, title, slug, is_active)."""
    try:
        surveys_col = get_survey_collection()
        surveys = await surveys_col.find(
            {},
            {"id": 1, "title": 1, "slug": 1, "is_active": 1, "_id": 0},
        ).to_list(length=None)
        return {"success": True, "data": surveys}
    except Exception as e:
        logger.error(f"Error listing surveys: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Responses per survey (bar chart) ─────────────────────────────
@router.get("/responses/per-survey")
async def get_responses_per_survey() -> dict[str, Any]:
    """Count responses grouped by survey_id."""
    try:
        responses_col = get_responses_collection()
        surveys_col = get_survey_collection()

        pipeline = [
            {"$group": {"_id": "$survey_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        result = await responses_col.aggregate(pipeline).to_list(length=None)

        # Resolve survey titles
        survey_ids = [r["_id"] for r in result if r["_id"]]
        surveys = await surveys_col.find(
            {"id": {"$in": survey_ids}}, {"id": 1, "title": 1, "_id": 0}
        ).to_list(length=None)
        title_map = {s["id"]: s["title"] for s in surveys}

        data = [
            {
                "survey_id": r["_id"],
                "title": title_map.get(r["_id"], r["_id"]),
                "count": r["count"],
            }
            for r in result
            if r["_id"]
        ]
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Error getting responses per survey: {e}")
        raise HTTPException(status_code=500, detail=str(e))
