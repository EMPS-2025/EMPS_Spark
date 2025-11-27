import re
from typing import List, Dict, Any, Optional


class EnhancedResponseBuilder:
    def _minify(self, html: str) -> str:
        """
        Flattens HTML to a single line to keep Chainlit from treating it as a code block.
        """
        return re.sub(r'>\s+<', '><', html.strip())

    def _format_pct(self, value: float) -> str:
        if value == 0:
            return '<span class="badge badge-blue">-</span>'
        symbol = "▲" if value > 0 else "▼"
        color = "badge-green" if value > 0 else "badge-red"
        return f'<span class="badge {color}">{symbol} {abs(value):.1f}%</span>'

    def build_dashboard(
        self,
        primary_market: str,
        date_label: str,
        time_label: str,
        market_data: Dict[str, Dict],
        prev_year_data: Dict[str, Dict],
        derivative_data: List[Dict],
        insights: List[str],
        derivative_note: Optional[str] = None,
        total_market_vol: float = 0.0,
    ) -> str:
        """
        Build a full “executive dashboard” for the chat message.
        """

        # 1. KPI strip (MCP, volume, bids)
        stats_html = self._build_stats_row(primary_market, market_data, total_market_vol)

        # 2. Market comparison (DAM / GDAM / RTM vs prev year)
        comparison_html = self._build_comparison_table(market_data, prev_year_data)

        # 3. Derivatives panel
        deriv_html = self._build_derivatives(derivative_data, derivative_note)

        # 4. AI Insights panel
        insights_html = self._build_insights(insights)

        # --- Layout: header + stats + 2-column body + insights ---
        raw_html = f"""
        <div class="dashboard-container">
          <div class="header-section">
            <div class="header-main">
              <h1 class="main-title">{primary_market} Dashboard: {date_label}</h1>
              <div class="sub-time">⏱ {time_label}</div>
            </div>
            <div class="header-tags">
              <span class="pill pill-market">{primary_market}</span>
              <span class="pill pill-area">Area: ALL India</span>
            </div>
          </div>

          <div class="dashboard-grid">
            {stats_html}

            <div class="dashboard-split">
              {comparison_html}
              {deriv_html}
            </div>

            {insights_html}
          </div>
        </div>
        """

        return self._minify(raw_html)

    # ------------------------------------------------------------------
    #   KPI STRIP
    # ------------------------------------------------------------------
    def _build_stats_row(self, market: str, all_data: Dict, total_volume: float) -> str:
        data = all_data.get(market, {})
        price = data.get("twap", 0)
        market_vol = data.get("total_volume_gwh", 0)

        # Bids data
        buy_bids = data.get("purchase_bid_total_mw", 0)
        sell_bids = data.get("sell_bid_total_mw", 0)

        # Bid ratio
        bid_ratio = (buy_bids / sell_bids) if sell_bids > 0 else 0
        ratio_color = "badge-green" if bid_ratio > 1 else "badge-red"
        ratio_label = "Buy-Side Dominant" if bid_ratio > 1 else "Sell-Side Dominant"

        return f"""
        <div class="stats-row">
          <div class="stat-card">
            <div class="stat-label">Market Clearing Price</div>
            <div class="stat-value">₹{price:.2f}<span class="stat-unit">/kWh</span></div>
            <div class="stat-trend">
              <span class="badge badge-blue">System Normal</span>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-label">Total Traded Volume</div>
            <div class="stat-value">{total_volume:.1f}<span class="stat-unit">GWh</span></div>
            <div class="stat-trend">{market} share: {market_vol:.1f} GWh</div>
          </div>

          <div class="stat-card">
            <div class="stat-label">Market Depth (Avg MW)</div>
            <div class="bid-grid">
              <div>
                <div class="bid-label">Buy Bids</div>
                <div class="bid-val">{buy_bids:,.0f}</div>
              </div>
              <div class="bid-sep"></div>
              <div>
                <div class="bid-label">Sell Bids</div>
                <div class="bid-val">{sell_bids:,.0f}</div>
              </div>
            </div>
            <div class="stat-trend" style="margin-top:8px">
              <span class="badge {ratio_color}">{ratio_label} ({bid_ratio:.1f}x)</span>
            </div>
          </div>
        </div>
        """

    # ------------------------------------------------------------------
    #   MARKET COMPARISON TABLE
    # ------------------------------------------------------------------
    def _build_comparison_table(self, current: Dict, previous: Dict) -> str:
        rows = ""
        for m in ["DAM", "GDAM", "RTM"]:
            curr_data = current.get(m, {})
            prev_data = previous.get(m, {})

            p_cur = curr_data.get("twap", 0)
            p_prev = prev_data.get("twap", 0)
            v_cur = curr_data.get("total_volume_gwh", 0)
            v_prev = prev_data.get("total_volume_gwh", 0)

            yoy_p = ((p_cur - p_prev) / p_prev * 100) if p_prev > 0 else 0
            yoy_badge = self._format_pct(yoy_p)

            rows += f"""
            <tr>
              <td class="cell-primary">{m}</td>
              <td>
                <div class="cell-primary">{v_cur:.1f} GWh</div>
                <div class="cell-sub">Prev: {v_prev:.1f}</div>
              </td>
              <td>
                <div class="cell-primary">₹{p_cur:.3f}</div>
                <div class="cell-sub">Prev: ₹{p_prev:.3f}</div>
              </td>
              <td>{yoy_badge}</td>
            </tr>
            """

        return f"""
        <div class="data-section">
          <div class="section-header">
            <div class="section-title">📊 Market Comparison (Price &amp; Volume)</div>
          </div>
          <table class="modern-table">
            <thead>
              <tr>
                <th>Segment</th>
                <th>Volume</th>
                <th>Price</th>
                <th>YoY Price Δ</th>
              </tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
        """

    # ------------------------------------------------------------------
    #   DERIVATIVE MARKET PANEL
    # ------------------------------------------------------------------
    def _build_derivatives(
        self, rows: List[Dict], note: Optional[str] = None
    ) -> str:
        subtitle_html = (
            f'<div class="section-subtitle">{note}</div>' if note else ""
        )

        if not rows:
            return f"""
            <div class="data-section">
              <div class="section-header">
                <div class="section-title">💹 Derivative Market (Futures)</div>
                {subtitle_html}
              </div>
              <div class="empty-state">
                ℹ️ No Derivative Market data available for this date.
              </div>
            </div>
            """

        table_rows = ""
        for r in rows:
            price = float(r.get("close_price_rs_per_mwh", 0) or 0) / 1000.0
            month = r.get("contract_month")
            if hasattr(month, "strftime"):
                month = month.strftime("%b '%y")

            table_rows += f"""
            <tr>
              <td class="cell-primary">{r.get('exchange')}</td>
              <td>{r.get('commodity')}</td>
              <td>{month}</td>
              <td class="cell-primary">₹{price:.2f}</td>
            </tr>
            """

        return f"""
        <div class="data-section">
          <div class="section-header">
            <div class="section-title">💹 Derivative Market (Futures)</div>
            {subtitle_html}
          </div>
          <table class="modern-table">
            <thead>
              <tr>
                <th>Exchange</th>
                <th>Commodity</th>
                <th>Month</th>
                <th>Close Price</th>
              </tr>
            </thead>
            <tbody>{table_rows}</tbody>
          </table>
        </div>
        """

    # ------------------------------------------------------------------
    #   AI INSIGHTS PANEL
    # ------------------------------------------------------------------
    def _build_insights(self, insights: List[str]) -> str:
        if not insights:
            return ""

        items = "".join(
            [
                f'<div class="insight-item"><div class="insight-icon">⚡</div><div>{i}</div></div>'
                for i in insights
            ]
        )

        return f"""
        <div class="insights-container">
          <div style="font-weight:700;margin-bottom:1rem;color:#0f172a;">
            🤖 AI Market Insights
          </div>
          {items}
        </div>
        """
