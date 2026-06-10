from __future__ import annotations

import io
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Semantic colors carried over from the originals (used as accents on the light theme).
POSITIVE = "#10b981"
NEGATIVE = "#ef4444"
WARNING = "#f97316"
ACCENT_NIKHIL = "#f59e0b"
ACCENT_PANKIT = "#0284c7"
INDIGO = "#6366f1"
MUTED = "#64748b"
SURFACE = "#ffffff"
BORDER = "#d1d5db"
SUBTLE_BORDER = "#e5e7eb"
PANEL_BG = "#ffffff"
PAGE_BG = "#f9fafb"
TEXT = "#111827"
TEXT_MUTED = "#6b7280"


def inject_visual_system() -> None:
    """Light-theme replica of the source dashboard component system."""
    st.markdown(
        """
<style>
:root {
  --scf-bg: #f9fafb;
  --scf-card: #ffffff;
  --scf-card-soft: #f8fafc;
  --scf-border: #d1d5db;
  --scf-border-soft: #e5e7eb;
  --scf-text: #111827;
  --scf-muted: #6b7280;
  --scf-faint: #9ca3af;
  --scf-green: #10b981;
  --scf-red: #ef4444;
  --scf-orange: #f97316;
  --scf-amber: #f59e0b;
  --scf-blue: #0284c7;
  --scf-indigo: #6366f1;
}
.block-container,
[data-testid="stMainBlockContainer"] {
  max-width: 1440px;
  padding: 2.1rem 2rem 3rem;
}
[data-testid="stSidebar"] {
  border-right: 1px solid var(--scf-border-soft);
}
h1 {
  font-size: 2rem !important;
  line-height: 1.12 !important;
  letter-spacing: 0 !important;
  margin-bottom: .35rem !important;
}
h2, h3, h4 {
  color: var(--scf-text) !important;
  letter-spacing: 0 !important;
}
h4, h5 {
  margin-top: 1.4rem !important;
  padding-bottom: .48rem !important;
  border-bottom: 1px solid var(--scf-border-soft) !important;
  font-size: .78rem !important;
  font-weight: 800 !important;
  letter-spacing: .08em !important;
  text-transform: uppercase !important;
  color: #374151 !important;
}
[data-testid="stMetric"] {
  background: var(--scf-card);
  border: 1px solid var(--scf-border-soft);
  border-left: 3px solid var(--scf-blue);
  border-radius: 8px;
  padding: 14px 16px;
  min-height: 96px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
}
[data-testid="stMetricLabel"] {
  color: var(--scf-muted);
  font-size: .66rem;
  font-weight: 800;
  letter-spacing: .07em;
  text-transform: uppercase;
}
[data-testid="stMetricValue"] {
  color: var(--scf-text);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
  font-size: 1.36rem;
  font-weight: 800;
  line-height: 1.15;
}
[data-testid="stMetricDelta"] {
  color: var(--scf-muted);
  font-size: .72rem;
}
div[data-testid="stHorizontalBlock"] {
  gap: .88rem;
}
.stPlotlyChart {
  background: var(--scf-card);
  border: 1px solid var(--scf-border-soft);
  border-radius: 8px;
  padding: 10px 12px 2px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
}
[data-testid="stDataFrame"] {
  border: 1px solid var(--scf-border-soft);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
}
div[role="radiogroup"] {
  gap: .35rem;
  flex-wrap: wrap;
}
div[role="radiogroup"] label {
  background: var(--scf-card);
  border: 1px solid var(--scf-border-soft);
  border-radius: 999px;
  padding: .26rem .72rem;
  min-height: 2rem;
}
div[role="radiogroup"] label:has(input:checked) {
  border-color: var(--scf-blue);
  background: #eff6ff;
  color: #075985;
  font-weight: 700;
}
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div {
  border-radius: 8px;
}
.stButton > button,
[data-testid="stDownloadButton"] button {
  border: 1px solid var(--scf-border-soft);
  border-radius: 999px;
  background: #ffffff;
  color: #374151;
  font-weight: 750;
  padding: .42rem .86rem;
  min-height: 2.25rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
}
.stButton > button:hover,
[data-testid="stDownloadButton"] button:hover {
  border-color: var(--scf-blue);
  color: #075985;
  background: #eff6ff;
}
.scf-section {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 1rem;
  margin: 1.35rem 0 .8rem;
  padding-bottom: .52rem;
  border-bottom: 1px solid var(--scf-border-soft);
}
.scf-section-title {
  font-size: .76rem;
  font-weight: 850;
  letter-spacing: .09em;
  text-transform: uppercase;
  color: #374151;
}
.scf-section-sub {
  color: var(--scf-muted);
  font-size: .78rem;
}
.scf-card {
  background: var(--scf-card);
  border: 1px solid var(--scf-border-soft);
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
}
.scf-kpi {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid var(--scf-border-soft);
  border-left: 3px solid var(--accent, #0284c7);
  border-radius: 8px;
  padding: 15px 17px;
  min-height: 104px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
}
.scf-kpi-label {
  color: var(--scf-muted);
  font-size: .66rem;
  font-weight: 800;
  letter-spacing: .075em;
  text-transform: uppercase;
  margin-bottom: .38rem;
}
.scf-kpi-value {
  color: var(--accent, #111827);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
  font-size: 1.42rem;
  font-weight: 850;
  line-height: 1.15;
}
.scf-kpi-sub {
  color: var(--scf-muted);
  font-size: .72rem;
  margin-top: .42rem;
}
.scf-chip {
  display: inline-block;
  border-radius: 999px;
  padding: 3px 9px;
  font-size: .68rem;
  font-weight: 750;
  margin: 0 6px 6px 0;
}
.scf-chip-blue { background:#dbeafe; color:#1e40af; }
.scf-chip-red { background:#fee2e2; color:#991b1b; }
.scf-chip-amber { background:#fffbeb; color:#92400e; }
.scf-chip-green { background:#d1fae5; color:#065f46; }
.scf-path-row {
  display: flex;
  gap: .5rem;
  flex-wrap: wrap;
  margin: .25rem 0 .65rem;
}
.scf-path-label {
  color: var(--scf-muted);
  font-size: .72rem;
  font-weight: 800;
  letter-spacing: .075em;
  text-transform: uppercase;
  margin-right: .1rem;
  align-self: center;
}
</style>
""",
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str = "") -> None:
    sub = f'<span class="scf-section-sub">{subtitle}</span>' if subtitle else ""
    st.markdown(
        f'<div class="scf-section"><span class="scf-section-title">{title}</span>{sub}</div>',
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, sub: str = "", color: str = ACCENT_PANKIT) -> str:
    sub_html = f'<div class="scf-kpi-sub">{sub}</div>' if sub else ""
    return (
        f'<div class="scf-kpi" style="--accent:{color}">'
        f'<div class="scf-kpi-label">{label}</div>'
        f'<div class="scf-kpi-value">{value}</div>'
        f'{sub_html}</div>'
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


def chip(text: str, variant: str = "blue") -> str:
    return f'<span class="scf-chip scf-chip-{variant}">{text}</span>'


def fmt_money(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    value = float(value)
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.0f}"


def fmt_pct(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{float(value) * 100:.1f}%"


def fmt_irr(value: float | None) -> str:
    """Matches the HTML fmtIRR: hides null/NaN/exact-zero as an em dash."""
    if value is None or pd.isna(value) or float(value) == 0:
        return "—"
    return f"{float(value):.2f}%"


def data_config() -> dict:
    return {
        "facility": st.column_config.NumberColumn("Facility", format="$ %.0f"),
        "overdraft": st.column_config.NumberColumn("Overdraft", format="$ %.0f"),
        "total_facility": st.column_config.NumberColumn("Total Facility", format="$ %.0f"),
        "util_denom": st.column_config.NumberColumn("Facility Basis", format="$ %.0f"),
        "ob": st.column_config.NumberColumn("OB", format="$ %.0f"),
        "ob_30d": st.column_config.NumberColumn("OB 30d Ago", format="$ %.0f"),
        "ob_90d": st.column_config.NumberColumn("OB 90d Ago", format="$ %.0f"),
        "peak_ob": st.column_config.NumberColumn("Peak OB", format="$ %.0f"),
        "avg_ob": st.column_config.NumberColumn("Avg OB", format="$ %.0f"),
        "mtd_repayments": st.column_config.NumberColumn("MTD Repayments", format="$ %.0f"),
        "net_ob": st.column_config.NumberColumn("Net OB", format="$ %.0f"),
        "target_ob_75": st.column_config.NumberColumn("Target OB 75%", format="$ %.0f"),
        "gap_to_75": st.column_config.NumberColumn("Gap to 75%", format="$ %.0f"),
        "headroom": st.column_config.NumberColumn("Headroom", format="$ %.0f"),
        "utilization_pct": st.column_config.NumberColumn("Utilization", format="%.1f%%"),
        "irr": st.column_config.NumberColumn("IRR", format="%.2f%%"),
        "ob_dent_30d": st.column_config.NumberColumn("30d OB Dent", format="$ %.0f"),
        "ob_dent_90d": st.column_config.NumberColumn("90d OB Dent", format="$ %.0f"),
        "ob_dent_30d_pct_display": st.column_config.NumberColumn("30d Dent %", format="%.1f%%"),
        "last_disbursed": st.column_config.DateColumn("Last Disbursed"),
        "first_disbursed": st.column_config.DateColumn("First Disbursed"),
        "peak_ob_date": st.column_config.DateColumn("Peak OB Date"),
        "raw_status": st.column_config.TextColumn("Status"),
        "account_type": st.column_config.TextColumn("Account Type"),
        "days_since_last": st.column_config.NumberColumn("Days Since Disb", format="%d"),
        "company": st.column_config.TextColumn("Company"),
        "am": st.column_config.TextColumn("AM"),
        "partner": st.column_config.TextColumn("Partner"),
        "health_score": st.column_config.ProgressColumn("Health /100", min_value=0, max_value=100, format="%d"),
    }


def show_table(frame: pd.DataFrame, columns: list[str] | None = None, height: int | None = None) -> None:
    if columns is not None:
        columns = [c for c in columns if c in frame.columns]
        frame = frame[columns]
    kwargs = {"height": height} if height is not None else {}
    st.dataframe(frame, use_container_width=True, hide_index=True, column_config=data_config(), **kwargs)


def base_layout(fig: go.Figure, title: str, height: int = 380) -> go.Figure:
    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=12, r=12, t=48, b=16),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11, color=TEXT_MUTED)),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, sans-serif", color=TEXT, size=12),
        title_font=dict(size=14, color=TEXT),
        hoverlabel=dict(bgcolor="#111827", bordercolor="#374151", font_color="#f9fafb"),
    )
    fig.update_yaxes(gridcolor="rgba(100,116,139,.18)", zeroline=False, tickfont=dict(color=TEXT_MUTED, size=11))
    fig.update_xaxes(gridcolor="rgba(100,116,139,.10)", zeroline=False, tickfont=dict(color=TEXT_MUTED, size=11))
    return fig


def grouped_bar(categories: list, series: dict[str, tuple[list, str]], title: str, money: bool = True, orientation: str = "v") -> go.Figure:
    """series: {name: (values, color)}."""
    fig = go.Figure()
    for name, (values, color) in series.items():
        if orientation == "h":
            fig.add_bar(y=categories, x=values, name=name, marker_color=color, orientation="h")
        else:
            fig.add_bar(x=categories, y=values, name=name, marker_color=color)
    fig.update_layout(barmode="group")
    if money:
        axis = dict(tickprefix="$")
        if orientation == "h":
            fig.update_xaxes(**axis)
        else:
            fig.update_yaxes(**axis)
    return base_layout(fig, title)


def donut(labels: list[str], values: list[float], colors: list[str], title: str) -> go.Figure:
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.6, marker=dict(colors=colors), textinfo="label+percent"))
    return base_layout(fig, title, height=340)


def export_portfolio_report(accounts: pd.DataFrame) -> bytes:
    total_facility = accounts["util_denom"].sum() if "util_denom" in accounts else accounts["total_facility"].sum()
    total_ob = accounts["ob"].sum()
    kpis = {
        "Accounts": len(accounts),
        "Total Facility": total_facility,
        "Total OB": total_ob,
        "Utilization (%)": (total_ob / total_facility * 100) if total_facility > 0 else 0,
        "MTD Repayments": accounts["mtd_repayments"].sum() if "mtd_repayments" in accounts else 0,
    }
    kpi_df = pd.DataFrame([kpis])
    
    raw_cols = ["id", "company", "am", "partner", "account_type", "total_facility", "util_denom", "ob", "utilization_pct", "mtd_repayments"]
    raw_cols = [c for c in raw_cols if c in accounts.columns]
    raw_data = accounts[raw_cols].copy()
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        kpi_df.to_excel(writer, sheet_name="KPI Summary", index=False)
        raw_data.to_excel(writer, sheet_name="Account Data", index=False)
    return output.getvalue()
