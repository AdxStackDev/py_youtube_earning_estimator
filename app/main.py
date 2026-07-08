"""FastAPI application for the YouTube Earnings Estimator."""

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse

from app.cache import CacheManager
from app.config import get_settings
from app.estimator import Estimator
from app.exceptions import ChannelNotFoundError, ValidationError, YouTubeAPIError
from app.schemas import EstimateResponse
from app.service import EstimationService
from app.youtube_client import YouTubeClient

settings = get_settings()

youtube_client = YouTubeClient(
    api_key=settings.YOUTUBE_API_KEY,
    timeout=settings.API_TIMEOUT_SECONDS,
)
estimator = Estimator()
cache = CacheManager(settings)
service = EstimationService(
    youtube_client=youtube_client,
    estimator=estimator,
    cache=cache,
    rpm_shorts_low=settings.RPM_SHORTS_LOW,
    rpm_shorts_high=settings.RPM_SHORTS_HIGH,
    ads_share=settings.ADS_REVENUE_SHARE,
)

app = FastAPI(title="YouTube Earnings Estimator")


@app.exception_handler(ChannelNotFoundError)
async def channel_not_found_handler(request: Request, exc: ChannelNotFoundError) -> JSONResponse:
    """Return HTTP 404 when a channel cannot be found."""
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(YouTubeAPIError)
async def youtube_api_error_handler(request: Request, exc: YouTubeAPIError) -> JSONResponse:
    """Return HTTP 502 when YouTube API returns an error."""
    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Return HTTP 422 when input validation fails."""
    return JSONResponse(status_code=422, content={"detail": exc.message})


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return HTTP 500 for unhandled exceptions without exposing internals."""
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/estimate", response_model=EstimateResponse)
def estimate(
    q: str = Query(..., min_length=1, max_length=256),
    rpm_low: float | None = Query(None, ge=0.01, le=100.0),
    rpm_high: float | None = Query(None, ge=0.01, le=100.0),
) -> EstimateResponse:
    """Estimate YouTube channel earnings.

    Args:
        q: Channel identifier (handle, URL, or search query).
        rpm_low: Optional low-end RPM override.
        rpm_high: Optional high-end RPM override.

    Returns:
        Full estimation response with channel stats, earnings, and video data.
    """
    effective_rpm_low = rpm_low or settings.RPM_LOW
    effective_rpm_high = rpm_high or settings.RPM_HIGH

    return service.estimate(q, effective_rpm_low, effective_rpm_high)
