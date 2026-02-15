import googleapiclient.discovery as discovery
import googleapiclient.errors as errors
from src.utils.validators import get_videoId
import pandas as pd, os
from src.core.config import get_settings


class YouTubeService:
    def __init__(self):
        """Initialize YouTube API client"""
        settings = get_settings()
        self.youtube_client = discovery.build(
            settings.API_SERVICE_NAME,
            settings.API_VERSION,
            developerKey=settings.YOUTUBE_API_KEY
        )

    def get_comments(self, video_id: str, max_results: int) -> dict:
        comments = []
        next_page_token = None
        total_fetched = 0
        
        try:
            while True:
                if total_fetched >= max_results:
                    break
                remaining = max_results - total_fetched
                page_size = min(100, remaining)

                request = self.youtube_client.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    maxResults=page_size,
                    pageToken=next_page_token
                )
                response = request.execute()

                for item in response["items"]:
                    snippet = item["snippet"]["topLevelComment"]["snippet"]
                    comments.append({
                        "author": snippet["authorDisplayName"],
                        "published_at": snippet["publishedAt"],
                        "updated_at": snippet["updatedAt"],
                        "like_count": snippet["likeCount"],
                        "text": snippet["textDisplay"]
                    })

                total_fetched = len(comments)
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break

            comments_df = pd.DataFrame(comments, columns=["author", "published_at", "updated_at", "like_count", "text"])
            os.makedirs("src/models/data", exist_ok=True)
            comments_df.to_csv("src/models/data/comments.csv", index=False, encoding="utf-8")
                
            return {
                "video_id": video_id,
                "comments": comments,
                "total": len(comments)
            }
        
        except errors.HttpError as e:
            if e.resp.status == 404:
                raise ValueError(f"Video not found: {video_id}")
            elif e.resp.status == 403:
                raise ValueError("API quota exceeded or comments disabled")
            else:
                raise Exception(f"YouTube API error: {str(e)}")