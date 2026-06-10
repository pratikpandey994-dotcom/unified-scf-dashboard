from __future__ import annotations

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
        margin=dict(l=10, r=10, t=48, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_yaxes(gridcolor="rgba(100,116,139,.18)")
    fig.update_xaxes(gridcolor="rgba(100,116,139,.10)")
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
