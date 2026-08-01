"""
CodeLens AI - FastAPI Application
Gemini-Powered Code Review SaaS for XPRIZE Build with Gemini
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from pathlib import Path
import os

from .config import settings
from .gemini_reviewer import GeminiReviewer
from .models import ReviewRequest

app = FastAPI(
    title="CodeLens AI",
    description="AI-Powered Code Review SaaS — Built with Google Gemini",
    version=settings.APP_VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini reviewer
reviewer = GeminiReviewer(
    api_key=settings.GEMINI_API_KEY,
    model=settings.GEMINI_MODEL
)

# In-memory review storage (production would use a database)
reviews_db: list = []
stats = {
    "total_reviews": 0,
    "lines_reviewed": 0,
    "issues_found": 0,
    "languages": {},
    "started_at": datetime.now(timezone.utc).isoformat()
}

# Serve frontend
frontend_dir = Path(__file__).parent.parent / "frontend"


@app.get("/")
async def serve_index():
    index_file = frontend_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "CodeLens AI API", "version": settings.APP_VERSION}


@app.get("/style.css")
async def serve_css():
    return FileResponse(str(frontend_dir / "style.css"), media_type="text/css")


@app.get("/app.js")
async def serve_js():
    return FileResponse(str(frontend_dir / "app.js"), media_type="application/javascript")


@app.get("/api/info")
async def api_info():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "powered_by": "Google Gemini 2.0 Flash",
        "status": "operational",
        "demo_mode": settings.DEMO_MODE or not settings.GEMINI_API_KEY
    }


@app.post("/api/review")
async def create_review(request: ReviewRequest):
    """Submit code for AI-powered review"""
    try:
        result = await reviewer.review_code(
            code=request.code,
            language=request.language,
            context=request.context
        )

        # Store review
        reviews_db.append(result)
        if len(reviews_db) > 100:
            reviews_db.pop(0)

        # Update stats
        stats["total_reviews"] += 1
        stats["lines_reviewed"] += result.get("lines_reviewed", 0)
        stats["issues_found"] += len(result.get("issues", []))
        lang = request.language
        stats["languages"][lang] = stats["languages"].get(lang, 0) + 1

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reviews")
async def list_reviews(limit: int = 10):
    """List past reviews"""
    return {
        "reviews": reviews_db[-limit:][::-1],
        "total": len(reviews_db)
    }


@app.get("/api/reviews/{review_id}")
async def get_review(review_id: str):
    """Get a specific review by ID"""
    for review in reviews_db:
        if review.get("review_id") == review_id:
            return review
    raise HTTPException(status_code=404, detail="Review not found")


@app.get("/api/stats")
async def get_stats():
    """Usage statistics"""
    return {
        **stats,
        "avg_score": round(
            sum(r.get("score", 0) for r in reviews_db) / max(len(reviews_db), 1), 1
        ),
        "recent_reviews": len(reviews_db),
        "uptime_since": stats["started_at"]
    }


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "gemini_configured": bool(settings.GEMINI_API_KEY)
    }


# Mount static files as fallback
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")
