from src.services.cache import CacheService
from src.core.config import get_settings
from fastapi import Request, status, HTTPException
import time

settings = get_settings()
cache_service = CacheService()

async def rate_limiter(request: Request):
    client_ip = request.client.host
    if "x-forwarded-for" in request.headers:
        client_ip = request.headers["x-forwarded-for"].split(",")[0]

    current_minute = int(time.time() // 60) # in minutes
    key = f"rate_limit:{client_ip}:{current_minute}"

    current_count = cache_service.redis_server.incr(key)
    limit = settings.RATE_LIMIT_PER_MINUTE
    if current_count > limit:
        retry_after = 60 - (int(time.time()) % 60)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={f"Retry After: {str(retry_after)}"}
        )
    
    request.state.rate_limit_remaining = max(0, limit-current_count)
    return True