# Sentiment analysis API

A REST API that analyzes sentiment of YouTube video comments using RoBERTa transformer model. Built with FastAPI, Redis caching, and comprehensive testing.

---

## Features

- **Sentiment Analysis**: Powered by RoBERTa transformer model (cardiffnlp/twitter-roberta-base-sentiment-latest)
- **Batch Processing**: Efficiently analyzes 100+ comments in seconds
- **Redis Caching**: Faster on repeated requests (< 100 ms)
- **Rate Limiting**: IP-based rate-limiting (10 requests per minute)
- **Text Preprocessing**: Handles URLs, emojis, HTML, and special characters
- **Aggregated Metrics**: Sentiment distribution, confidence scores, engagement stats
- **RESTful API**: Clean, well-documented endpoints with Swagger UI
- **Comprehensive Testing**: A handful of unit and integration tests (more to be added)

---

## Architecture


| Layer | Components & Responsibilities |
| :--- | :--- |
| **API Layer** | `POST /api/v1/analyze`, Rate Limiting (Redis) |
| **Service Layer** | `YouTubeService` (fetch comments), `AnalyzerService` (orchestration), `CacheService` (Redis) |
| **Model Layer** | `TextProcessor` (cleaning), `SentimentAnalyzer` (RoBERTa) |
| **Data Layer** | Redis (caching), YouTube Data API v3 |

---

