"""YouTube Data API v3 client for channel resolution and statistics retrieval."""

import math
import re

import httpx

from app.exceptions import ChannelNotFoundError, ValidationError, YouTubeAPIError
from app.schemas import ChannelStats, VideoInfo

BASE_URL = "https://www.googleapis.com/youtube/v3"

# Regex patterns for URL-based channel resolution
CHANNEL_ID_PATTERN = re.compile(r"/channel/([A-Za-z0-9_-]+)")
HANDLE_IN_URL_PATTERN = re.compile(r"/@([A-Za-z0-9._-]+)")
LEGACY_URL_PATTERN = re.compile(r"/(?:c|user)/")


class YouTubeClient:
    """Synchronous client for YouTube Data API v3."""

    def __init__(self, api_key: str, timeout: int = 10) -> None:
        self._api_key = api_key
        self._timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    def _request(self, endpoint: str, params: dict) -> dict:
        """Make a GET request to the YouTube API and return parsed JSON.

        Raises YouTubeAPIError on HTTP errors or timeouts.
        """
        params["key"] = self._api_key
        url = f"{BASE_URL}/{endpoint}"
        try:
            response = self._client.get(url, params=params)
        except httpx.TimeoutException:
            raise YouTubeAPIError(status_code=408, message="Request timeout")
        except httpx.HTTPError as e:
            raise YouTubeAPIError(status_code=0, message=str(e))

        if response.status_code != 200:
            raise YouTubeAPIError(
                status_code=response.status_code,
                message=response.text,
            )

        return response.json()

    def resolve_channel(self, query: str) -> str:
        """Resolve any input (handle, URL, text) to a Channel_ID.

        Resolution strategy:
        1. Input starts with @ → channels.list?forHandle
        2. Input contains /channel/UC... → extract Channel_ID directly
        3. Input contains /@handle in URL → channels.list?forHandle
        4. Input contains /c/ or /user/ → search.list fallback
        5. Otherwise → search.list?type=channel&q=input

        Raises:
            ValidationError: If input is empty or exceeds 200 characters.
            ChannelNotFoundError: If no channel matches the input.
            YouTubeAPIError: On API errors or timeouts.
        """
        # Normalize input
        query = query.strip()

        # Input validation
        if not query:
            raise ValidationError("Input must not be empty")
        if len(query) > 200:
            raise ValidationError("Input must not exceed 200 characters")

        # Strategy 1: Handle prefixed with @
        if query.startswith("@"):
            return self._resolve_by_handle(query)

        # Strategy 2: Direct channel URL with /channel/ID
        channel_match = CHANNEL_ID_PATTERN.search(query)
        if channel_match:
            return channel_match.group(1)

        # Strategy 3: URL with /@handle
        handle_match = HANDLE_IN_URL_PATTERN.search(query)
        if handle_match:
            handle = f"@{handle_match.group(1)}"
            return self._resolve_by_handle(handle)

        # Strategy 4: Legacy URL with /c/ or /user/
        if LEGACY_URL_PATTERN.search(query):
            return self._resolve_by_search(query)

        # Strategy 5: Plain text search
        return self._resolve_by_search(query)

    def _resolve_by_handle(self, handle: str) -> str:
        """Resolve a channel handle using channels.list?forHandle."""
        data = self._request("channels", {
            "part": "id",
            "forHandle": handle,
        })

        items = data.get("items", [])
        if not items:
            raise ChannelNotFoundError(handle)

        return items[0]["id"]

    def _resolve_by_search(self, query: str) -> str:
        """Resolve a channel using search.list?type=channel."""
        data = self._request("search", {
            "part": "snippet",
            "type": "channel",
            "q": query,
            "maxResults": 1,
        })

        items = data.get("items", [])
        if not items:
            raise ChannelNotFoundError(query)

        return items[0]["snippet"]["channelId"]

    def get_channel_stats(self, channel_id: str) -> ChannelStats:
        """Fetch channel statistics and metadata.

        Uses channels.list with part=snippet,statistics,contentDetails.

        Raises:
            ChannelNotFoundError: If no channel found for the given ID.
            YouTubeAPIError: On API errors or timeouts.
        """
        data = self._request("channels", {
            "part": "snippet,statistics,contentDetails",
            "id": channel_id,
        })

        items = data.get("items", [])
        if not items:
            raise ChannelNotFoundError(channel_id)

        item = items[0]
        snippet = item["snippet"]
        statistics = item["statistics"]
        content_details = item["contentDetails"]

        # Handle hidden subscriber count
        hidden_subs = statistics.get("hiddenSubscriberCount", False)
        subscriber_count = 0 if hidden_subs else int(statistics.get("subscriberCount", 0))

        # Extract thumbnail URL (prefer higher resolution when available)
        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = None
        for size in ("high", "medium", "default"):
            if size in thumbnails and thumbnails[size].get("url"):
                thumbnail_url = thumbnails[size]["url"]
                break

        return ChannelStats(
            title=snippet["title"],
            subscriber_count=subscriber_count,
            total_views=int(statistics.get("viewCount", 0)),
            video_count=int(statistics.get("videoCount", 0)),
            uploads_playlist_id=content_details["relatedPlaylists"]["uploads"],
            channel_id=item.get("id", channel_id),
            custom_url=snippet.get("customUrl"),
            published_at=snippet.get("publishedAt"),
            thumbnail_url=thumbnail_url,
        )

    def get_recent_videos(
        self, uploads_playlist_id: str, max_results: int = 10
    ) -> list[VideoInfo]:
        """Fetch recent videos from an uploads playlist.

        Fetches video IDs from playlistItems.list, then batch-fetches
        video details (title, view count) from videos.list.

        Raises:
            YouTubeAPIError: On API errors or timeouts.
        """
        # Step 1: Get video IDs from playlist
        data = self._request("playlistItems", {
            "part": "contentDetails",
            "playlistId": uploads_playlist_id,
            "maxResults": max_results,
        })

        items = data.get("items", [])
        if not items:
            return []

        video_ids = [
            item["contentDetails"]["videoId"] for item in items
        ]

        # Step 2: Batch fetch video details (max 50 per request)
        videos: list[VideoInfo] = []
        num_batches = math.ceil(len(video_ids) / 50)

        for i in range(num_batches):
            batch = video_ids[i * 50 : (i + 1) * 50]
            batch_data = self._request("videos", {
                "part": "snippet,statistics",
                "id": ",".join(batch),
            })

            for video_item in batch_data.get("items", []):
                thumbnails = video_item["snippet"].get("thumbnails", {})
                thumbnail_url = None
                for size in ("medium", "default"):
                    if size in thumbnails and thumbnails[size].get("url"):
                        thumbnail_url = thumbnails[size]["url"]
                        break

                videos.append(VideoInfo(
                    video_id=video_item["id"],
                    title=video_item["snippet"]["title"],
                    view_count=int(video_item["statistics"].get("viewCount", 0)),
                    thumbnail_url=thumbnail_url,
                ))

        return videos

    def get_recent_shorts(
        self, channel_id: str, max_results: int = 10
    ) -> list[VideoInfo]:
        """Fetch recent Shorts from a channel using search API.

        Uses search.list with videoDuration=short to find Shorts,
        then batch-fetches video details (title, view count, thumbnail).

        Raises:
            YouTubeAPIError: On API errors or timeouts.
        """
        # Step 1: Search for short-duration videos on the channel
        data = self._request("search", {
            "part": "id",
            "channelId": channel_id,
            "type": "video",
            "videoDuration": "short",
            "order": "date",
            "maxResults": max_results,
        })

        items = data.get("items", [])
        if not items:
            return []

        video_ids = [item["id"]["videoId"] for item in items]

        # Step 2: Batch fetch video details (max 50 per request)
        shorts: list[VideoInfo] = []
        num_batches = math.ceil(len(video_ids) / 50)

        for i in range(num_batches):
            batch = video_ids[i * 50 : (i + 1) * 50]
            batch_data = self._request("videos", {
                "part": "snippet,statistics",
                "id": ",".join(batch),
            })

            for video_item in batch_data.get("items", []):
                thumbnails = video_item["snippet"].get("thumbnails", {})
                thumb_url = None
                for size in ("medium", "default"):
                    if size in thumbnails and thumbnails[size].get("url"):
                        thumb_url = thumbnails[size]["url"]
                        break

                shorts.append(VideoInfo(
                    video_id=video_item["id"],
                    title=video_item["snippet"]["title"],
                    view_count=int(video_item["statistics"].get("viewCount", 0)),
                    thumbnail_url=thumb_url,
                ))

        return shorts
