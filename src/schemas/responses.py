from pydantic import BaseModel
from typing import List

class CommentResult(BaseModel):
    author: str
    text: str
    cleaned_text: str
    like_count: int
    published_at: str
    updated_at: str
    sentiment: str
    confidence: float


class SentimentDistribution(BaseModel):
    positive: float
    negative: float
    neutral: float


class AnalysisResponse(BaseModel):
    video_id: str
    total_comments: int
    valid_comments: int
    sentiment_distribution: SentimentDistribution
    overall_sentiment: str
    average_confidence: float
    comments: List[CommentResult]
    processing_time_ms: int
    cached: bool = False
    source: str