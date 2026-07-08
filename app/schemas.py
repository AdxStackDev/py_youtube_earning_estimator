"""Pydantic schemas for the YouTube Earnings Estimator."""

from pydantic import BaseModel, Field


class VideoInfo(BaseModel):
    """Information about a single YouTube video."""

    video_id: str
    title: str
    view_count: int = Field(ge=0)
    thumbnail_url: str | None = None


class ChannelStats(BaseModel):
    """Channel statistics retrieved from YouTube Data API."""

    title: str
    subscriber_count: int = Field(ge=0)
    total_views: int = Field(ge=0)
    video_count: int = Field(ge=0)
    uploads_playlist_id: str
    channel_id: str = ""
    custom_url: str | None = None
    published_at: str | None = None
    thumbnail_url: str | None = None


class EarningsResult(BaseModel):
    """Calculated earnings estimate with low, medium, and high bounds."""

    estimated_monthly_views: float = Field(ge=0)
    earnings_low: float = Field(ge=0)
    earnings_medium: float = Field(ge=0)
    earnings_high: float = Field(ge=0)


class ContentBreakdown(BaseModel):
    """Earnings breakdown for a specific content focus (long-form or shorts)."""

    content_type: str  # "long_form" or "shorts"
    rpm_low: float = Field(ge=0)
    rpm_high: float = Field(ge=0)
    rpm_effective: float = Field(ge=0)
    estimated_monthly_views: float = Field(ge=0)
    baseline_daily_views: float = Field(ge=0)
    earnings_low: float = Field(ge=0)
    earnings_medium: float = Field(ge=0)
    earnings_high: float = Field(ge=0)
    ads_revenue: float = Field(ge=0)
    premium_revenue: float = Field(ge=0)


class EstimateResponse(BaseModel):
    """Full API response combining channel stats, earnings, and video data."""

    channel_title: str
    channel_id: str
    channel_url: str
    custom_url: str | None = None
    published_at: str | None = None
    thumbnail_url: str | None = None
    subscriber_count: int
    total_views: int
    video_count: int

    # Per-content-focus earnings breakdowns
    long_form: ContentBreakdown
    shorts: ContentBreakdown

    recent_videos: list[VideoInfo]
    recent_shorts: list[VideoInfo] = []

    # Flat long-form fields retained for backward compatibility
    estimated_monthly_views: float
    earnings_low: float
    earnings_medium: float
    earnings_high: float
    rpm_low: float
    rpm_high: float
