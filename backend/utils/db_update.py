"""
Database update utilities for syncing data from API to database.
"""

import logging
import httpx
from typing import Any, Optional
from .db_wrapper import (
    get_survey_collection,
    create_survey,
    get_responses_collection,
    create_survey_response,
    get_most_recent_response,
    update_user_from_response
)
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API base URL - adjust this to your actual API URL
API_BASE_URL = os.getenv("API_BASE_URL","")  # Update this with your actual API base URL
API_KEY = os.getenv("API_KEY")  # Update this with your actual API key if needed


async def sync_all_data() -> dict[str, Any]:
    """
    Main orchestration function to sync all data from API to database.
    
    This function:
    1. Syncs new surveys from the API
    2. Gets all surveys from the database
    3. Syncs new responses for each survey
    
    Returns:
        dict[str, Any]: A dictionary containing:
            - success (bool): Whether the overall operation was successful
            - surveys_result (dict): Result from survey sync
            - responses_results (list): List of results from each survey's response sync
            - total_responses_added (int): Total number of responses added across all surveys
            - message (str): Status message
            
    Example:
        >>> result = await sync_all_data()
        >>> print(f"Added {result['surveys_result']['surveys_added']} surveys")
        >>> print(f"Added {result['total_responses_added']} responses")
    """
    logger.info("Starting complete data sync...")
    
    try:
        # Step 1: Sync surveys
        logger.info("Step 1: Syncing surveys from API")
        surveys_result = await sync_surveys_from_api()
        
        if not surveys_result["success"]:
            logger.error("Failed to sync surveys")
            return {
                "success": False,
                "surveys_result": surveys_result,
                "responses_results": [],
                "total_responses_added": 0,
                "message": "Failed to sync surveys"
            }
        
        logger.info(f"Survey sync completed: {surveys_result['surveys_added']} surveys added")
        
        # Step 2: Get all surveys from database
        logger.info("Step 2: Fetching all surveys from database")
        survey_collection = get_survey_collection()
        all_surveys = await survey_collection.find({}, {"id": 1, "title": 1}).to_list(length=None)
        
        logger.info(f"Found {len(all_surveys)} surveys in database")
        
        # Step 3: Sync responses for each survey
        logger.info("Step 3: Syncing responses for all surveys")
        responses_results = []
        total_responses_added = 0
        failed_syncs = 0
        
        for survey in all_surveys:
            survey_id = survey.get("id")
            survey_title = survey.get("title", "N/A")
            
            if not survey_id:
                logger.warning(f"Survey missing ID, skipping: {survey_title}")
                continue
            
            logger.info(f"Syncing responses for survey: {survey_title} (ID: {survey_id})")
            
            response_result = await sync_responses_from_api(survey_id)
            responses_results.append({
                "survey_id": survey_id,
                "survey_title": survey_title,
                "result": response_result
            })
            
            if response_result["success"]:
                total_responses_added += response_result["responses_added"]
                logger.info(
                    f"Added {response_result['responses_added']} responses for survey: {survey_title}"
                )
            else:
                failed_syncs += 1
                logger.warning(f"Failed to sync responses for survey: {survey_title}")
        
        logger.info(f"Response sync completed: {total_responses_added} total responses added")
        
        if failed_syncs > 0:
            logger.warning(f"{failed_syncs} surveys had failed response syncs")
        
        return {
            "success": True,
            "surveys_result": surveys_result,
            "responses_results": responses_results,
            "total_responses_added": total_responses_added,
            "surveys_with_failed_sync": failed_syncs,
            "message": (
                f"Sync completed: {surveys_result['surveys_added']} surveys added, "
                f"{total_responses_added} responses added"
            )
        }
        
    except Exception as e:
        logger.error(f"Error during complete data sync: {e}")
        return {
            "success": False,
            "surveys_result": {},
            "responses_results": [],
            "total_responses_added": 0,
            "message": f"Error: {str(e)}"
        }


async def sync_surveys_from_api() -> dict[str, Any]:
    """
    Sync surveys from the API to the database.
    
    This function:
    1. Gets the current count of surveys in the database
    2. Calls the /api/surveys endpoint to get the total number of surveys
    3. If there are new surveys (API total > DB count), fetches all surveys from the API
    4. Adds the new surveys to the database
    
    Returns:
        dict[str, Any]: A dictionary containing:
            - success (bool): Whether the operation was successful
            - surveys_added (int): Number of new surveys added
            - total_api_surveys (int): Total surveys from API
            - total_db_surveys (int): Total surveys in database before sync
            - message (str): Status message
            
    Example:
        >>> result = await sync_surveys_from_api()
        >>> print(f"Added {result['surveys_added']} new surveys")
    """
    base_url = API_BASE_URL
    survey_collection = get_survey_collection()
    
    try:
        # Get current count of surveys in the database
        db_survey_count = await survey_collection.count_documents({})
        logger.info(f"Current surveys in database: {db_survey_count}")
        
        # Call API to get total number of surveys
        # Prepare headers with API key
        headers = {}
        if API_KEY:
            headers["X-API-Key"] = API_KEY
        
        async with httpx.AsyncClient() as client:
            # First, get the first page to check the total count
            response = await client.get(
                f"{base_url}/api/surveys",
                params={"page": 1, "limit": 100},  # Using max limit to minimize requests
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("success"):
                logger.error(f"API returned unsuccessful response: {data}")
                return {
                    "success": False,
                    "surveys_added": 0,
                    "total_api_surveys": 0,
                    "total_db_surveys": db_survey_count,
                    "message": "API request was not successful"
                }
            
            pagination = data["data"]["pagination"]
            total_api_surveys = pagination["total"]
            total_pages = pagination["totalPages"]
            
            logger.info(f"Total surveys from API: {total_api_surveys}")
            
            # Check if there are new surveys
            if total_api_surveys <= db_survey_count:
                logger.info("No new surveys to add")
                return {
                    "success": True,
                    "surveys_added": 0,
                    "total_api_surveys": total_api_surveys,
                    "total_db_surveys": db_survey_count,
                    "message": "No new surveys to add"
                }
            
            # Fetch all surveys from API (handling pagination)
            all_api_surveys = []
            all_api_surveys.extend(data["data"]["surveys"])
            
            # Fetch remaining pages if any
            for page in range(2, total_pages + 1):
                logger.info(f"Fetching page {page} of {total_pages}")
                response = await client.get(
                    f"{base_url}/api/surveys",
                    params={"page": page, "limit": 100},
                    headers=headers
                )
                response.raise_for_status()
                page_data = response.json()
                
                if page_data.get("success"):
                    all_api_surveys.extend(page_data["data"]["surveys"])
            
            logger.info(f"Fetched {len(all_api_surveys)} surveys from API")
            
            # Get existing survey IDs from database to avoid duplicates
            existing_surveys = await survey_collection.find({}, {"id": 1}).to_list(length=None)
            existing_survey_ids = {survey["id"] for survey in existing_surveys}
            
            # Filter out surveys that already exist in the database
            new_surveys = [survey for survey in all_api_surveys if survey["id"] not in existing_survey_ids]
            
            logger.info(f"Found {len(new_surveys)} new surveys to add")
            
            # Add new surveys to database
            surveys_added = 0
            for survey in new_surveys:
                # Convert datetime strings to datetime objects if needed
                survey_data = prepare_survey_for_db(survey)
                
                result = await create_survey(survey_data)
                if result:
                    surveys_added += 1
                    logger.info(f"Added survey: {survey_data.get('title', 'N/A')}")
                else:
                    logger.warning(f"Failed to add survey: {survey_data.get('title', 'N/A')}")
            
            logger.info(f"Successfully added {surveys_added} new surveys")
            
            return {
                "success": True,
                "surveys_added": surveys_added,
                "total_api_surveys": total_api_surveys,
                "total_db_surveys": db_survey_count,
                "message": f"Successfully added {surveys_added} new surveys"
            }
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error occurred while syncing surveys: {e}")
        return {
            "success": False,
            "surveys_added": 0,
            "total_api_surveys": 0,
            "total_db_surveys": db_survey_count,
            "message": f"HTTP error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error syncing surveys from API: {e}")
        return {
            "success": False,
            "surveys_added": 0,
            "total_api_surveys": 0,
            "total_db_surveys": db_survey_count,
            "message": f"Error: {str(e)}"
        }


async def sync_responses_from_api(survey_id: str) -> dict[str, Any]:
    """
    Sync survey responses from the API to the database for a specific survey.
    
    This function:
    1. Gets the most recent response date from the database for the given survey
    2. Calls /api/responses/last-response-date to check if there are newer responses
    3. If there are newer responses, fetches all responses after the DB date from the API
    4. Adds the new responses to the database
    5. Updates user records in the users collection based on response data
    
    Args:
        survey_id: The UUID of the survey to sync responses for
        
    Returns:
        dict[str, Any]: A dictionary containing:
            - success (bool): Whether the operation was successful
            - responses_added (int): Number of new responses added
            - users_updated (int): Number of user records updated
            - last_api_response_date (str): Date of last response from API
            - last_db_response_date (str): Date of last response in DB before sync
            - message (str): Status message
            
    Example:
        >>> result = await sync_responses_from_api("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
        >>> print(f"Added {result['responses_added']} new responses")
        >>> print(f"Updated {result['users_updated']} user records")
    """
    base_url = API_BASE_URL
    responses_collection = get_responses_collection()
    
    try:
        # Get the most recent response from the database for this survey
        db_last_response = await get_most_recent_response(survey_id)
        db_last_date = None
        if db_last_response and "created_at" in db_last_response:
            db_last_date = db_last_response["created_at"]
            if isinstance(db_last_date, datetime):
                # Ensure db_last_date is timezone-aware for comparison
                if db_last_date.tzinfo is None:
                    from datetime import timezone
                    db_last_date = db_last_date.replace(tzinfo=timezone.utc)
                db_last_date_str = db_last_date.isoformat()
            else:
                db_last_date_str = str(db_last_date)
            logger.info(f"Last response in DB for survey {survey_id}: {db_last_date_str}")
        else:
            logger.info(f"No responses found in DB for survey {survey_id}")
            db_last_date_str = None
        
        # Prepare headers with API key
        headers = {}
        if API_KEY:
            headers["X-API-Key"] = API_KEY
        
        async with httpx.AsyncClient() as client:
            # Check the last response date from the API
            last_date_response = await client.get(
                f"{base_url}/api/responses/last-response-date",
                headers=headers
            )
            last_date_response.raise_for_status()
            last_date_data = last_date_response.json()
            
            if not last_date_data.get("success"):
                logger.error(f"API returned unsuccessful response: {last_date_data}")
                return {
                    "success": False,
                    "responses_added": 0,
                    "users_updated": 0,
                    "last_api_response_date": None,
                    "last_db_response_date": db_last_date_str,
                    "message": "API request was not successful"
                }
            
            api_last_date_str = last_date_data["data"].get("last_response_date")
            if not api_last_date_str:
                logger.info("No responses found in API")
                return {
                    "success": True,
                    "responses_added": 0,
                    "users_updated": 0,
                    "last_api_response_date": None,
                    "last_db_response_date": db_last_date_str,
                    "message": "No responses found in API"
                }
            
            logger.info(f"Last response in API: {api_last_date_str}")
            
            # Convert API date string to datetime for comparison
            api_last_date = datetime.fromisoformat(api_last_date_str.replace('Z', '+00:00'))
            
            # Check if there are new responses
            if db_last_date and api_last_date <= db_last_date:
                logger.info("No new responses to add")
                return {
                    "success": True,
                    "responses_added": 0,
                    "users_updated": 0,
                    "last_api_response_date": api_last_date_str,
                    "last_db_response_date": db_last_date_str,
                    "message": "No new responses to add"
                }
            
            # Prepare query parameters
            params = {
                "survey_id": survey_id,
                "page": 1,
                "limit": 100  # Using max limit to minimize requests
            }
            
            # If we have a last date, use it as start_date filter
            if db_last_date:
                # Add a small buffer to avoid duplicate (get responses strictly after the last one)
                start_date = db_last_date.date().isoformat()
                params["start_date"] = start_date
                logger.info(f"Fetching responses from {start_date} onwards")
            
            # Fetch first page to get total count
            response = await client.get(
                f"{base_url}/api/responses",
                params=params,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("success"):
                logger.error(f"API returned unsuccessful response: {data}")
                return {
                    "success": False,
                    "responses_added": 0,
                    "users_updated": 0,
                    "last_api_response_date": api_last_date_str,
                    "last_db_response_date": db_last_date_str,
                    "message": "API request was not successful"
                }
            
            pagination = data["data"]["pagination"]
            total_pages = pagination["totalPages"]
            
            logger.info(f"Total pages to fetch: {total_pages}")
            
            # Collect all responses from API
            all_api_responses = []
            all_api_responses.extend(data["data"]["responses"])
            
            # Fetch remaining pages if any
            for page in range(2, total_pages + 1):
                logger.info(f"Fetching page {page} of {total_pages}")
                params["page"] = page
                response = await client.get(
                    f"{base_url}/api/responses",
                    params=params,
                    headers=headers
                )
                response.raise_for_status()
                page_data = response.json()
                
                if page_data.get("success"):
                    all_api_responses.extend(page_data["data"]["responses"])
            
            logger.info(f"Fetched {len(all_api_responses)} responses from API")
            
            # Get existing response IDs from database to avoid duplicates
            existing_responses = await responses_collection.find(
                {"survey_id": survey_id},
                {"id": 1}
            ).to_list(length=None)
            existing_response_ids = {resp["id"] for resp in existing_responses}
            
            # Filter out responses that already exist and are newer than DB last date
            new_responses = []
            for resp in all_api_responses:
                if resp["id"] not in existing_response_ids:
                    # Double-check the date to ensure it's newer
                    resp_created_at = datetime.fromisoformat(resp["created_at"].replace('Z', '+00:00'))
                    if not db_last_date or resp_created_at > db_last_date:
                        new_responses.append(resp)
            
            logger.info(f"Found {len(new_responses)} new responses to add")
            
            # Add new responses to database and update user data
            responses_added = 0
            users_updated = 0
            for response_data in new_responses:
                # Convert datetime strings to datetime objects if needed
                prepared_response = prepare_response_for_db(response_data)
                
                # Add response to responses collection
                result = await create_survey_response(prepared_response)
                if result:
                    responses_added += 1
                    logger.info(f"Added response: {prepared_response.get('id', 'N/A')}")
                    
                    # Update user data in users collection
                    user_updated = await update_user_from_response(prepared_response)
                    if user_updated:
                        users_updated += 1
                else:
                    logger.warning(f"Failed to add response: {prepared_response.get('id', 'N/A')}")
            
            logger.info(f"Successfully added {responses_added} new responses")
            logger.info(f"Updated {users_updated} user records")
            
            return {
                "success": True,
                "responses_added": responses_added,
                "users_updated": users_updated,
                "last_api_response_date": api_last_date_str,
                "last_db_response_date": db_last_date_str,
                "message": f"Successfully added {responses_added} new responses and updated {users_updated} user records"
            }
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error occurred while syncing responses: {e}")
        return {
            "success": False,
            "responses_added": 0,
            "users_updated": 0,
            "last_api_response_date": None,
            "last_db_response_date": db_last_date_str if 'db_last_date_str' in locals() else None,
            "message": f"HTTP error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error syncing responses from API: {e}")
        return {
            "success": False,
            "responses_added": 0,
            "users_updated": 0,
            "last_api_response_date": None,
            "last_db_response_date": db_last_date_str if 'db_last_date_str' in locals() else None,
            "message": f"Error: {str(e)}"
        }


def prepare_survey_for_db(survey: dict[str, Any]) -> dict[str, Any]:
    """
    Prepare survey data from API for database insertion.
    
    Converts datetime string fields to datetime objects as needed.
    
    Args:
        survey: Survey data from API
        
    Returns:
        dict[str, Any]: Survey data ready for database insertion
    """
    survey_copy = survey.copy()
    
    # Convert datetime string fields to datetime objects
    datetime_fields = ["created_at", "updated_at", "published_at", "expires_at"]
    for field in datetime_fields:
        if field in survey_copy and survey_copy[field] is not None:
            if isinstance(survey_copy[field], str):
                try:
                    survey_copy[field] = datetime.fromisoformat(survey_copy[field].replace('Z', '+00:00'))
                except Exception as e:
                    logger.warning(f"Failed to parse datetime field '{field}': {e}")
    
    return survey_copy


def prepare_response_for_db(response: dict[str, Any]) -> dict[str, Any]:
    """
    Prepare response data from API for database insertion.
    
    Converts datetime string fields to datetime objects as needed.
    
    Args:
        response: Response data from API
        
    Returns:
        dict[str, Any]: Response data ready for database insertion
    """
    response_copy = response.copy()
    
    # Convert datetime string fields to datetime objects
    datetime_fields = ["created_at", "updated_at"]
    for field in datetime_fields:
        if field in response_copy and response_copy[field] is not None:
            if isinstance(response_copy[field], str):
                try:
                    response_copy[field] = datetime.fromisoformat(response_copy[field].replace('Z', '+00:00'))
                except Exception as e:
                    logger.warning(f"Failed to parse datetime field '{field}': {e}")
    
    return response_copy
