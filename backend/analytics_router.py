"""
Analytics router for user statistics endpoints.
"""

import logging
from typing import Any
from fastapi import APIRouter, HTTPException
from utils.db_wrapper import get_users_collection, get_responses_collection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["analytics"])


@router.get("/total")
async def get_total_users() -> dict[str, Any]:
    """
    Get the total number of users in the database.
    
    Returns:
        dict with:
            - total (int): Total number of users
            - success (bool): Whether the operation was successful
    
    Example:
        >>> GET /api/users/total
        >>> {"success": true, "total": 55}
    """
    try:
        users_collection = get_users_collection()
        total = await users_collection.count_documents({})
        
        logger.info(f"Total users: {total}")
        
        return {
            "success": True,
            "total": total
        }
    except Exception as e:
        logger.error(f"Error getting total users: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/by-region")
async def get_users_by_region() -> dict[str, Any]:
    """
    Get the number of users per region.
    
    Returns:
        dict with:
            - success (bool): Whether the operation was successful
            - data (dict): Dictionary mapping region names to user counts
            - total_users (int): Total number of users with region data
    
    Example:
        >>> GET /api/users/by-region
        >>> {
        >>>   "success": true,
        >>>   "data": {
        >>>     "Beirut": 30,
        >>>     "Mount Lebanon": 15,
        >>>     "North": 10
        >>>   },
        >>>   "total_users": 55
        >>> }
    """
    try:
        users_collection = get_users_collection()
        
        # Aggregate users by region
        # Use MongoDB aggregation to unwind the geo_region array and count
        pipeline = [
            # Unwind the geo_region array (since it's a list field)
            {"$unwind": "$geo_region"},
            # Group by region and count
            {"$group": {
                "_id": "$geo_region",
                "count": {"$sum": 1}
            }},
            # Sort by count descending
            {"$sort": {"count": -1}}
        ]
        
        result = await users_collection.aggregate(pipeline).to_list(length=None)
        
        # Convert to dictionary format
        region_counts = {item["_id"]: item["count"] for item in result if item["_id"]}
        
        # Get total users with region data
        total_users = await users_collection.count_documents({"geo_region": {"$exists": True, "$ne": []}})
        
        logger.info(f"Users by region: {len(region_counts)} regions, {total_users} total users")
        
        return {
            "success": True,
            "data": region_counts,
            "total_users": total_users
        }
    except Exception as e:
        logger.error(f"Error getting users by region: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/by-topic")
async def get_users_by_topic() -> dict[str, Any]:
    """
    Get the number of users per topic (training track).
    
    This endpoint analyzes survey responses to count how many users
    selected each training track option.
    
    Returns:
        dict with:
            - success (bool): Whether the operation was successful
            - data (dict): Dictionary mapping topic/training track to user counts
            - total_responses (int): Total number of responses with topic data
    
    Example:
        >>> GET /api/users/by-topic
        >>> {
        >>>   "success": true,
        >>>   "data": {
        >>>     "microsoft_ai_academy": 25,
        >>>     "lebanon_coding": 20,
        >>>     "digital_literacy": 15,
        >>>     "oracle_technical_leadership": 10,
        >>>     "national_cybersecurity": 4
        >>>   },
        >>>   "total_responses": 74
        >>> }
    """
    try:
        responses_collection = get_responses_collection()
        
        # Aggregate responses by training_track field
        # The training_track is stored in the responses.training_track field
        pipeline = [
            # Filter only responses that have the training_track field
            {"$match": {
                "responses.training_track": {"$exists": True, "$ne": None}
            }},
            # Group by training_track and count
            {"$group": {
                "_id": "$responses.training_track",
                "count": {"$sum": 1}
            }},
            # Sort by count descending
            {"$sort": {"count": -1}}
        ]
        
        result = await responses_collection.aggregate(pipeline).to_list(length=None)
        
        # Convert to dictionary format with friendly labels
        topic_labels = {
            "oracle_technical_leadership": "Technical Leadership (Oracle)",
            "lebanon_coding": "Lebanon Coding",
            "microsoft_ai_academy": "AI Academy (Microsoft)",
            "digital_literacy": "Digital Literacy & Inclusion",
            "national_cybersecurity": "National Cybersecurity"
        }
        
        topic_counts = {}
        for item in result:
            if item["_id"]:
                # Use the friendly label if available, otherwise use the raw value
                label = topic_labels.get(item["_id"], item["_id"])
                topic_counts[label] = item["count"]
        
        # Get total responses with topic data
        total_responses = await responses_collection.count_documents({
            "responses.training_track": {"$exists": True, "$ne": None}
        })
        
        logger.info(f"Users by topic: {len(topic_counts)} topics, {total_responses} total responses")
        
        return {
            "success": True,
            "data": topic_counts,
            "total_responses": total_responses
        }
    except Exception as e:
        logger.error(f"Error getting users by topic: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
