import os
import json
import logging
import asyncio
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from google.cloud import pubsub_v1

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger("ingestion_service")

app = FastAPI(
    title="FP&A Financial Ingestion Service",
    description="High-throughput asynchronous ingestion endpoint for financial events"
)

class FinancialEvent(BaseModel):

    transaction_id: str = Field(..., alias="transactionId")
    timestamp: str = Field(..., description="ISO 8601 format timestamp or unix timestamp string")
    department_id: str = Field(..., alias="departmentId")
    amount: float = Field(..., gt=0.0)
    currency: str = Field(..., min_length=3, max_length=3)
    category: str
    vendor: str

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v):
        allowed = ["USD", "INR", "EUR", "GBP"]
        if v not in allowed:
            raise ValueError(f"Currency must be one of {allowed}")
        return v

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "transactionId": "tx-999123",
                "timestamp": "1720000000",
                "departmentId": "D-202",
                "amount": 45000.50,
                "currency": "USD",
                "category": "Software Licenses",
                "vendor": "Google Cloud"
            }
        }
    }

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
TOPIC_ID = os.getenv("PUBSUB_TOPIC_ID", "transactions")

publisher = None
topic_path = None

if PROJECT_ID:
    try:
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)
        logger.info(f"Initialized Pub/Sub Publisher client for project {PROJECT_ID}, topic {TOPIC_ID}")
    except Exception as e:
        logger.warning(f"Failed to initialize GCP Pub/Sub client: {e}. Running in local mock mode.")
else:
    logger.info("GCP_PROJECT_ID environment variable not found. Running in local mock mode.")

@app.post("/api/v1/transactions", status_code=status.HTTP_202_ACCEPTED)
async def ingest_transaction(event: FinancialEvent):
    """
    Asynchronously ingests financial transactions, validates the schema,
    and publishes the event to Google Cloud Pub/Sub (or local mock queue).
    """

    # the event model is first converted into the python dict 
    # then serialized and then the encoded into the byte stream
    event_dict = event.model_dump()
    payload = json.dumps(event_dict).encode("utf-8")

    if publisher and topic_path:
        try:
            loop = asyncio.get_running_loop()
            future = await loop.run_in_executor(
                None,
                lambda: publisher.publish(
                    topic_path,
                    payload,
                    department_id=event.department_id,
                    currency=event.currency
                )
            )

            def callback(fut):
                try:
                    message_id = fut.result()
                    logger.info(f"Published transaction {event.transaction_id} to Pub/Sub. Msg ID: {message_id}")
                except Exception as ex:
                    logger.error(f"Async publish callback failed for {event.transaction_id}: {ex}")

            future.add_done_callback(callback)
            return {"status": "Accepted", "transactionId": event.transaction_id, "mode": "production"}
        except Exception as e:
            logger.error(f"Error executing Pub/Sub publish for transaction {event.transaction_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal message broker publish failure."
            )
    else:
        logger.info(f"[MOCK MODE] Ingested transaction {event.transaction_id}: {event_dict}")
        return {"status": "Accepted", "transactionId": event.transaction_id, "mode": "local-mock"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "pubsub_connected": publisher is not None,
        "mode": "production" if publisher else "local-mock"
    }

