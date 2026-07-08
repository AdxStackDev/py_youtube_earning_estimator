"""Configuration module for YouTube Earnings Estimator.

Loads settings from environment variables and .env file using pydantic-settings.
Also supports Streamlit Community Cloud secrets (st.secrets).
System environment variables take precedence over .env file values.
"""

import os
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _load_streamlit_secrets() -> None:
    """Load Streamlit secrets into environment variables if available."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "YOUTUBE_API_KEY" in st.secrets:
            for key in st.secrets:
                if key not in os.environ:
                    os.environ[key] = str(st.secrets[key])
    except Exception:
        pass


_load_streamlit_secrets()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    YOUTUBE_API_KEY: str
    RPM_LOW: float = 1.00  # long-form low RPM (USD per 1000 views)
    RPM_HIGH: float = 5.00  # long-form high RPM (USD per 1000 views)
    RPM_SHORTS_LOW: float = 0.03  # shorts low RPM (USD per 1000 views)
    RPM_SHORTS_HIGH: float = 0.20  # shorts high RPM (USD per 1000 views)
    ADS_REVENUE_SHARE: float = 0.95  # portion of revenue from ads
    CACHE_TTL_SECONDS: int = 3600
    API_TIMEOUT_SECONDS: int = 10
    CACHE_CHANNEL_TTL: int = 86400  # 24 hours
    CACHE_STATS_TTL: int = 3600  # 1 hour
    CACHE_VIDEOS_TTL: int = 1800  # 30 minutes
    CACHE_MAX_SIZE: int = 1000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        """Validate configuration constraints."""
        # YOUTUBE_API_KEY must be non-empty
        if not self.YOUTUBE_API_KEY or not self.YOUTUBE_API_KEY.strip():
            raise ValueError("YOUTUBE_API_KEY must be a non-empty string")

        # RPM values must be positive
        if self.RPM_LOW <= 0:
            raise ValueError("RPM_LOW must be a positive number")
        if self.RPM_HIGH <= 0:
            raise ValueError("RPM_HIGH must be a positive number")

        # RPM_LOW must be less than RPM_HIGH
        if self.RPM_LOW >= self.RPM_HIGH:
            raise ValueError("RPM_LOW must be less than RPM_HIGH")

        # Shorts RPM values must be positive and low < high
        if self.RPM_SHORTS_LOW <= 0:
            raise ValueError("RPM_SHORTS_LOW must be a positive number")
        if self.RPM_SHORTS_HIGH <= 0:
            raise ValueError("RPM_SHORTS_HIGH must be a positive number")
        if self.RPM_SHORTS_LOW >= self.RPM_SHORTS_HIGH:
            raise ValueError("RPM_SHORTS_LOW must be less than RPM_SHORTS_HIGH")

        # Ads revenue share must be between 0 and 1 inclusive
        if not 0.0 <= self.ADS_REVENUE_SHARE <= 1.0:
            raise ValueError("ADS_REVENUE_SHARE must be between 0.0 and 1.0 inclusive")

        # CACHE_TTL_SECONDS must be >= 1
        if self.CACHE_TTL_SECONDS < 1:
            raise ValueError("CACHE_TTL_SECONDS must be >= 1")

        # API_TIMEOUT_SECONDS must be between 1 and 120 inclusive
        if self.API_TIMEOUT_SECONDS < 1 or self.API_TIMEOUT_SECONDS > 120:
            raise ValueError("API_TIMEOUT_SECONDS must be between 1 and 120 inclusive")

        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a singleton Settings instance."""
    return Settings()
