import os
import asyncio
import logging
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from frontend_endpoints import router as frontend_router
from analytics_router import router as analytics_router
from utils.db_update import sync_all_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

origins = [
    os.getenv("VITE_URL", "http://localhost:3000"),
    os.getenv("BACKEND_URL", "http://localhost:8000"),
]

app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,  # Specific allowed origins
        allow_credentials=True,  # Allow cookies and authentication headers
        allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
        allow_headers=["*"],  # Allow all headers
    )


# Background task for periodic data sync
sync_task = None
should_sync = True

async def periodic_sync():
    """
    Background task that runs sync_all_data() every 30 minutes.
    """
    global should_sync
    
    # Wait 5 seconds after startup before first sync
    await asyncio.sleep(5)
    
    while should_sync:
        try:
            logger.info("Starting periodic data sync...")
            result = await sync_all_data()
            
            if result["success"]:
                logger.info(
                    f"Periodic sync completed: {result['surveys_result']['surveys_added']} surveys, "
                    f"{result['total_responses_added']} responses added"
                )
            else:
                logger.error(f"Periodic sync failed: {result['message']}")
        except Exception as e:
            logger.error(f"Error in periodic sync task: {e}")
        
        # Wait 30 minutes before next sync (1800 seconds)
        if should_sync:
            logger.info("Next sync in 30 minutes...")
            await asyncio.sleep(1800)


@app.on_event("startup")
async def startup_event():
    """
    Start the periodic sync task when the app starts.
    """
    global sync_task
    sync_task = asyncio.create_task(periodic_sync())
    logger.info("Periodic data sync task started (runs every 30 minutes)")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Stop the periodic sync task when the app shuts down.
    """
    global should_sync, sync_task
    should_sync = False
    
    if sync_task:
        sync_task.cancel()
        try:
            await sync_task
        except asyncio.CancelledError:
            logger.info("Periodic data sync task stopped")


# Manual sync endpoint (optional - for testing/manual triggers)
@app.post("/api/sync/manual")
async def manual_sync():
    """
    Manually trigger a data sync.
    Returns the sync results.
    """
    try:
        logger.info("Manual sync triggered via API endpoint")
        result = await sync_all_data()
        return result
    except Exception as e:
        logger.error(f"Error in manual sync: {e}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


app.include_router(frontend_router)
app.include_router(analytics_router)