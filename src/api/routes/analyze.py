from fastapi import APIRouter, HTTPException, Depends
from src.schemas.requests import AnalyzeRequest
from src.schemas.responses import AnalysisResponse
from src.services.youtube import YouTubeService
from src.services.analyzer import AnalyzerService
from src.services.cache import CacheService
from src.utils.validators import get_videoId
from src.api.dependencies import rate_limiter

router = APIRouter()

youtube_service = YouTubeService()
analyzer_service = AnalyzerService()
cache_service = CacheService()

@router.post("/analyze", dependencies=[Depends(rate_limiter)])
def analyze_url(request: AnalyzeRequest):
    """
    Analyze Sentiment of YouTube video comments
    """
    # Step 1: Extract video ID
    video_id = get_videoId(request.video_url)
    if not video_id:
        raise HTTPException(
            status_code=400, 
            detail="Invalid YouTube URL"
        )
    
    # cache_key = f"{video_id}:{request.max_comments}"
    cache_key = cache_service.generate_analysis_key(video_id, request.max_comments)
    cached_data = cache_service.get(cache_key)
    if cached_data:
        cached_data["cached"] = True
        cached_data["source"] = "cache"
        return AnalysisResponse(**cached_data)
    
    # Step 2: Fetch Comments
    try:
        comments_data = youtube_service.get_comments(
            video_id, 
            request.max_comments
        )
    except ValueError as e:
        # Handle validation errors (video not found, etc.)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"YouTube API Error: {e}")
        raise HTTPException(status_code=503, detail=f"YouTube API error: {str(e)}")
    
    # Step 3: Analyze Comments
    try:
        result = analyzer_service.analyze_comments(
            video_id=video_id,
            comments=comments_data["comments"]
        )
        result["cached"] = False
        result["source"] = "api"
        cache_service.set(cache_key, result)
    except Exception as e:
        print(f"Analysis Error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

    # Step 4: Return Response
    try:
        return AnalysisResponse(**result)
    except Exception as e:
        print(f"Schema Validation Error: {e}")
        print(f"Result was: {result}")
        raise HTTPException(status_code=500, detail=f"Response error: {str(e)}")