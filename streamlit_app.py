"""Streamlit dashboard for the YouTube Earnings Estimator.

A premium YouTube Money Calculator UI with content-focus and revenue-window
toggles, a revenue-structure breakdown, and a standalone earnings calculator.
"""

from datetime import datetime

import streamlit as st

# MUST be the very first Streamlit command
st.set_page_config(
    page_title="YouTube Money Calculator",
    page_icon="\u25b6\ufe0f",
    layout="centered",
)

from app.cache import CacheManager
from app.config import get_settings
from app.estimator import Estimator
from app.exceptions import ChannelNotFoundError, ValidationError, YouTubeAPIError
from app.service import EstimationService
from app.youtube_client import YouTubeClient


@st.cache_resource
def get_service() -> EstimationService:
    """Create and cache the estimation service singleton."""
    settings = get_settings()
    client = YouTubeClient(api_key=settings.YOUTUBE_API_KEY, timeout=settings.API_TIMEOUT_SECONDS)
    estimator = Estimator()
    cache = CacheManager(settings)
    return EstimationService(
        youtube_client=client,
        estimator=estimator,
        cache=cache,
        rpm_shorts_low=settings.RPM_SHORTS_LOW,
        rpm_shorts_high=settings.RPM_SHORTS_HIGH,
        ads_share=settings.ADS_REVENUE_SHARE,
    )


# --------------------------------------------------------------------------- #
# Styling
# --------------------------------------------------------------------------- #
def inject_premium_css() -> None:
    """Inject premium CSS styling that works with Streamlit's rendering model."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700;800&display=swap');

        /* Hide Streamlit deploy button and header */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        [data-testid="stHeader"] {display: none;}
        [data-testid="stToolbar"] {display: none;}
        footer {visibility: hidden;}

        /* Global font */
        html, body, .stApp, [class*="css"] {
            font-family: "Roboto", "Inter", -apple-system, BlinkMacSystemFont,
                         "Segoe UI", "Helvetica Neue", Arial, sans-serif !important;
        }

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            max-width: 860px;
        }

        /* Brand bar */
        .brand-bar {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            margin-bottom: 1.2rem;
        }
        .brand-logo {
            background: #FF0000;
            color: #fff;
            font-weight: 800;
            font-size: 1rem;
            padding: 0.3rem 0.6rem;
            border-radius: 8px;
            letter-spacing: -0.5px;
        }
        .brand-title {
            font-size: 1.35rem;
            font-weight: 700;
            letter-spacing: -0.3px;
        }

        /* Cards */
        .premium-card {
            background: var(--secondary-background-color, #1A1A1A);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 1.5rem 1.75rem;
            margin: 0.75rem 0 1.25rem 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            border-top: 3px solid #FF0000;
            color: var(--text-color, #F1F1F1);
            overflow: hidden;
        }

        .premium-card-title {
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 0.75rem;
            letter-spacing: -0.3px;
            color: var(--text-color, #F1F1F1);
        }

        /* Channel header */
        .channel-head {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        .channel-avatar {
            width: 52px;
            height: 52px;
            border-radius: 50%;
            object-fit: cover;
            border: 2px solid rgba(128,128,128,0.2);
        }
        .channel-name {
            font-size: 1.2rem;
            font-weight: 700;
            line-height: 1.2;
            color: var(--text-color, #F1F1F1);
        }
        .channel-id {
            font-size: 0.78rem;
            color: var(--text-color, #F1F1F1);
            opacity: 0.6;
            margin-top: 2px;
        }
        .channel-link a {
            color: #CC0000;
            font-weight: 600;
            font-size: 0.88rem;
            text-decoration: none;
        }
        .channel-link a:hover { text-decoration: underline; }

        /* Stat tiles */
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 0.75rem;
            margin-top: 0.75rem;
        }
        .stat-tile {
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 0.8rem 0.6rem;
            text-align: center;
            background: var(--secondary-background-color, #1A1A1A);
        }
        .stat-label {
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-color, #F1F1F1);
            opacity: 0.6;
            margin-bottom: 0.25rem;
        }
        .stat-value {
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--text-color, #F1F1F1);
        }

        /* Revenue display */
        .revenue-hero {
            font-size: 2.8rem;
            font-weight: 800;
            color: #FF0000;
            line-height: 1;
            letter-spacing: -1px;
            margin-top: 0.5rem;
        }
        .revenue-sub {
            font-size: 0.95rem;
            font-weight: 500;
            margin-top: 0.3rem;
            color: var(--text-color, #F1F1F1);
            opacity: 0.8;
        }
        .revenue-baseline {
            font-size: 0.82rem;
            color: var(--text-color, #F1F1F1);
            opacity: 0.6;
            margin-top: 0.15rem;
        }

        /* Data rows */
        .data-row {
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-top: 1px solid rgba(255,255,255,0.06);
            font-size: 0.9rem;
            color: var(--text-color, #F1F1F1);
        }
        .data-row .label { opacity: 0.65; }
        .data-row .value { font-weight: 700; }

        /* Focus pill */
        .focus-pill {
            display: inline-block;
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 999px;
            padding: 0.2rem 0.75rem;
            font-size: 0.78rem;
            font-weight: 600;
            color: var(--text-color, #F1F1F1);
            opacity: 0.7;
            margin-bottom: 0.5rem;
        }

        /* Buttons */
        .stButton > button[kind="primary"],
        .stButton > button[data-testid="stBaseButton-primary"] {
            background: #FF0000 !important;
            color: #fff !important;
            border: none !important;
            border-radius: 999px !important;
            padding: 0.5rem 1.75rem !important;
            font-weight: 700 !important;
        }
        .stButton > button[kind="primary"]:hover,
        .stButton > button[data-testid="stBaseButton-primary"]:hover {
            background: #CC0000 !important;
        }

        /* Video preview grid */
        .video-preview {
            text-decoration: none;
            color: inherit;
            display: block;
            margin-bottom: 1rem;
            min-width: 0;
            overflow: hidden;
        }
        .video-preview:hover {
            transform: scale(1.02);
            transition: transform 200ms ease;
        }
        .video-thumb {
            position: relative;
            width: 100%;
            padding-top: 56.25%;
            overflow: hidden;
            border-radius: 8px;
            background: rgba(255,255,255,0.05);
        }
        .video-thumb img {
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            object-fit: cover;
        }
        .video-preview-title {
            margin-top: 0.4rem;
            font-size: 0.84rem;
            font-weight: 500;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            color: var(--text-color, #F1F1F1);
        }
        .video-preview-views {
            font-size: 0.72rem;
            color: var(--text-color, #F1F1F1);
            opacity: 0.6;
        }

        /* Shorts preview */
        .shorts-preview {
            text-decoration: none;
            color: inherit;
            display: block;
            margin-bottom: 0.75rem;
            min-width: 0;
            overflow: hidden;
        }
        .shorts-preview:hover {
            transform: scale(1.02);
            transition: transform 200ms ease;
        }
        .shorts-thumb {
            position: relative;
            width: 100%;
            padding-top: 177.78%;
            overflow: hidden;
            border-radius: 8px;
            background: rgba(255,255,255,0.05);
        }
        .shorts-thumb img {
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            object-fit: cover;
        }

        /* Grid containers */
        .video-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            overflow: hidden;
        }
        .shorts-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 0.75rem;
            overflow: hidden;
        }

        /* Disclaimer */
        .disclaimer-box {
            background: rgba(61,48,0,0.5);
            border: 1px solid rgba(255,224,130,0.3);
            border-radius: 12px;
            padding: 1rem 1.25rem;
            font-size: 0.82rem;
            color: #FFE082;
            line-height: 1.5;
            margin-top: 1rem;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 0.6rem 1.2rem;
            font-weight: 600;
            font-size: 0.9rem;
        }
        .stTabs [aria-selected="true"] {
            border-bottom-color: #FF0000 !important;
        }

        /* Labels */
        .stTextInput label p,
        .stNumberInput label p,
        .stSelectbox label p,
        .stRadio > label {
            font-weight: 500 !important;
            font-size: 0.88rem !important;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- #
# Formatting helpers
# --------------------------------------------------------------------------- #
def format_number(n: float) -> str:
    """Format a number with comma separators (no decimals)."""
    return f"{int(n):,}"


def format_compact_number(n: float) -> str:
    """Format large numbers compactly (e.g. 1.2M, 45.3K)."""
    n = int(n)
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def format_currency(amount: float) -> str:
    """Format a float as USD currency with comma separators."""
    return f"${amount:,.2f}"


def format_currency_compact(amount: float) -> str:
    """Format currency compactly for large hero numbers."""
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:,.2f}M"
    return f"${amount:,.0f}" if amount >= 1000 else f"${amount:,.2f}"


def format_date(iso: str | None) -> str:
    """Format an ISO 8601 timestamp as e.g. 'Oct 26, 2020'."""
    if not iso:
        return "\u2014"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except (ValueError, AttributeError):
        return "\u2014"


# --------------------------------------------------------------------------- #
# API call (direct, no backend server needed)
# --------------------------------------------------------------------------- #
def fetch_estimate(query: str) -> dict | None:
    """Call the estimation service directly. Returns data dict or None on error."""
    settings = get_settings()
    service = get_service()

    try:
        response = service.estimate(query, settings.RPM_LOW, settings.RPM_HIGH)
        return response.model_dump()
    except ValidationError as e:
        st.warning(str(e))
        return None
    except ChannelNotFoundError:
        st.error("Channel not found. Please check the name/URL and try again.")
        return None
    except YouTubeAPIError as e:
        if e.status_code == 408:
            st.error("The request timed out. Please try again.")
        else:
            st.error("YouTube API is temporarily unavailable. Please try again later.")
        return None
    except Exception:
        st.error("An unexpected error occurred. Please try again later.")
        return None


def _display_error(response) -> None:
    """Kept for compatibility but not used in direct mode."""
    pass


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
def render_channel_summary(data: dict) -> None:
    """Render the channel summary card as a single HTML block."""
    avatar = data.get("thumbnail_url", "")
    channel_url = data.get("channel_url", "")
    title = data.get("channel_title", "")
    ch_id = data.get("channel_id", "\u2014")

    avatar_html = (
        f'<img class="channel-avatar" src="{avatar}" alt="" />'
        if avatar
        else '<div class="channel-avatar" style="background:#FF0000;"></div>'
    )

    # Monetization eligibility check (YouTube Partner Program requirements):
    # - 1,000+ subscribers
    # - 4,000+ public watch hours in last 12 months (we estimate from views)
    # We can't know actual watch hours, so we use a heuristic:
    # If subs >= 1000 and total_views >= 100,000 => likely monetized
    subs = data.get("subscriber_count", 0)
    total_views = data.get("total_views", 0)
    is_likely_monetized = subs >= 1000 and total_views >= 100_000

    if is_likely_monetized:
        monetize_badge = (
            '<span style="display:inline-block; background:#1B5E20; color:#A5D6A7; '
            'font-size:0.72rem; font-weight:600; padding:0.2rem 0.6rem; '
            'border-radius:999px; margin-left:0.5rem;">'
            '\u2713 Likely Monetized</span>'
        )
    else:
        monetize_badge = (
            '<span style="display:inline-block; background:#4A1010; color:#EF9A9A; '
            'font-size:0.72rem; font-weight:600; padding:0.2rem 0.6rem; '
            'border-radius:999px; margin-left:0.5rem;">'
            '\u2717 Not Eligible</span>'
        )

    stats_html = "".join(
        f'<div class="stat-tile"><div class="stat-label">{lbl}</div>'
        f'<div class="stat-value">{val}</div></div>'
        for lbl, val in [
            ("Subscribers", format_number(data.get("subscriber_count", 0))),
            ("Views", format_number(data.get("total_views", 0))),
            ("Videos", format_number(data.get("video_count", 0))),
            ("Registration", format_date(data.get("published_at"))),
        ]
    )

    st.markdown(
        f"""<div class="premium-card">
            <div class="premium-card-title">Channel summary {monetize_badge}</div>
            <div class="channel-head">
                {avatar_html}
                <div style="flex:1;">
                    <div class="channel-name">{title}</div>
                    <div class="channel-id">Channel ID: {ch_id}</div>
                </div>
                <div class="channel-link">
                    <a href="{channel_url}" target="_blank">Open channel &#8599;</a>
                </div>
            </div>
            <div class="stat-grid">{stats_html}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def render_tabbed_calculator(data: dict | None) -> None:
    """Render the tabbed YouTube Money Calculator using Streamlit native tabs."""
    tab1, tab2 = st.tabs(["\U0001F4CA Channel Estimator", "\U0001F4B0 Manual Calculator"])

    with tab1:
        _render_channel_estimator_tab(data)

    with tab2:
        _render_manual_calculator_tab()


def _render_channel_estimator_tab(data: dict | None) -> None:
    """Render the Channel Estimator tab content."""
    if data is None:
        st.info("Enter a channel above and click **Calculate Earnings** to see revenue estimates.")
        return

    tcol1, tcol2 = st.columns(2)
    with tcol1:
        window = st.radio(
            "Revenue window",
            options=["Monthly", "Yearly"],
            horizontal=True,
            key="revenue_window",
        )
    with tcol2:
        focus = st.radio(
            "Content focus",
            options=["Videos", "Shorts"],
            horizontal=True,
            key="content_focus",
        )

    breakdown = data["long_form"] if focus == "Videos" else data["shorts"]
    window_mult = 12 if window == "Yearly" else 1

    medium = breakdown["earnings_medium"] * window_mult
    low = breakdown["earnings_low"] * window_mult
    high = breakdown["earnings_high"] * window_mult
    ads = breakdown["ads_revenue"] * window_mult
    premium = breakdown["premium_revenue"] * window_mult
    views_this_period = breakdown["estimated_monthly_views"] * window_mult

    st.markdown(
        f"""<div class="premium-card">
            <span class="focus-pill">{focus} &bull; {window}</span>
            <div class="revenue-hero">{format_currency_compact(medium)}</div>
            <div class="revenue-sub">estimated {window.lower()} revenue</div>
            <div class="revenue-baseline">Baseline daily views: {format_number(breakdown["baseline_daily_views"])}</div>
            <div class="data-row"><span class="label">Estimated range</span>
                <span class="value">{format_currency(low)} &ndash; {format_currency(high)}</span></div>
            <div class="data-row"><span class="label">Effective RPM</span>
                <span class="value">{format_currency(breakdown["rpm_effective"])}</span></div>
            <div class="data-row"><span class="label">Views this period</span>
                <span class="value">{format_number(views_this_period)}</span></div>
            <div class="premium-card-title" style="margin-top:1rem;">Revenue Structure ({window})</div>
            <div class="data-row"><span class="label">Ads (~{int(round(ads / medium * 100)) if medium else 95}%)</span>
                <span class="value">{format_currency(ads)}</span></div>
            <div class="data-row"><span class="label">Premium</span>
                <span class="value">{format_currency(premium)}</span></div>
        </div>""",
        unsafe_allow_html=True,
    )


def _render_manual_calculator_tab() -> None:
    """Render the Manual Calculator tab content."""
    st.caption("Estimate earnings from your own numbers \u2014 no channel lookup required.")

    c1, c2, c3 = st.columns(3)
    with c1:
        daily_views = st.number_input(
            "Daily views", min_value=0, value=10_000, step=1_000, key="calc_daily_views"
        )
    with c2:
        content_type = st.selectbox(
            "Content type", ["Long-form", "Shorts"], key="calc_content_type"
        )
    with c3:
        window = st.selectbox("Window", ["Daily", "Monthly", "Yearly"], key="calc_window")

    if content_type == "Long-form":
        default_low, default_high = 1.00, 5.00
    else:
        default_low, default_high = 0.03, 0.20

    r1, r2 = st.columns(2)
    with r1:
        rpm_low = st.number_input(
            "RPM low ($/1000 views)",
            min_value=0.01,
            max_value=100.0,
            value=default_low,
            step=0.01,
            key="calc_rpm_low",
        )
    with r2:
        rpm_high = st.number_input(
            "RPM high ($/1000 views)",
            min_value=0.01,
            max_value=100.0,
            value=default_high,
            step=0.01,
            key="calc_rpm_high",
        )

    if rpm_high < rpm_low:
        st.warning("RPM high must be greater than or equal to RPM low.")
        rpm_high = rpm_low

    period_days = {"Daily": 1, "Monthly": 30, "Yearly": 365}[window]
    period_views = daily_views * period_days

    low = round(period_views / 1000 * rpm_low, 2)
    high = round(period_views / 1000 * rpm_high, 2)
    medium = round((low + high) / 2, 2)

    st.markdown(
        f"""<div class="premium-card">
            <div class="revenue-hero" style="font-size:2.2rem;">{format_currency(medium)}</div>
            <div class="revenue-sub">estimated {window.lower()} revenue</div>
            <div class="data-row"><span class="label">Estimated range</span>
                <span class="value">{format_currency(low)} &ndash; {format_currency(high)}</span></div>
            <div class="data-row"><span class="label">{window} views</span>
                <span class="value">{format_number(period_views)}</span></div>
            <div class="data-row"><span class="label">Effective RPM</span>
                <span class="value">{format_currency(round((rpm_low + rpm_high) / 2, 2))}</span></div>
        </div>""",
        unsafe_allow_html=True,
    )


def render_video_previews(videos: list[dict]) -> None:
    """Render video preview grid with thumbnails."""
    if not videos:
        return

    videos = videos[:10]

    items_html = ""
    for v in videos:
        video_id = v.get("video_id", "")
        title = v.get("title", "")
        view_count = v.get("view_count", 0)
        thumbnail_url = v.get("thumbnail_url", "")

        thumb = (
            f'<img src="{thumbnail_url}" alt="" />' if thumbnail_url else ""
        )

        items_html += (
            f'<a href="https://www.youtube.com/watch?v={video_id}" target="_blank" class="video-preview">'
            f'<div class="video-thumb">{thumb}</div>'
            f'<div class="video-preview-title">{title}</div>'
            f'<div class="video-preview-views">{format_compact_number(view_count)} views</div>'
            f'</a>'
        )

    st.markdown(
        f"""<div class="premium-card">
            <div class="premium-card-title">Recent Videos</div>
            <div class="video-grid">
                {items_html}
            </div>
        </div>""",
        unsafe_allow_html=True,
    )


def render_shorts_previews(shorts: list[dict]) -> None:
    """Render Shorts preview grid."""
    if not shorts:
        return

    shorts = shorts[:10]

    items_html = ""
    for s in shorts:
        video_id = s.get("video_id", "")
        title = s.get("title", "")
        view_count = s.get("view_count", 0)
        thumbnail_url = s.get("thumbnail_url", "")

        thumb = (
            f'<img src="{thumbnail_url}" alt="" />' if thumbnail_url else ""
        )

        items_html += (
            f'<a href="https://www.youtube.com/shorts/{video_id}" target="_blank" class="shorts-preview">'
            f'<div class="shorts-thumb">{thumb}</div>'
            f'<div class="video-preview-title">{title}</div>'
            f'<div class="video-preview-views">{format_compact_number(view_count)} views</div>'
            f'</a>'
        )

    st.markdown(
        f"""<div class="premium-card">
            <div class="premium-card-title">Recent Shorts</div>
            <div class="shorts-grid">
                {items_html}
            </div>
        </div>""",
        unsafe_allow_html=True,
    )


def render_disclaimer() -> None:
    """Render the estimate accuracy disclaimer."""
    st.markdown(
        """<div class="disclaimer-box">
            &#9888;&#65039; <strong>Disclaimer:</strong> These figures are estimates based on publicly
            available data and assumed RPM (Revenue Per Mille) values. They do not represent
            actual channel earnings, which depend on ad rates, audience geography, content
            category, watch time, and sponsorship deals.
        </div>""",
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    """Run the Streamlit dashboard."""
    inject_premium_css()

    # Brand bar
    st.markdown(
        """<div class="brand-bar">
            <span class="brand-logo">\u25b6 YT</span>
            <span class="brand-title">YouTube Money Calculator</span>
        </div>""",
        unsafe_allow_html=True,
    )

    # Channel input
    query = st.text_input(
        "Channel name, handle, or URL",
        max_chars=256,
        placeholder="@channelname, youtube.com/@channelname, or a channel name",
    )
    submitted = st.button("Calculate Earnings", type="primary")

    if submitted:
        if not query or not query.strip():
            st.warning("Please enter a channel name, handle, or URL.")
        else:
            with st.spinner("Fetching channel data..."):
                data = fetch_estimate(query)
            if data:
                st.session_state["estimate_data"] = data

    # Results
    data = st.session_state.get("estimate_data")

    if data:
        render_channel_summary(data)
        render_tabbed_calculator(data)
        render_video_previews(data.get("recent_videos", []))
        render_shorts_previews(data.get("recent_shorts", []))
        render_disclaimer()
    else:
        render_tabbed_calculator(None)
        render_disclaimer()


if __name__ == "__main__":
    main()
