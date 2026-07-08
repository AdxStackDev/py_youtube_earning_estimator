"""Custom exception classes for the YouTube Earnings Estimator."""


class ChannelNotFoundError(Exception):
    """Raised when no channel matches the provided input."""

    def __init__(self, query: str) -> None:
        self.query = query
        super().__init__(f"Channel not found for query: {query}")


class YouTubeAPIError(Exception):
    """Raised when YouTube Data API v3 returns an error or times out."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"YouTube API error {status_code}: {message}")


class ValidationError(Exception):
    """Raised for invalid input (empty, too long, bad format)."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
