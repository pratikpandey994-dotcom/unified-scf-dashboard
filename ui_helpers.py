from __future__ import annotations

import io
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ── Semantic color tokens (used by views) ──────────────────────────────────
POSITIVE = "#0D6B52"
NEGATIVE = "#991B1B"
WARNING  = "#B45309"
ACCENT_NIKHIL = "#C8960A"
ACCENT_PANKIT = "#1D4ED8"
INDIGO  = "#4361EE"
MUTED   = "#6B7280"

# Extended palette (available for import)
NAVY        = "#0F1F3D"
GOLD        = "#C8960A"
EMERALD     = "#0D6B52"
AMBER_WARM  = "#B45309"
CRIMSON     = "#991B1B"
BLUE_ROYAL  = "#1D4ED8"

LIGHT_THEME = {
    "bg":               "#F5F4EF",
    "card":             "#FFFFFF",
    "card_soft":        "#FAF9F5",
    "border":           "#E8E4DC",
    "border_soft":      "#EDE8DF",
    "text":             "#1A1A1A",
    "muted":            "#6B7280",
    "faint":            "#9CA3AF",
    # Accent carries selection/emphasis (tabs, pills, headings). Navy works on light only.
    "accent":           "#0F1F3D",
    "accent_text":      "#FFFFFF",
    "heading":          "#0F1F3D",
    "sidebar_bg":       "#0F1F3D",
    "sidebar_text":     "rgba(255,255,255,0.82)",
    "sidebar_muted":    "rgba(255,255,255,0.35)",
    "sidebar_border":   "rgba(255,255,255,0.08)",
    "pill_selected_bg":   "#0F1F3D",
    "pill_selected_text": "#FFFFFF",
    "button_hover_bg":    "#0F1F3D",
    "button_hover_text":  "#FFFFFF",
}
DARK_THEME = {
    "bg":               "#0D1117",
    "card":             "#161C24",
    "card_soft":        "#0F1520",
    "border":           "#2D333B",
    "border_soft":      "#2D333B",
    "text":             "#E5E7EB",
    "muted":            "#9CA3AF",
    "faint":            "#6B7280",
    # On dark, navy is invisible — gold carries selection/emphasis instead.
    "accent":           "#E3B341",
    "accent_text":      "#0F1F3D",
    "heading":          "#F3F4F6",
    "sidebar_bg":       "#0A0D14",
    "sidebar_text":     "rgba(255,255,255,0.80)",
    "sidebar_muted":    "rgba(255,255,255,0.32)",
    "sidebar_border":   "rgba(255,255,255,0.07)",
    "pill_selected_bg":   "rgba(227,179,65,0.22)",
    "pill_selected_text": "#FCD34D",
    "button_hover_bg":    "rgba(227,179,65,0.18)",
    "button_hover_text":  "#FCD34D",
}

# Module-level globals updated by _apply_theme
SURFACE      = DARK_THEME["card"]
BORDER       = DARK_THEME["border"]
SUBTLE_BORDER = DARK_THEME["border_soft"]
PANEL_BG     = DARK_THEME["bg"]
PAGE_BG      = DARK_THEME["bg"]
TEXT         = DARK_THEME["text"]
TEXT_MUTED   = DARK_THEME["muted"]
HEADING      = DARK_THEME["heading"]


def _apply_theme(theme_mode: str) -> dict[str, str]:
    theme = LIGHT_THEME if theme_mode == "Light" else DARK_THEME
    global SURFACE, BORDER, SUBTLE_BORDER, PANEL_BG, PAGE_BG, TEXT, TEXT_MUTED, HEADING
    SURFACE      = theme["card"]
    BORDER       = theme["border"]
    SUBTLE_BORDER = theme["border_soft"]
    PANEL_BG     = theme["bg"]
    PAGE_BG      = theme["bg"]
    TEXT         = theme["text"]
    TEXT_MUTED   = theme["muted"]
    HEADING      = theme["heading"]
    return theme


_CSS_TEMPLATE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&family=DM+Mono:wght@300;400;500&display=swap');

:root {
  --scf-bg:          TK_BG;
  --scf-card:        TK_CARD;
  --scf-card-soft:   TK_CARD_SOFT;
  --scf-border:      TK_BORDER;
  --scf-border-soft: TK_BORDER_SOFT;
  --scf-text:        TK_TEXT;
  --scf-muted:       TK_MUTED;
  --scf-faint:       TK_FAINT;
  --scf-navy:        #0F1F3D;
  --scf-gold:        #C8960A;
  --scf-emerald:     #0D6B52;
  --scf-emerald-bg:  #ECFDF5;
  --scf-amber:       #B45309;
  --scf-amber-bg:    #FFFBEB;
  --scf-crimson:     #991B1B;
  --scf-crimson-bg:  #FEF2F2;
  --scf-blue:        #1D4ED8;
  --scf-blue-bg:     #EFF6FF;
  --scf-indigo:      #4361EE;
  --scf-accent:      TK_ACCENT;
  --scf-accent-text: TK_ACCENT_TEXT;
  --scf-heading:     TK_HEADING;
  --scf-pill-bg:     TK_PILL_BG;
  --scf-pill-text:   TK_PILL_TEXT;
  --scf-btn-bg:      TK_BTN_BG;
  --scf-btn-text:    TK_BTN_TEXT;
}

/* ── Base ── */
html, body, [data-testid="stAppViewContainer"] {
  font-family: 'DM Sans', 'Segoe UI', sans-serif !important;
}
.stApp, [data-testid="stApp"] {
  background: var(--scf-bg) !important;
  color: var(--scf-text);
}
.block-container, [data-testid="stMainBlockContainer"] {
  max-width: 1440px;
  padding: 1.8rem 2rem 3rem;
}

/* ── Typography ── */
h1 {
  font-family: 'Syne', sans-serif !important;
  font-size: 1.55rem !important;
  font-weight: 800 !important;
  letter-spacing: 0.04em !important;
  color: var(--scf-heading) !important;
  line-height: 1.1 !important;
  margin-bottom: 0.15rem !important;
}
h2, h3 {
  font-family: 'Syne', sans-serif !important;
  color: var(--scf-text) !important;
  letter-spacing: 0 !important;
}
h4, h5 {
  font-family: 'DM Sans', sans-serif !important;
  font-size: 0.7rem !important;
  font-weight: 700 !important;
  letter-spacing: 0.09em !important;
  text-transform: uppercase !important;
  color: var(--scf-muted) !important;
  margin-top: 1.5rem !important;
  padding-bottom: 0.48rem !important;
  border-bottom: 1px solid var(--scf-border-soft) !important;
}
p { font-size: 0.86rem; }
small, .small { font-size: 0.78rem; color: var(--scf-muted); }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background: TK_SIDEBAR_BG !important;
  border-right: 1px solid TK_SIDEBAR_BORDER !important;
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stCaption p,
[data-testid="stSidebar"] .stInfo,
[data-testid="stSidebar"] p {
  color: TK_SIDEBAR_TEXT !important;
}
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
  font-family: 'DM Sans', sans-serif !important;
  font-size: 0.64rem !important;
  font-weight: 700 !important;
  letter-spacing: 0.12em !important;
  text-transform: uppercase !important;
  color: TK_SIDEBAR_MUTED !important;
  border-bottom: none !important;
  padding-bottom: 0 !important;
  margin-top: 1.1rem !important;
  margin-bottom: 0.4rem !important;
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > * + * {
  margin-top: 0.1rem;
}
/* Sidebar radio pills on dark */
[data-testid="stSidebar"] div[role="radiogroup"] label {
  background: rgba(255,255,255,0.07) !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
  color: TK_SIDEBAR_TEXT !important;
  border-radius: 999px;
}
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
  background: var(--scf-gold) !important;
  border-color: var(--scf-gold) !important;
  color: var(--scf-navy) !important;
  font-weight: 700 !important;
}
/* Sidebar selectbox / multiselect */
[data-testid="stSidebar"] [data-baseweb="select"] > div {
  background: rgba(255,255,255,0.07) !important;
  border-color: rgba(255,255,255,0.15) !important;
  color: TK_SIDEBAR_TEXT !important;
  border-radius: 8px;
}
[data-testid="stSidebar"] [data-baseweb="select"] span {
  color: TK_SIDEBAR_TEXT !important;
}
/* Sidebar toggle */
[data-testid="stSidebar"] [data-testid="stToggle"] label span {
  color: TK_SIDEBAR_TEXT !important;
}
/* Sidebar file uploader */
[data-testid="stSidebar"] [data-testid="stFileUploader"] label {
  color: TK_SIDEBAR_TEXT !important;
}
/* Sidebar date input */
[data-testid="stSidebar"] [data-baseweb="input"] > div {
  background: rgba(255,255,255,0.07) !important;
  border-color: rgba(255,255,255,0.15) !important;
  border-radius: 8px;
}
[data-testid="stSidebar"] [data-baseweb="input"] input {
  color: TK_SIDEBAR_TEXT !important;
}
/* Sidebar expander */
[data-testid="stSidebar"] [data-testid="stExpander"] summary,
[data-testid="stSidebar"] [data-testid="stExpander"] span {
  color: TK_SIDEBAR_TEXT !important;
}
/* Sidebar info box */
[data-testid="stSidebar"] [data-testid="stAlertContainer"] {
  background: rgba(200,150,10,0.15) !important;
  border: 1px solid rgba(200,150,10,0.3) !important;
  color: #FCD34D !important;
}
[data-testid="stSidebar"] [data-testid="stAlertContainer"] p {
  color: #FCD34D !important;
}

/* ── Team radio (main area) ── */
div[role="radiogroup"] {
  gap: 0.35rem;
  flex-wrap: wrap;
}
div[role="radiogroup"] label {
  background: var(--scf-card);
  border: 1px solid var(--scf-border-soft);
  border-radius: 999px;
  padding: 0.28rem 0.8rem;
  min-height: 2rem;
  font-family: 'DM Sans', sans-serif;
  font-size: 0.82rem;
  transition: all 0.15s;
}
div[role="radiogroup"] label:has(input:checked) {
  border-color: var(--scf-accent);
  background: var(--scf-accent);
  color: var(--scf-accent-text);
  font-weight: 600;
}

/* ── KPI card (custom HTML) ── */
.scf-kpi {
  background: var(--scf-card);
  border: 1px solid var(--scf-border-soft);
  border-top: 3px solid var(--accent, var(--scf-accent));
  border-radius: 10px;
  padding: 14px 16px;
  min-height: 100px;
  box-shadow: 0 1px 3px rgba(15,31,61,0.04);
}
.scf-kpi-label {
  font-family: 'DM Sans', sans-serif;
  font-size: 0.65rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--scf-muted);
  margin-bottom: 5px;
}
.scf-kpi-value {
  font-family: 'DM Mono', ui-monospace, monospace;
  font-size: 1.38rem;
  font-weight: 400;
  color: var(--scf-text);
  line-height: 1.15;
}
.scf-kpi-sub {
  font-family: 'DM Sans', sans-serif;
  font-size: 0.72rem;
  color: var(--scf-muted);
  margin-top: 0.42rem;
}
.scf-heat-bar {
  margin-top: 8px;
  height: 3px;
  background: var(--scf-border);
  border-radius: 2px;
  overflow: hidden;
}
.scf-heat-fill {
  height: 100%;
  border-radius: 2px;
}

/* ── st.metric widget ── */
[data-testid="stMetric"] {
  background: var(--scf-card);
  border: 1px solid var(--scf-border-soft);
  border-top: 3px solid var(--scf-accent);
  border-left: none;
  border-radius: 10px;
  padding: 14px 16px;
  min-height: 96px;
  box-shadow: 0 1px 3px rgba(15,31,61,0.04);
}
[data-testid="stMetricLabel"] {
  font-family: 'DM Sans', sans-serif !important;
  font-size: 0.65rem !important;
  font-weight: 600 !important;
  letter-spacing: 0.06em !important;
  text-transform: uppercase !important;
  color: var(--scf-muted) !important;
}
[data-testid="stMetricValue"] {
  font-family: 'DM Mono', ui-monospace, monospace !important;
  font-size: 1.38rem !important;
  font-weight: 400 !important;
  color: var(--scf-text) !important;
  line-height: 1.15 !important;
}
[data-testid="stMetricDelta"] {
  font-family: 'DM Sans', sans-serif !important;
  font-size: 0.72rem !important;
  color: var(--scf-muted) !important;
}
div[data-testid="stHorizontalBlock"] { gap: 0.88rem; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
  gap: 0;
  background: transparent;
  border-bottom: 1px solid var(--scf-border);
  padding: 0;
  margin-bottom: 0.5rem;
  flex-wrap: wrap;          /* 10+ tabs: wrap instead of hiding behind a scroll */
  overflow-x: visible !important;
}
.stTabs [data-baseweb="tab-list"] button[data-testid="stTabScrollButton"] {
  display: none !important; /* no scroll arrows once tabs wrap */
}
.stTabs [data-baseweb="tab"] {
  font-family: 'DM Sans', sans-serif !important;
  font-size: 0.82rem !important;
  font-weight: 500 !important;
  color: var(--scf-muted) !important;
  padding: 0.55rem 1.1rem !important;
  background: transparent !important;
  border-bottom: 2px solid transparent !important;
  border-radius: 0 !important;
  transition: color 0.15s !important;
}
.stTabs [data-baseweb="tab"]:hover {
  color: var(--scf-text) !important;
  background: transparent !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
  font-weight: 700 !important;
  color: var(--scf-heading) !important;
  border-bottom: 2px solid var(--scf-accent) !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ── Chart container ── */
.stPlotlyChart {
  background: var(--scf-card) !important;
  border: 1px solid var(--scf-border-soft) !important;
  border-radius: 10px !important;
  padding: 10px 12px 2px !important;
  box-shadow: 0 1px 3px rgba(15,31,61,0.04) !important;
}

/* ── DataFrame ── */
[data-testid="stDataFrame"] {
  border: 1px solid var(--scf-border-soft) !important;
  border-radius: 10px !important;
  overflow: hidden !important;
  box-shadow: 0 1px 3px rgba(15,31,61,0.04) !important;
}

/* ── Buttons ── */
.stButton > button,
[data-testid="stDownloadButton"] button {
  font-family: 'DM Sans', sans-serif !important;
  border: 1px solid var(--scf-border-soft) !important;
  border-radius: 999px !important;
  background: var(--scf-card) !important;
  color: var(--scf-text) !important;
  font-weight: 600 !important;
  font-size: 0.8rem !important;
  padding: 0.4rem 0.9rem !important;
  min-height: 2.1rem !important;
  box-shadow: 0 1px 2px rgba(15,31,61,0.04) !important;
  transition: all 0.15s !important;
}
.stButton > button:hover,
[data-testid="stDownloadButton"] button:hover {
  border-color: var(--scf-accent) !important;
  background: var(--scf-btn-bg) !important;
  color: var(--scf-btn-text) !important;
}

/* ── Selectbox / Multiselect ── */
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div {
  border-radius: 8px !important;
}

/* ── Section header ── */
.scf-section {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 1rem;
  margin: 1.4rem 0 0.8rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--scf-border-soft);
}
.scf-section-title {
  font-family: 'DM Sans', sans-serif;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  color: var(--scf-muted);
}
.scf-section-sub {
  font-family: 'DM Sans', sans-serif;
  color: var(--scf-muted);
  font-size: 0.78rem;
}

/* ── Cards ── */
.scf-card {
  background: var(--scf-card);
  border: 1px solid var(--scf-border-soft);
  border-radius: 10px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(15,31,61,0.04);
}

/* ── Badges ── */
.scf-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 7px;
  border-radius: 4px;
  font-family: 'DM Sans', sans-serif;
  font-size: 0.67rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  white-space: nowrap;
}
.scf-badge-clean    { background: #ECFDF5; color: #0D6B52; }
.scf-badge-overdue  { background: #FFFBEB; color: #B45309; }
.scf-badge-npa      { background: #FEF2F2; color: #991B1B; }
.scf-badge-active   { background: #EFF6FF; color: #1D4ED8; }
.scf-badge-inactive { background: #F3F4F6; color: #64748B; }
.scf-badge-suspended { background: #FFF8E7; color: #92400E; }
.scf-badge-high     { background: #ECFDF5; color: #0D6B52; }
.scf-badge-mid      { background: #FFFBEB; color: #B45309; }
.scf-badge-low      { background: #FEF2F2; color: #991B1B; }
.scf-badge-zero     { background: #F3F4F6; color: #64748B; }
.scf-badge-workable { background: #F5F3FF; color: #5B21B6; }

/* ── Chips (legacy) ── */
.scf-chip {
  display: inline-block;
  border-radius: 4px;
  padding: 2px 8px;
  font-family: 'DM Sans', sans-serif;
  font-size: 0.67rem;
  font-weight: 700;
  margin: 0 5px 5px 0;
}
.scf-chip-blue   { background: #EFF6FF; color: #1D4ED8; }
.scf-chip-red    { background: #FEF2F2; color: #991B1B; }
.scf-chip-amber  { background: #FFFBEB; color: #B45309; }
.scf-chip-green  { background: #ECFDF5; color: #0D6B52; }

/* ── Quick-path row ── */
.scf-path-row {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin: 0.25rem 0 0.65rem;
}
.scf-path-label {
  font-family: 'DM Sans', sans-serif;
  color: var(--scf-muted);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  margin-right: 0.1rem;
  align-self: center;
}

/* ── Page header ── */
.scf-page-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding-bottom: 0.75rem;
  margin-bottom: 0.5rem;
  border-bottom: 2px solid var(--scf-accent);
}
.scf-page-title {
  font-family: 'Syne', sans-serif !important;
  font-size: 1.2rem !important;
  font-weight: 800 !important;
  letter-spacing: 0.08em !important;
  text-transform: uppercase !important;
  color: var(--scf-heading) !important;
}
.scf-page-tag {
  font-family: 'DM Sans', sans-serif;
  font-size: 0.78rem;
  color: var(--scf-muted);
  font-weight: 400;
  margin-left: 0.5rem;
}
.scf-page-date {
  font-family: 'DM Mono', monospace;
  font-size: 0.78rem;
  color: var(--scf-muted);
}

/* ── Util dist bar ── */
.scf-util-dist {
  display: flex;
  height: 28px;
  border-radius: 8px;
  overflow: hidden;
  gap: 2px;
  margin-bottom: 8px;
}
.scf-util-seg {
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'DM Mono', monospace;
  font-size: 10.5px;
  font-weight: 500;
  color: white;
  border-radius: 4px;
  cursor: default;
}

/* ── Caption overrides ── */
.stCaption, [data-testid="stCaptionContainer"] p {
  font-family: 'DM Sans', sans-serif;
  color: var(--scf-muted);
  font-size: 0.78rem;
}
TK_THEME_EXTRA
</style>
"""

# Dark-only overrides: pastel badge/chip backgrounds read as glare on dark cards —
# switch to translucent fills with bright text. Light mode keeps the originals.
_DARK_EXTRA_CSS = """
.scf-badge-clean, .scf-badge-high, .scf-chip-green { background: rgba(16,185,129,0.16); color: #6EE7B7; }
.scf-badge-overdue, .scf-badge-mid, .scf-badge-suspended, .scf-chip-amber { background: rgba(245,158,11,0.16); color: #FCD34D; }
.scf-badge-npa, .scf-badge-low, .scf-chip-red { background: rgba(239,68,68,0.16); color: #FCA5A5; }
.scf-badge-active, .scf-chip-blue { background: rgba(59,130,246,0.16); color: #93C5FD; }
.scf-badge-inactive, .scf-badge-zero { background: rgba(107,114,128,0.2); color: #D1D5DB; }
.scf-badge-workable { background: rgba(139,92,246,0.16); color: #C4B5FD; }
[data-testid="stAlertContainer"] { background: rgba(227,179,65,0.1) !important; color: var(--scf-text) !important; }
"""


def inject_visual_system(theme_mode: str = "Light") -> None:
    """Inject the full visual system CSS, parameterised by theme."""
    theme = _apply_theme(theme_mode)
    css = (
        _CSS_TEMPLATE
        .replace("TK_BG",           theme["bg"])
        .replace("TK_CARD_SOFT",    theme["card_soft"])
        .replace("TK_CARD",         theme["card"])
        .replace("TK_BORDER_SOFT",  theme["border_soft"])
        .replace("TK_BORDER",       theme["border"])
        .replace("TK_TEXT",         theme["text"])
        .replace("TK_MUTED",        theme["muted"])
        .replace("TK_FAINT",        theme["faint"])
        .replace("TK_SIDEBAR_BG",   theme["sidebar_bg"])
        .replace("TK_SIDEBAR_TEXT", theme["sidebar_text"])
        .replace("TK_SIDEBAR_MUTED",theme["sidebar_muted"])
        .replace("TK_SIDEBAR_BORDER",theme["sidebar_border"])
        .replace("TK_PILL_BG",      theme["pill_selected_bg"])
        .replace("TK_PILL_TEXT",     theme["pill_selected_text"])
        .replace("TK_BTN_BG",       theme["button_hover_bg"])
        .replace("TK_BTN_TEXT",     theme["button_hover_text"])
        .replace("TK_ACCENT_TEXT",  theme["accent_text"])
        .replace("TK_ACCENT",       theme["accent"])
        .replace("TK_HEADING",      theme["heading"])
        .replace("TK_THEME_EXTRA",  _DARK_EXTRA_CSS if theme_mode != "Light" else "")
    )
    st.markdown(css, unsafe_allow_html=True)


# ── Helper: section header ────────────────────────────────────────────────
def section_header(title: str, subtitle: str = "") -> None:
    sub = f'<span class="scf-section-sub">{subtitle}</span>' if subtitle else ""
    st.markdown(
        f'<div class="scf-section"><span class="scf-section-title">{title}</span>{sub}</div>',
        unsafe_allow_html=True,
    )


# ── Helper: metric card (custom HTML) ────────────────────────────────────
def metric_card(label: str, value: str, sub: str = "", color: str = NAVY, heat_pct: int | None = None) -> str:
    sub_html = f'<div class="scf-kpi-sub">{sub}</div>' if sub else ""
    heat_html = (
        f'<div class="scf-heat-bar"><div class="scf-heat-fill" style="width:{heat_pct}%;background:{color}"></div></div>'
        if heat_pct is not None else ""
    )
    return (
        f'<div class="scf-kpi" style="--accent:{color}">'
        f'<div class="scf-kpi-label">{label}</div>'
        f'<div class="scf-kpi-value">{value}</div>'
        f'{sub_html}{heat_html}</div>'
    )


def metric_cards(items: list[tuple[str, str, str, str]], columns: int | None = None) -> None:
    if not items:
        return
    columns = columns or min(len(items), 5)
    for start in range(0, len(items), columns):
        cols = st.columns(columns)
        for col, item in zip(cols, items[start : start + columns]):
            label, value, sub, color = item
            col.markdown(metric_card(label, value, sub, color), unsafe_allow_html=True)


# ── Helper: status badge ─────────────────────────────────────────────────
def status_badge(text: str, variant: str = "active") -> str:
    """Return an inline HTML badge. variant: clean|overdue|npa|active|inactive|suspended|high|mid|low|zero|workable"""
    return f'<span class="scf-badge scf-badge-{variant}">{text}</span>'


# ── Helper: chip (legacy) ────────────────────────────────────────────────
def chip(text: str, variant: str = "blue") -> str:
    return f'<span class="scf-chip scf-chip-{variant}">{text}</span>'


# ── Helper: util distribution bar ────────────────────────────────────────
def util_dist_bar(
    segments: list[dict],  # [{"label": "≥75%", "pct": 42, "count": 82, "color": "#0D6B52"}, …]
) -> str:
    segs_html = "".join(
        f'<div class="scf-util-seg" style="flex:{s["pct"]};background:{s["color"]}" '
        f'title="{s["count"]} accounts {s["label"]}">{s["pct"]}%</div>'
        for s in segments
        if s["pct"] > 0
    )
    return f'<div class="scf-util-dist">{segs_html}</div>'


# ── Formatters ───────────────────────────────────────────────────────────
def fmt_money(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    value = float(value)
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.0f}"


def fmt_pct(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{float(value) * 100:.1f}%"


def fmt_irr(value: float | None) -> str:
    if value is None or pd.isna(value) or float(value) == 0:
        return "—"
    return f"{float(value):.2f}%"


# ── Table helpers ────────────────────────────────────────────────────────
def data_config() -> dict:
    return {
        "facility":                 st.column_config.NumberColumn("Facility",         format="$ %.0f"),
        "overdraft":                st.column_config.NumberColumn("Overdraft",         format="$ %.0f"),
        "total_facility":           st.column_config.NumberColumn("Total Facility",    format="$ %.0f"),
        "util_denom":               st.column_config.NumberColumn("Facility Basis",    format="$ %.0f"),
        "ob":                       st.column_config.NumberColumn("OB",                format="$ %.0f"),
        "ob_30d":                   st.column_config.NumberColumn("OB 30d Ago",        format="$ %.0f"),
        "ob_90d":                   st.column_config.NumberColumn("OB 90d Ago",        format="$ %.0f"),
        "peak_ob":                  st.column_config.NumberColumn("Peak OB",           format="$ %.0f"),
        "avg_ob":                   st.column_config.NumberColumn("Avg OB",            format="$ %.0f"),
        "mtd_repayments":           st.column_config.NumberColumn("MTD Repayments",    format="$ %.0f"),
        "net_ob":                   st.column_config.NumberColumn("Net OB",            format="$ %.0f"),
        "target_ob_75":             st.column_config.NumberColumn("Target OB 75%",     format="$ %.0f"),
        "gap_to_75":                st.column_config.NumberColumn("Gap to 75%",        format="$ %.0f"),
        "headroom":                 st.column_config.NumberColumn("Headroom",          format="$ %.0f"),
        "utilization_pct":          st.column_config.NumberColumn("Utilization",       format="%.1f%%"),
        "irr":                      st.column_config.NumberColumn("IRR",               format="%.2f%%"),
        "ob_dent_30d":              st.column_config.NumberColumn("30d OB Dent",       format="$ %.0f"),
        "ob_dent_90d":              st.column_config.NumberColumn("90d OB Dent",       format="$ %.0f"),
        "ob_dent_30d_pct_display":  st.column_config.NumberColumn("30d Dent %",        format="%.1f%%"),
        "last_disbursed":           st.column_config.DateColumn("Last Disbursed"),
        "first_disbursed":          st.column_config.DateColumn("First Disbursed"),
        "peak_ob_date":             st.column_config.DateColumn("Peak OB Date"),
        "raw_status":               st.column_config.TextColumn("Status"),
        "account_type":             st.column_config.TextColumn("Account Type"),
        "days_since_last":          st.column_config.NumberColumn("Days Since Disb",   format="%d"),
        "company":                  st.column_config.TextColumn("Company"),
        "am":                       st.column_config.TextColumn("AM"),
        "partner":                  st.column_config.TextColumn("Partner"),
        "health_score":             st.column_config.ProgressColumn("Health /100", min_value=0, max_value=100, format="%d"),
    }


def show_table(frame: pd.DataFrame, columns: list[str] | None = None, height: int | None = None) -> None:
    if columns is not None:
        columns = [c for c in columns if c in frame.columns]
        frame = frame[columns]
    kwargs = {"height": height} if height is not None else {}
    st.dataframe(frame, width="stretch", hide_index=True, column_config=data_config(), **kwargs)


# ── Chart base layout ────────────────────────────────────────────────────
def base_layout(fig: go.Figure, title: str, height: int = 380) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color=HEADING, family="DM Sans"), x=0),
        height=height,
        margin=dict(l=12, r=12, t=44, b=16),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            font=dict(size=11, color=TEXT_MUTED, family="DM Sans"),
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, Segoe UI, sans-serif", color=TEXT, size=12),
        hoverlabel=dict(
            bgcolor=SURFACE,
            bordercolor=BORDER,
            font_color=TEXT,
            font_family="DM Sans",
        ),
    )
    fig.update_yaxes(
        gridcolor="#F3F0EB" if TEXT == "#1A1A1A" else "rgba(255,255,255,0.07)",
        zeroline=False,
        tickfont=dict(color=TEXT_MUTED, size=11, family="DM Mono"),
    )
    fig.update_xaxes(
        gridcolor="#F3F0EB" if TEXT == "#1A1A1A" else "rgba(255,255,255,0.06)",
        zeroline=False,
        tickfont=dict(color=TEXT_MUTED, size=11, family="DM Sans"),
    )
    return fig


def grouped_bar(
    categories: list,
    series: dict[str, tuple[list, str]],
    title: str,
    money: bool = True,
    orientation: str = "v",
) -> go.Figure:
    fig = go.Figure()
    for name, (values, color) in series.items():
        if orientation == "h":
            fig.add_bar(y=categories, x=values, name=name, marker_color=color, orientation="h",
                        marker=dict(line=dict(width=0)), opacity=0.92)
        else:
            fig.add_bar(x=categories, y=values, name=name, marker_color=color,
                        marker=dict(line=dict(width=0)), opacity=0.92)
    fig.update_layout(barmode="group", bargap=0.22, bargroupgap=0.05)
    if money:
        axis = dict(tickprefix="$")
        if orientation == "h":
            fig.update_xaxes(**axis)
        else:
            fig.update_yaxes(**axis)
    return base_layout(fig, title)


def donut(labels: list[str], values: list[float], colors: list[str], title: str) -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.65,
        marker=dict(colors=colors, line=dict(color="rgba(0,0,0,0)", width=0)),
        textinfo="label+percent",
        textfont=dict(family="DM Sans", size=12),
        hovertemplate="%{label}: %{value:.1f}%<extra></extra>",
    ))
    return base_layout(fig, title, height=340)


# ── Export ───────────────────────────────────────────────────────────────
def export_portfolio_report(accounts: pd.DataFrame) -> bytes:
    total_facility = (
        accounts["util_denom"].sum() if "util_denom" in accounts else accounts["total_facility"].sum()
    )
    total_ob = accounts["ob"].sum()
    kpis = {
        "Accounts":         len(accounts),
        "Total Facility":   total_facility,
        "Total OB":         total_ob,
        "Utilization (%)":  (total_ob / total_facility * 100) if total_facility > 0 else 0,
        "MTD Repayments":   accounts["mtd_repayments"].sum() if "mtd_repayments" in accounts else 0,
    }
    kpi_df = pd.DataFrame([kpis])
    raw_cols = [
        "id", "company", "am", "partner", "account_type",
        "total_facility", "util_denom", "ob", "utilization_pct", "mtd_repayments",
    ]
    raw_cols = [c for c in raw_cols if c in accounts.columns]
    raw_data = accounts[raw_cols].copy()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        kpi_df.to_excel(writer, sheet_name="KPI Summary", index=False)
        raw_data.to_excel(writer, sheet_name="Account Data", index=False)
    return output.getvalue()


# ── Backward-compat alias (kept so old imports don't break) ──────────────
def _legacy_visual_system_template(theme_mode: str = "Dark") -> None:
    inject_visual_system(theme_mode)
