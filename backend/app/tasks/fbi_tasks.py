"""
Celery tasks for FBI crime data.

Primary use: pre-warm or refresh the Redis cache for a given US state
without blocking an active web request.

Example usage (from a Python shell or another task):
    from app.tasks.fbi_tasks import prefetch_state_crime_data
    prefetch_state_crime_data.delay("CA")
    prefetch_state_crime_data.delay("NY")
"""

import asyncio
import logging

from app.core.celery_app import celery_app
from app.core.redis_cache import cache_set, CACHE_7_DAYS

logger = logging.getLogger(__name__)

FBI_CACHE_KEY = "fbi:state:{state}"


@celery_app.task(name="fbi.prefetch_state", bind=True, max_retries=2, default_retry_delay=60)
def prefetch_state_crime_data(self, state: str):
    """
    Fetch FBI crime rates for the given 2-letter state code and store in Redis.

    The task uses a synthetic address so it can reuse the existing
    CrimeService._fetch_fbi_rates() method without modification.
    """
    from app.services.crime_service import crime_service

    state = state.upper().strip()
    # Synthetic address that matches the regex in _state_from_address()
    synthetic_address = f"City, {state} 00000, USA"

    logger.info("Prefetching FBI data for state: %s", state)
    try:
        result = asyncio.run(crime_service._fetch_fbi_rates(synthetic_address))
        if result:
            cache_set(FBI_CACHE_KEY.format(state=state), result, ttl=CACHE_7_DAYS)
            logger.info("Cached FBI data for %s: %.0f/100k (%s)", state, result["total"], result["source"])
            return {"state": state, "cached": True, "rate": result["total"]}
        else:
            logger.warning("FBI API returned no data for %s; cache not updated", state)
            return {"state": state, "cached": False}
    except Exception as exc:
        logger.error("FBI prefetch failed for %s: %s", state, exc)
        raise self.retry(exc=exc)
