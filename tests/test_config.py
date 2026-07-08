"""Tests for app/config.py configuration module."""

import pytest
from pydantic import ValidationError

from app.config import Settings, get_settings


class TestSettings:
    """Test the Settings class validation."""

    def _make_settings(self, **overrides):
        """Helper to create Settings with defaults + overrides."""
        defaults = {
            "YOUTUBE_API_KEY": "test-api-key-123",
            "RPM_LOW": 0.50,
            "RPM_HIGH": 4.00,
            "CACHE_TTL_SECONDS": 3600,
            "API_TIMEOUT_SECONDS": 10,
        }
        defaults.update(overrides)
        return Settings(**defaults)

    def test_valid_defaults(self):
        """Settings with valid API key and defaults should pass validation."""
        settings = self._make_settings()
        assert settings.YOUTUBE_API_KEY == "test-api-key-123"
        assert settings.RPM_LOW == 0.50
        assert settings.RPM_HIGH == 4.00
        assert settings.CACHE_TTL_SECONDS == 3600
        assert settings.API_TIMEOUT_SECONDS == 10
        assert settings.CACHE_CHANNEL_TTL == 86400
        assert settings.CACHE_STATS_TTL == 3600
        assert settings.CACHE_VIDEOS_TTL == 1800
        assert settings.CACHE_MAX_SIZE == 1000

    def test_empty_api_key_raises(self):
        """Empty YOUTUBE_API_KEY should raise validation error."""
        with pytest.raises(ValidationError, match="YOUTUBE_API_KEY must be a non-empty string"):
            self._make_settings(YOUTUBE_API_KEY="")

    def test_whitespace_api_key_raises(self):
        """Whitespace-only YOUTUBE_API_KEY should raise validation error."""
        with pytest.raises(ValidationError, match="YOUTUBE_API_KEY must be a non-empty string"):
            self._make_settings(YOUTUBE_API_KEY="   ")

    def test_rpm_low_not_positive_raises(self):
        """RPM_LOW <= 0 should raise validation error."""
        with pytest.raises(ValidationError, match="RPM_LOW must be a positive number"):
            self._make_settings(RPM_LOW=0)

        with pytest.raises(ValidationError, match="RPM_LOW must be a positive number"):
            self._make_settings(RPM_LOW=-1.0)

    def test_rpm_high_not_positive_raises(self):
        """RPM_HIGH <= 0 should raise validation error."""
        with pytest.raises(ValidationError, match="RPM_HIGH must be a positive number"):
            self._make_settings(RPM_HIGH=0)

    def test_rpm_low_gte_rpm_high_raises(self):
        """RPM_LOW >= RPM_HIGH should raise validation error."""
        with pytest.raises(ValidationError, match="RPM_LOW must be less than RPM_HIGH"):
            self._make_settings(RPM_LOW=5.0, RPM_HIGH=4.0)

        with pytest.raises(ValidationError, match="RPM_LOW must be less than RPM_HIGH"):
            self._make_settings(RPM_LOW=4.0, RPM_HIGH=4.0)

    def test_cache_ttl_less_than_one_raises(self):
        """CACHE_TTL_SECONDS < 1 should raise validation error."""
        with pytest.raises(ValidationError, match="CACHE_TTL_SECONDS must be >= 1"):
            self._make_settings(CACHE_TTL_SECONDS=0)

    def test_api_timeout_below_range_raises(self):
        """API_TIMEOUT_SECONDS < 1 should raise validation error."""
        with pytest.raises(ValidationError, match="API_TIMEOUT_SECONDS must be between 1 and 120"):
            self._make_settings(API_TIMEOUT_SECONDS=0)

    def test_api_timeout_above_range_raises(self):
        """API_TIMEOUT_SECONDS > 120 should raise validation error."""
        with pytest.raises(ValidationError, match="API_TIMEOUT_SECONDS must be between 1 and 120"):
            self._make_settings(API_TIMEOUT_SECONDS=121)

    def test_api_timeout_boundary_valid(self):
        """API_TIMEOUT_SECONDS at boundaries (1, 120) should be valid."""
        s1 = self._make_settings(API_TIMEOUT_SECONDS=1)
        assert s1.API_TIMEOUT_SECONDS == 1

        s2 = self._make_settings(API_TIMEOUT_SECONDS=120)
        assert s2.API_TIMEOUT_SECONDS == 120


class TestGetSettings:
    """Test the get_settings singleton accessor."""

    def test_get_settings_returns_settings_instance(self, monkeypatch):
        """get_settings() should return a Settings instance."""
        monkeypatch.setenv("YOUTUBE_API_KEY", "test-key-for-singleton")
        # Clear the lru_cache so it picks up the new env var
        get_settings.cache_clear()
        settings = get_settings()
        assert isinstance(settings, Settings)
        assert settings.YOUTUBE_API_KEY == "test-key-for-singleton"

    def test_get_settings_is_singleton(self, monkeypatch):
        """get_settings() should return the same instance on multiple calls."""
        monkeypatch.setenv("YOUTUBE_API_KEY", "test-key-singleton")
        get_settings.cache_clear()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
