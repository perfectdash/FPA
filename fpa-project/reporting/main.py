import os
import json
import logging
import asyncio
from contextlib import asynccontextmanager
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException, status
from google.cloud import bigquery
from redis.asyncio import StrictRedis

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("reporting_service")

# will give the cloud run these secrets and let the container to access these things
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

redis_client = None 

@asynccontextmanager
async def lifespan(app: FastAPI): 
    global redis_client
    try: 
        redis_client = StrictRedis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=0,
            decode_responses=True,
            socket_timeout=2.0
        )
        await redis_client.ping()
        logger.info(f"Connected to Redis cache at {REDIS_HOST}:{REDIS_PORT}")
    except Exception as e: 
        redis_client = None
        logger.warning(f"Failed to connect to Redis cache at {REDIS_HOST}:{REDIS_PORT}: {e}.")
    
    yield 
    
    if redis_client: 
        await redis_client.close()
        logger.info("Redis connection closed")

app = FastAPI(
    title="FP&A Analytical Reporting Service",
    description="High-performance query API serving variance reports with cache-aside acceleration",
    lifespan=lifespan
)

bq_client = None
if PROJECT_ID:
    try:
        bq_client = bigquery.Client(project=PROJECT_ID)
        logger.info(f"Initialized BigQuery client targeting project {PROJECT_ID}")
    except Exception as e:
        logger.warning(f"Failed to initialize BigQuery client: {e}.")
else:
    logger.info("GCP_PROJECT_ID environment variable not found")


# let's consider this for testing
MOCK_BUDGETS = {
    "D-101": {"name": "HR Division", "allocated": 50000.0, "base_spent": 38000.0},
    "D-202": {"name": "Engineering", "allocated": 120000.0, "base_spent": 105000.0},
    "D-303": {"name": "Marketing", "allocated": 75000.0, "base_spent": 42000.0}
}

def get_variance_query(project: str, days: int = 30) -> str:
    """Compiles the BigQuery DDL query for variance calculations."""
    return f"""
    WITH ActualSpend AS (
      SELECT 
        department_id, 
        SUM(amount) AS actual_spent
      FROM `{project}.fpa_analytics.transactions_raw`
      WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
      GROUP BY department_id
    ),
    Budget AS (
      SELECT 
        department_id, 
        allocated_budget 
      FROM EXTERNAL_QUERY(
        "projects/{project}/locations/us/connections/fpa-postgres-connection",
        "SELECT department_id, allocated_budget FROM department_budgets;"
      )
    )
    SELECT 
      b.department_id, 
      b.allocated_budget, 
      COALESCE(a.actual_spent, 0) as actual_spent,
      (b.allocated_budget - COALESCE(a.actual_spent, 0)) as variance
    FROM Budget b
    LEFT JOIN ActualSpend a ON b.department_id = a.department_id
    """


@app.get("/api/v1/fpa/variance", response_model=List[Dict[str, Any]])
async def get_variance_report(days: int = 30):

    """
    Fetches the budget variance report. Checks the Redis cache first
    to prevent costly BigQuery table scans. If both Redis and BigQuery
    are offline, returns dynamically generated mock transactions for demoing.
    """
    cache_key = f"fpa_variance_report_days_{days}"

    if redis_client:
        try:
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                logger.info("Serving variance report from Redis cache (Cache Hit)")
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Redis cache lookup failed: {e}")

    if bq_client and PROJECT_ID:
        try:
            logger.info("Executing BigQuery analytics query (Cache Miss)")
            query_job = bq_client.query(get_variance_query(PROJECT_ID, days))
            results = await asyncio.to_thread(query_job.result)
            data_list = []
            
            for row in results:
                
                allocated = float(row.allocated_budget)
                spent = float(row.actual_spent)
                variance = float(row.variance)
                burn_rate = round((spent / allocated) * 100, 2) if allocated > 0 else 0
                
                data_list.append({
                    "department_id": row.department_id,
                    "department_name": MOCK_BUDGETS.get(row.department_id, {}).get("name", "Unknown"),
                    "allocated_budget": allocated,
                    "actual_spent": spent,
                    "variance": variance,
                    "burn_rate": burn_rate
                })

            if redis_client:
                try:
                    await redis_client.setex(cache_key, 300, json.dumps(data_list))
                    logger.info("Cached BigQuery query results in Redis")
                except Exception as ex:
                    logger.warning(f"Failed to cache results in Redis: {ex}")
            
            return data_list

        except Exception as e:
            logger.warning(f"BigQuery query execution failed: {e}. Falling back to mock data.")

    # Fallback to local mock data if BigQuery/Redis/GCP are offline or query fails
    logger.info("Serving mock variance report data")
    mock_data = []
    for dept_id, info in MOCK_BUDGETS.items():
        allocated = info["allocated"]
        spent = info["base_spent"]
        variance = allocated - spent
        burn_rate = round((spent / allocated) * 100, 2) if allocated > 0 else 0
        mock_data.append({
            "department_id": dept_id,
            "department_name": info["name"],
            "allocated_budget": allocated,
            "actual_spent": spent,
            "variance": variance,
            "burn_rate": burn_rate
        })
    return mock_data

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {
        "status": "healthy",
        "redis_connected": redis_client is not None,
        "bigquery_connected": bq_client is not None,
    }

