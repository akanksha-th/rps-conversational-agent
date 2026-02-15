from fastapi import APIRouter, HTTPException
from src.schemas.requests import AnalyzeRequest
from src.services.youtube import YouTubeService
from src.utils.validators import get_videoId

router = APIRouter()

@router.post("/analyze")
def analyze_url(request: AnalyzeRequest):
    """
    Analyze Sentiment of YouTube video comments
    
    Parameters:
        - video_url: URL of the YouTube video
        - max_comments: Number of comments to analyze (100)
    """
    try:
        video_id = get_videoId(request.video_url)
        if not video_id:
            raise HTTPException(
                status_code=400, 
                detail="Invalid YouTube URL"
            )
        service = YouTubeService()
        results = service.get_comments(video_id, request.max_comments)
        return {"status": "success", "data": results}
    except ValueError as e:
        # Handle validation errors (video not found, etc.)
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(status_code=500, detail=str(e))