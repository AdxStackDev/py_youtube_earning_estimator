"""Estimator module for YouTube Earnings Estimator.

Calculates estimated monthly earnings from video view data and RPM values.
"""

from app.schemas import ContentBreakdown, EarningsResult, VideoInfo


class Estimator:
    """Calculates estimated YouTube channel earnings from video data."""

    def estimate_earnings(
        self,
        videos: list[VideoInfo],
        rpm_low: float = 0.50,
        rpm_high: float = 4.00,
    ) -> EarningsResult:
        """Calculate earnings from video view data and RPM values.

        Args:
            videos: List of VideoInfo objects with view counts.
            rpm_low: Low-end revenue per mille (per 1000 views).
            rpm_high: High-end revenue per mille (per 1000 views).

        Returns:
            EarningsResult with estimated monthly views and earnings range.
        """
        if len(videos) == 0:
            return EarningsResult(
                estimated_monthly_views=0.0,
                earnings_low=0.0,
                earnings_medium=0.0,
                earnings_high=0.0,
            )

        avg_views = sum(v.view_count for v in videos) / len(videos)

        # Monthly multiplier based on video count
        num_videos = len(videos)
        if num_videos >= 10:
            multiplier = 4.0
        elif num_videos >= 5:
            multiplier = 3.0
        else:
            multiplier = 2.0

        estimated_monthly_views = avg_views * multiplier

        low = round(estimated_monthly_views / 1000 * rpm_low, 2)
        high = round(estimated_monthly_views / 1000 * rpm_high, 2)
        medium = round((low + high) / 2, 2)

        return EarningsResult(
            estimated_monthly_views=estimated_monthly_views,
            earnings_low=low,
            earnings_medium=medium,
            earnings_high=high,
        )

    def build_breakdown(
        self,
        content_type: str,
        videos: list[VideoInfo],
        rpm_low: float,
        rpm_high: float,
        ads_share: float = 0.95,
    ) -> ContentBreakdown:
        """Build a full earnings breakdown for a given content focus.

        Derives baseline daily views, effective RPM, and an ads/premium
        revenue split from the medium earnings estimate.

        Args:
            content_type: "long_form" or "shorts".
            videos: List of VideoInfo objects with view counts.
            rpm_low: Low-end RPM for this content focus.
            rpm_high: High-end RPM for this content focus.
            ads_share: Fraction of revenue attributed to ads (rest is Premium).

        Returns:
            ContentBreakdown with earnings, view projections, and revenue split.
        """
        result = self.estimate_earnings(videos, rpm_low, rpm_high)

        estimated_monthly_views = result.estimated_monthly_views
        baseline_daily_views = round(estimated_monthly_views / 30.0, 0)
        rpm_effective = round((rpm_low + rpm_high) / 2.0, 2)

        ads_revenue = round(result.earnings_medium * ads_share, 2)
        premium_revenue = round(result.earnings_medium - ads_revenue, 2)

        return ContentBreakdown(
            content_type=content_type,
            rpm_low=rpm_low,
            rpm_high=rpm_high,
            rpm_effective=rpm_effective,
            estimated_monthly_views=estimated_monthly_views,
            baseline_daily_views=baseline_daily_views,
            earnings_low=result.earnings_low,
            earnings_medium=result.earnings_medium,
            earnings_high=result.earnings_high,
            ads_revenue=ads_revenue,
            premium_revenue=premium_revenue,
        )
