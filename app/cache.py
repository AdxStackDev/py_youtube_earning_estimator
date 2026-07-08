"""In-memory TTL cache module for the YouTube Earnings Estimator.

Provides a CacheManager with three separate caches for channel IDs,
channel statistics, and video data, each with different TTL values.
Combined max size is enforced with LRU eviction.
"""

from cachetools import TTLCache

from app.config import Settings
from app.schemas import ChannelStats, VideoInfo


class CacheManager:
    """Manages three TTL caches for channel resolution, stats, and videos.

    Input normalization (strip + lowercase) is applied to channel_id cache
    keys for case-insensitive matching. Combined max size across all caches
    is enforced via per-cache maxsize allocation with LRU eviction.
    """

    def __init__(self, settings: Settings) -> None:
        max_size = settings.CACHE_MAX_SIZE

        # Split the combined max size across caches:
        # 400 for channel_id, 200 for stats, 200 for videos, 200 for shorts
        channel_id_max = max_size * 2 // 5  # 400 for default 1000
        stats_max = (max_size - channel_id_max) // 3  # 200
        videos_max = (max_size - channel_id_max) // 3  # 200
        shorts_max = max_size - channel_id_max - stats_max - videos_max  # 200

        self._channel_id_cache: TTLCache[str, str] = TTLCache(
            maxsize=channel_id_max,
            ttl=settings.CACHE_CHANNEL_TTL,
        )
        self._stats_cache: TTLCache[str, ChannelStats] = TTLCache(
            maxsize=stats_max,
            ttl=settings.CACHE_STATS_TTL,
        )
        self._videos_cache: TTLCache[str, list[VideoInfo]] = TTLCache(
            maxsize=videos_max,
            ttl=settings.CACHE_VIDEOS_TTL,
        )
        self._shorts_cache: TTLCache[str, list[VideoInfo]] = TTLCache(
            maxsize=shorts_max,
            ttl=settings.CACHE_VIDEOS_TTL,
        )

    @staticmethod
    def _normalize(query: str) -> str:
        """Normalize input for case-insensitive cache matching."""
        return query.strip().lower()

    def get_channel_id(self, normalized_input: str) -> str | None:
        """Retrieve a cached channel ID for the given input.

        Returns None on cache miss.
        """
        key = self._normalize(normalized_input)
        return self._channel_id_cache.get(key)

    def set_channel_id(self, normalized_input: str, channel_id: str) -> None:
        """Store a channel ID mapping in the cache."""
        key = self._normalize(normalized_input)
        self._channel_id_cache[key] = channel_id

    def get_stats(self, channel_id: str) -> ChannelStats | None:
        """Retrieve cached channel statistics.

        Returns None on cache miss.
        """
        return self._stats_cache.get(channel_id)

    def set_stats(self, channel_id: str, stats: ChannelStats) -> None:
        """Store channel statistics in the cache."""
        self._stats_cache[channel_id] = stats

    def get_videos(self, channel_id: str) -> list[VideoInfo] | None:
        """Retrieve cached video data.

        Returns None on cache miss.
        """
        return self._videos_cache.get(channel_id)

    def set_videos(self, channel_id: str, videos: list[VideoInfo]) -> None:
        """Store video data in the cache."""
        self._videos_cache[channel_id] = videos

    def get_shorts(self, channel_id: str) -> list[VideoInfo] | None:
        """Retrieve cached Shorts data.

        Returns None on cache miss.
        """
        return self._shorts_cache.get(channel_id)

    def set_shorts(self, channel_id: str, shorts: list[VideoInfo]) -> None:
        """Store Shorts data in the cache."""
        self._shorts_cache[channel_id] = shorts
