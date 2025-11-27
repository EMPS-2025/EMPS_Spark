# presenters/chart_generator.py
"""Generates interactive Plotly charts with multi-market support."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Any, Optional

# Professional Color Palette
COLORS = {
    "DAM": "#2563eb",     # Electric Blue
    "GDAM": "#16a34a",    # Success Green
    "RTM": "#f59e0b",     # Warm Amber
    "VOL": "rgba(148, 163, 184, 0.25)",  # Slate with transparency
    "BID_BUY": "#60a5fa",  # Light Blue
    "BID_SELL": "#fb7185", # Soft Coral
    "GRID": "#e2e8f0",
    "TEXT_PRIMARY": "#0f172a",
    "TEXT_SECONDARY": "#475569",
}


def _apply_card_layout(fig: go.Figure, title: str, subtitle: Optional[str] = None, show_legend: bool = True) -> go.Figure:
    """Apply a clean dashboard layout that mirrors card-style UI."""

    subtitle_html = (
        f"<br><span style='font-size: 12px; color: {COLORS['TEXT_SECONDARY']};'>{subtitle}</span>"
        if subtitle
        else ""
    )

    fig.update_layout(
        title=dict(text=f"<b>{title}</b>{subtitle_html}", x=0, xanchor="left"),
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=16, r=16, t=48, b=32),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.04,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.6)",
            bordercolor="rgba(226,232,240,0.6)",
            borderwidth=1,
        ),
        font=dict(family="Inter, 'Segoe UI', sans-serif", size=12, color=COLORS["TEXT_PRIMARY"]),
        plot_bgcolor="rgba(255,255,255,0)",
        paper_bgcolor="rgba(255,255,255,0)",
        showlegend=show_legend,
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor=COLORS["GRID"],
        zeroline=False,
        showline=False,
        tickfont=dict(color=COLORS["TEXT_SECONDARY"]),
        title=None,
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=COLORS["GRID"],
        zeroline=False,
        showline=False,
        tickfont=dict(color=COLORS["TEXT_SECONDARY"]),
        titlefont=dict(color=COLORS["TEXT_SECONDARY"]),
    )

    return fig

def generate_market_chart(
    market_name: str,
    time_label: str,
    rows: List[Dict[str, Any]],
    is_quarterly: bool
):
    if not rows: return None
    
    # Data Prep
    rows = sorted(rows, key=lambda x: (x['delivery_date'], x.get('block_index', x.get('slot_index', 0))))
    if is_quarterly:
        x_vals = [f"{r['delivery_date']} S-{r['slot_index']}" for r in rows]
        volumes = [r['mcv_mw'] * 0.25 for r in rows]
    else:
        x_vals = [f"{r['delivery_date']} H-{r.get('block_index', 0)}" for r in rows]
        volumes = [r['mcv_mw'] / 4.0 for r in rows]
        
    prices = [r['price_avg'] / 1000.0 for r in rows]
    buy_bids = [r['purchase_bid_mw'] for r in rows]
    sell_bids = [r['sell_bid_mw'] for r in rows]

    # Create Dual-Axis Chart
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 1. Volume (Bar - Background)
    fig.add_trace(
        go.Bar(
            x=x_vals,
            y=volumes,
            name="Volume",
            marker=dict(color=COLORS['VOL'], line=dict(color='rgba(148,163,184,0.35)', width=1)),
            hovertemplate="Volume: %{y:.2f} MWh<extra></extra>",
        ),
        secondary_y=False
    )

    # 2. Bids (Lines - Dotted)
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=buy_bids,
        name="Buy Bids",
        line=dict(color=COLORS['BID_BUY'], dash='dot', width=1.4),
        visible='legendonly',
        hovertemplate="Buy Bid: %{y:.1f} MW<extra></extra>",
    ), secondary_y=True)
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=sell_bids,
        name="Sell Bids",
        line=dict(color=COLORS['BID_SELL'], dash='dot', width=1.4),
        visible='legendonly',
        hovertemplate="Sell Bid: %{y:.1f} MW<extra></extra>",
    ), secondary_y=True)

    # 3. Price (Line - Primary Focus)
    fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=prices,
            name="Price",
            mode="lines+markers",
            line=dict(color=COLORS.get(market_name, '#2563eb'), width=3, shape='spline'),
            marker=dict(size=6, color='white', line=dict(color=COLORS.get(market_name, '#2563eb'), width=2)),
            hovertemplate="Price: ₹%{y:.2f}/kWh<extra></extra>",
        ),
        secondary_y=True
    )

    _apply_card_layout(fig, f"{market_name} Price & Volume", time_label)

    fig.update_xaxes(showgrid=False, showline=False, tickangle=-35)
    fig.update_yaxes(title="Vol (MWh)", secondary_y=False, showgrid=False, showline=False, showticklabels=False)
    fig.update_yaxes(title="Price (₹/kWh)", secondary_y=True, gridcolor=COLORS['GRID'])
    fig.update_traces(marker_line_width=0)
    fig.update_layout(hoverlabel=dict(bgcolor="white", font_color=COLORS['TEXT_PRIMARY']))

    return fig


def generate_multi_market_chart(
    market_data: Dict[str, List[Dict[str, Any]]],
    time_label: str,
    is_quarterly: bool
) -> Optional[go.Figure]:
    if not market_data: return None

    fig = go.Figure()

    for market_name, rows in market_data.items():
        if not rows: continue
        rows = sorted(rows, key=lambda x: (x['delivery_date'], x.get('block_index', x.get('slot_index', 0))))
        
        if is_quarterly:
            x_vals = [f"{r['delivery_date']} S-{r['slot_index']}" for r in rows]
        else:
            x_vals = [f"{r['delivery_date']} H-{r.get('block_index', 0)}" for r in rows]
        prices = [r['price_avg'] / 1000.0 for r in rows]

        fig.add_trace(go.Scatter(
            x=x_vals, y=prices, name=market_name,
            mode="lines+markers",
            line=dict(color=COLORS.get(market_name, '#666'), width=2.5, shape='spline'),
            marker=dict(size=5, color='white', line=dict(color=COLORS.get(market_name, '#666'), width=2)),
            hovertemplate=f"{market_name}: ₹%{{y:.2f}}/kWh<extra></extra>",
        ))

    _apply_card_layout(fig, "Market Comparison", time_label)

    fig.update_xaxes(showgrid=True, gridcolor=COLORS['GRID'], showline=False)
    fig.update_yaxes(title="Price (₹/kWh)", showgrid=True, gridcolor=COLORS['GRID'])
    fig.update_layout(hoverlabel=dict(bgcolor="white", font_color=COLORS['TEXT_PRIMARY']))

    return fig


def generate_comparison_chart(current_data, previous_data, year):
    markets = ['DAM', 'GDAM', 'RTM']
    
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Volume (GWh)", "Price (₹/kWh)"))
    
    has_data = False
    for market in markets:
        curr = current_data.get(market, {})
        prev = previous_data.get(market, {})

        if curr.get('total_volume_gwh', 0) > 0:
            has_data = True
            # Clean Bar Chart: Grouped
            fig.add_trace(
                go.Bar(
                    name=f"{market} '{year}",
                    x=[market],
                    y=[curr.get('total_volume_gwh', 0)],
                    marker_color=COLORS.get(market),
                    hovertemplate=f"%{{x}} {year}: %{{y:.2f}} GWh<extra></extra>",
                ),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Bar(
                    name=f"{market} '{year-1}",
                    x=[market],
                    y=[prev.get('total_volume_gwh', 0)],
                    marker_color=COLORS.get(market),
                    opacity=0.25,
                    showlegend=False,
                    hovertemplate="%{x} {year_minus}: %{y:.2f} GWh<extra></extra>".format(year_minus=year-1),
                ),
                row=1,
                col=1,
            )

            fig.add_trace(
                go.Bar(
                    name=f"{market}",
                    x=[market],
                    y=[curr.get('twap', 0)],
                    marker_color=COLORS.get(market),
                    showlegend=False,
                    hovertemplate=f"%{{x}} {year}: ₹%{{y:.2f}}/kWh<extra></extra>",
                ),
                row=1,
                col=2,
            )
            fig.add_trace(
                go.Bar(
                    name=f"{market} Prev",
                    x=[market],
                    y=[prev.get('twap', 0)],
                    marker_color=COLORS.get(market),
                    opacity=0.25,
                    showlegend=False,
                    hovertemplate="%{x} {year_minus}: ₹%{y:.2f}/kWh<extra></extra>".format(year_minus=year-1),
                ),
                row=1,
                col=2,
            )
            
    if not has_data: return None

    _apply_card_layout(fig, "Year-over-Year Performance")
    fig.update_layout(barmode='group', hoverlabel=dict(bgcolor="white", font_color=COLORS['TEXT_PRIMARY']))
    fig.update_xaxes(showgrid=False, showline=False)
    fig.update_yaxes(gridcolor=COLORS['GRID'])

    return fig
