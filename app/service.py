"""Service layer for the YouTube Earnings Estimator.

Orchestrates YouTube client, estimator, and cache to fulfill estimation requests.
"""

from app.cache import CacheManager
from app.estimator import Estimator
from app.schemas import EstimateResponse
from app.youtube_client import YouTubeClient


def _build_channel_url(channel_id: str, custom_url: str | None) -> str:
    """Construct a public YouTube channel URL from a handle or channel ID."""
    if custom_url:
        handle = custom_url.lstrip("/")
        if handle.startswith("@"):
            return f"https://www.youtube.com/{handle}"
        return f"https://www.youtube.com/@{handle}" if not handle.startswith("channel/") else f"https://www.youtube.com/{handle}"
    return f"https://www.youtube.com/channel/{channel_id}"


class EstimationService:
    """Orchestrates channel resolution, stats retrieval, and earnings estimation."""

    def __init__(
        self,
        youtube_client: YouTubeClient,
        estimator: Estimator,
        cache: CacheManager,
        rpm_shorts_low: float = 0.03,
        rpm_shorts_high: float = 0.20,
        ads_share: float = 0.95,
    ) -> None:
        self._youtube_client = youtube_client
        self._estimator = estimator
        self._cache = cache
        self._rpm_shorts_low = rpm_shorts_low
        self._rpm_shorts_high = rpm_shorts_high
        self._ads_share = ads_share

    def estimate(
        self, query: str, rpm_low: float, rpm_high: float
    ) -> EstimateResponse:
        """Full estimation pipeline: resolve → stats → videos → calculate.

        Args:
            query: Channel identifier (handle, URL, or search query).
            rpm_low: Low-end long-form RPM value.
            rpm_high: High-end long-form RPM value.

        Returns:
            Complete estimation response with channel stats, earnings, and videos.

        Raises:
            ChannelNotFoundError: If no channel matches the query.
            YouTubeAPIError: On upstream API errors or timeouts.
        """
        # Normalize input for cache lookup
        normalized = query.strip().lower()

        # Resolve channel ID (cache-first)
        channel_id = self._cache.get_channel_id(normalized)
        if channel_id is None:
            channel_id = self._youtube_client.resolve_channel(query)
            self._cache.set_channel_id(normalized, channel_id)

        # Get channel stats (cache-first)
        stats = self._cache.get_stats(channel_id)
        if stats is None:
            stats = self._youtube_client.get_channel_stats(channel_id)
            self._cache.set_stats(channel_id, stats)

        # Get recent videos (cache-first)
        videos = self._cache.get_videos(channel_id)
        if videos is None:
            videos = self._youtube_client.get_recent_videos(stats.uploads_playlist_id)
            self._cache.set_videos(channel_id, videos)

        # Get recent shorts (cache-first)
        shorts_list = self._cache.get_shorts(channel_id)
        if shorts_list is None:
            shorts_list = self._youtube_client.get_recent_shorts(channel_id)
            self._cache.set_shorts(channel_id, shorts_list)

        # Build earnings breakdowns for both content focuses
        long_form = self._estimator.build_breakdown(
            "long_form", videos, rpm_low, rpm_high, self._ads_share
        )
        shorts = self._estimator.build_breakdown(
            "shorts", videos, self._rpm_shorts_low, self._rpm_shorts_high, self._ads_share
        )

        resolved_channel_id = stats.channel_id or channel_id
        channel_url = _build_channel_url(resolved_channel_id, stats.custom_url)

        return EstimateResponse(
            channel_title=stats.title,
            channel_id=resolved_channel_id,
            channel_url=channel_url,
            custom_url=stats.custom_url,
            published_at=stats.published_at,
            thumbnail_url=stats.thumbnail_url,
            subscriber_count=stats.subscriber_count,
            total_views=stats.total_views,
            video_count=stats.video_count,
            long_form=long_form,
            shorts=shorts,
            recent_videos=videos,
            recent_shorts=shorts_list,
            # Flat long-form fields for backward compatibility
            estimated_monthly_views=long_form.estimated_monthly_views,
            earnings_low=long_form.earnings_low,
            earnings_medium=long_form.earnings_medium,
            earnings_high=long_form.earnings_high,
            rpm_low=rpm_low,
            rpm_high=rpm_high,
        )
