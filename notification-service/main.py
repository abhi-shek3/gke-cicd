import asyncio
import logging
import os
from fastapi import FastAPI
import redis.asyncio as redis

# --- Configuration ---
app = FastAPI(title="Notification Service")
logging.basicConfig(level=logging.INFO)

# In K8s, we will inject this via ConfigMap. Locally, it defaults to localhost.
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

# --- Background Task ---
async def redis_listener():
    try:
        # Connect to Redis
        r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
        pubsub = r.pubsub()
        await pubsub.subscribe("note_events")
        
        logging.info("Successfully connected to Redis. Listening for 'note_events'...")
        
        # Infinite loop waiting for messages
        async for message in pubsub.listen():
            if message["type"] == "message":
                event_data = message["data"]
                logging.info(f"🔔 NOTIFICATION TRIGGERED: {event_data}")
                
    except Exception as e:
        logging.error(f"Redis connection failed: {e}. Is your Redis server running?")

# --- Lifecycle Events ---
@app.on_event("startup")
async def startup_event():
    # Start the listener in the background when FastAPI boots up
    asyncio.create_task(redis_listener())

# --- Endpoints ---
@app.get("/health")
def health_check():
    return {"status": "ok"}