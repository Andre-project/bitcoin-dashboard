"""
Callbacks for On-Chain Metrics Dashboard - Academic Style

Features:
- Rigorous statistical comparisons (MA, z-scores, percentiles)
- Single-line Summary section
- Toggle-based explanation panels (under charts)
- Footer with last update timestamp
"""

from dash import callback, Input, Output
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

from data_collectors.mempool_api import fetch_hash_rate, fetch_difficulty
from data_collectors.blockchain_com_api import (
    fetch_active_addresses,
    fetch_transaction_count,
    fetch_miners_revenue,
    fetch_nvt_ratio
)
from utils.logger import get_logger

logger = get_logger(__name__)

# Constants
COLOR_GREEN = '#28a745'
COLOR_RED = '#dc3545'
COLOR_NEUTRAL = '#6c757d'
COLOR_BLUE = '#007bff'
COLOR_ORANGE = '#ffa500'
ARROW_UP = '\u25B2'
ARROW_DOWN = '\u25BC'


def get_chart_layout(title_y: str) -> dict:
    """Standard chart layout."""
    return dict(
        template='plotly_white',
        hovermode='x unified',
        height=400,
        margin=dict(l=60, r=40, t=40, b=60),
        font=dict(size=11, family="Arial, sans-serif"),
        xaxis_title='Date',
        yaxis_title=title_y,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(
            showgrid=True, gridwidth=1, gridcolor='#e9ecef',
            rangeselector=dict(buttons=list([
                dict(count=1, label="1M", step="month", stepmode="backward"),
                dict(count=3, label="3M", step="month", stepmode="backward"),
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(step="all", label="ALL")
            ]))
        ),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='#e9ecef')
    )


def format_with_commas(value: float) -> str:
    return f"{int(value):,}"


def format_delta(delta_pct: float, benchmark_name: str, benchmark_value: str) -> tuple:
    if delta_pct > 0.5:
        arrow, color, sign = ARROW_UP, COLOR_GREEN, "+"
    elif delta_pct < -0.5:
        arrow, color, sign = ARROW_DOWN, COLOR_RED, ""
    else:
        arrow, color, sign = "", COLOR_NEUTRAL, ""
    
    text = f"{arrow} {sign}{delta_pct:.1f}% vs {benchmark_name} ({benchmark_value})"
    style = {'color': color, 'fontSize': '0.75em', 'fontWeight': '500', 'marginBottom': '3px'}
    return text, style


def register_callbacks(app):
    """Register all callbacks for On-Chain Metrics tab."""

    # CALLBACK 1: Load data
    @callback(
        Output('onchain-data-store', 'data'),
        Input('onchain-refresh-interval', 'n_intervals'),
        prevent_initial_call=False
    )
    def load_onchain_data(n_intervals):
        try:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            
            logger.info(f"Loading on-chain data from {start_date} to {end_date}")
            result = {'last_update': datetime.now().isoformat()}
            
            for name, fetch_fn in [
                ('active_addresses', fetch_active_addresses),
                ('tx_count', fetch_transaction_count),
                ('hash_rate', fetch_hash_rate),
                ('difficulty', fetch_difficulty),
                ('nvt_ratio', fetch_nvt_ratio),
                ('miners_revenue', fetch_miners_revenue)
            ]:
                try:
                    df = fetch_fn(start_date, end_date)
                    if not df.empty:
                        df['date'] = df['date'].dt.strftime('%Y-%m-%d')
                        result[name] = df.to_dict('records')
                    else:
                        result[name] = []
                except Exception as e:
                    logger.error(f"Error fetching {name}: {e}")
                    result[name] = []
            
            return result
        except Exception as e:
            logger.error(f"Critical error: {e}")
            return {}

    # CALLBACK 2: Toggle Explanations
    @callback(
        [Output('active-addr-explanation', 'style'),
         Output('tx-count-explanation', 'style'),
         Output('hash-rate-explanation', 'style'),
         Output('difficulty-explanation', 'style'),
         Output('nvt-explanation', 'style'),
         Output('miners-rev-explanation', 'style')],
        Input('show-chart-explanations-toggle', 'value')
    )
    def toggle_chart_explanations(toggle_value):
        if toggle_value and 'show' in toggle_value:
            return ({
                'display': 'block', 'padding': '15px', 'backgroundColor': '#f8f9fa',
                'border': '1px solid #dee2e6', 'borderTop': '3px solid #007bff',
                'marginTop': '10px', 'marginBottom': '20px', 'borderRadius': '4px'
            },) * 6
        return ({'display': 'none'},) * 6

    # CALLBACK 3: Summary Section
    @callback(
        [Output('summary-network', 'children'), Output('summary-network', 'style'), Output('summary-network-detail', 'children'),
         Output('summary-security', 'children'), Output('summary-security', 'style'), Output('summary-security-detail', 'children'),
         Output('summary-valuation', 'children'), Output('summary-valuation', 'style'), Output('summary-valuation-detail', 'children'),
         Output('summary-economics', 'children'), Output('summary-economics', 'style'), Output('summary-economics-detail', 'children'),
         Output('last-update-footer', 'children')],
        Input('onchain-data-store', 'data')
    )
    def update_summary(data):
        default_style = {'fontWeight': 'bold', 'color': COLOR_NEUTRAL}
        defaults = ("--", default_style, " (Addr+TX avg)",
                   "--", default_style, " (Hash+Diff avg)",
                   "--", default_style, " (NVT vs median)",
                   "--", default_style, " (Rev vs 90d MA)",
                   "Last Update: --")
        
        if not data:
            return defaults
        
        try:
            deltas = {}
            
            # Network
            network_deltas = []
            for key, col, window in [('active_addresses', 'active_addresses', 30), ('tx_count', 'tx_count', 50)]:
                if key in data and data[key]:
                    df = pd.DataFrame(data[key])
                    if not df.empty and col in df.columns:
                        current = df[col].iloc[-1]
                        ma = df[col].rolling(window, min_periods=1).mean().iloc[-1]
                        if ma > 0:
                            network_deltas.append((current - ma) / ma * 100)
            deltas['network'] = sum(network_deltas) / len(network_deltas) if network_deltas else 0
            
            # Security
            security_deltas = []
            if 'hash_rate' in data and data['hash_rate']:
                df = pd.DataFrame(data['hash_rate'])
                if not df.empty and 'hash_rate_eh' in df.columns:
                    current = df['hash_rate_eh'].iloc[-1]
                    ath = df['hash_rate_eh'].max()
                    if ath > 0:
                        security_deltas.append((current - ath) / ath * 100)
            if 'difficulty' in data and data['difficulty']:
                df = pd.DataFrame(data['difficulty'])
                if not df.empty and 'adjustment_pct' in df.columns:
                    security_deltas.append(df['adjustment_pct'].iloc[-1])
            deltas['security'] = sum(security_deltas) / len(security_deltas) if security_deltas else 0
            
            # Valuation
            if 'nvt_ratio' in data and data['nvt_ratio']:
                df = pd.DataFrame(data['nvt_ratio'])
                if not df.empty and 'nvt_ratio' in df.columns:
                    current = df['nvt_ratio'].iloc[-1]
                    median = df['nvt_ratio'].median()
                    deltas['valuation'] = (current - median) / median * 100 if median > 0 else 0
                else:
                    deltas['valuation'] = 0
            else:
                deltas['valuation'] = 0
            
            # Economics
            if 'miners_revenue' in data and data['miners_revenue']:
                df = pd.DataFrame(data['miners_revenue'])
                if not df.empty and 'revenue_usd' in df.columns:
                    current = df['revenue_usd'].iloc[-1]
                    ma90 = df['revenue_usd'].rolling(90, min_periods=1).mean().iloc[-1]
                    deltas['economics'] = (current - ma90) / ma90 * 100 if ma90 > 0 else 0
                else:
                    deltas['economics'] = 0
            else:
                deltas['economics'] = 0
            
            def fmt(val):
                if val > 0.5:
                    return f"{ARROW_UP} +{val:.1f}%", {'fontWeight': 'bold', 'color': COLOR_GREEN}
                elif val < -0.5:
                    return f"{ARROW_DOWN} {val:.1f}%", {'fontWeight': 'bold', 'color': COLOR_RED}
                return "0.0%", {'fontWeight': 'bold', 'color': COLOR_NEUTRAL}
            
            net_t, net_s = fmt(deltas['network'])
            sec_t, sec_s = fmt(deltas['security'])
            val_t, val_s = fmt(deltas['valuation'])
            eco_t, eco_s = fmt(deltas['economics'])
            
            update_time = data.get('last_update', '')
            try:
                dt = datetime.fromisoformat(update_time)
                update_str = f"Last Update: {dt.strftime('%Y-%m-%d %H:%M')} UTC"
            except:
                update_str = "Last Update: --"
            
            return (net_t, net_s, " (Addr+TX avg)",
                   sec_t, sec_s, " (Hash+Diff avg)",
                   val_t, val_s, " (NVT vs median)",
                   eco_t, eco_s, " (Rev vs 90d MA)",
                   update_str)
        except Exception as e:
            logger.error(f"Summary error: {e}")
            return defaults

    # CALLBACK 4-9: Metric updates (Active Addresses, TX Count, Hash Rate, Difficulty, NVT, Miners Revenue)
    
    @callback(
        [Output('active-addr-current', 'children'), Output('active-addr-current', 'style'),
         Output('active-addr-delta', 'children'), Output('active-addr-delta', 'style'),
         Output('active-addr-context', 'children'), Output('active-addresses-chart', 'figure')],
        Input('onchain-data-store', 'data')
    )
    def update_active_addresses(data):
        value_style = {'fontSize': '1.4em', 'fontWeight': 'bold', 'color': '#212529', 'marginBottom': '5px'}
        defaults = ("--", value_style, "--", {}, "--", go.Figure())
        if not data or 'active_addresses' not in data or not data['active_addresses']:
            return defaults
        try:
            df = pd.DataFrame(data['active_addresses'])
            if df.empty or 'active_addresses' not in df.columns:
                return defaults
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            df['ma30'] = df['active_addresses'].rolling(30, min_periods=1).mean()
            current = df['active_addresses'].iloc[-1]
            ma30 = df['ma30'].iloc[-1]
            delta_pct = (current - ma30) / ma30 * 100 if ma30 > 0 else 0
            delta_text, delta_style = format_delta(delta_pct, "30d MA", f"{int(ma30/1000):,}k")
            last_30 = df['active_addresses'].tail(30)
            context = f"Range: {int(last_30.min()/1000):,}k - {int(last_30.max()/1000):,}k (30d)"
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['date'], y=df['active_addresses'], mode='lines', line=dict(color=COLOR_BLUE, width=2), name='Active Addresses'))
            fig.add_trace(go.Scatter(x=df['date'], y=df['ma30'], mode='lines', line=dict(color=COLOR_ORANGE, width=2, dash='dot'), name='MA30'))
            fig.update_layout(**get_chart_layout('Active Addresses'))
            return (format_with_commas(current), value_style, delta_text, delta_style, context, fig)
        except Exception as e:
            logger.error(f"Active addresses error: {e}")
            return defaults

    @callback(
        [Output('tx-count-current', 'children'), Output('tx-count-current', 'style'),
         Output('tx-count-delta', 'children'), Output('tx-count-delta', 'style'),
         Output('tx-count-context', 'children'), Output('tx-count-chart', 'figure')],
        Input('onchain-data-store', 'data')
    )
    def update_tx_count(data):
        value_style = {'fontSize': '1.4em', 'fontWeight': 'bold', 'color': '#212529', 'marginBottom': '5px'}
        defaults = ("--", value_style, "--", {}, "--", go.Figure())
        if not data or 'tx_count' not in data or not data['tx_count']:
            return defaults
        try:
            df = pd.DataFrame(data['tx_count'])
            if df.empty or 'tx_count' not in df.columns:
                return defaults
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            df['ma50'] = df['tx_count'].rolling(50, min_periods=1).mean()
            current = df['tx_count'].iloc[-1]
            ma50 = df['ma50'].iloc[-1]
            delta_pct = (current - ma50) / ma50 * 100 if ma50 > 0 else 0
            delta_text, delta_style = format_delta(delta_pct, "50d MA", f"{int(ma50/1000):,}k")
            mean, std = df['tx_count'].mean(), df['tx_count'].std()
            z = (current - mean) / std if std > 0 else 0
            context = f"StdDev: {z:+.1f}s from mean"
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['date'], y=df['tx_count'], mode='lines', fill='tozeroy', line=dict(color=COLOR_BLUE, width=2), fillcolor='rgba(0,123,255,0.15)', name='TX Count'))
            fig.add_trace(go.Scatter(x=df['date'], y=df['ma50'], mode='lines', line=dict(color=COLOR_ORANGE, width=2, dash='dot'), name='MA50'))
            fig.update_layout(**get_chart_layout('Transaction Count'))
            return (format_with_commas(current), value_style, delta_text, delta_style, context, fig)
        except Exception as e:
            logger.error(f"TX count error: {e}")
            return defaults

    @callback(
        [Output('hash-rate-current', 'children'), Output('hash-rate-current', 'style'),
         Output('hash-rate-delta', 'children'), Output('hash-rate-delta', 'style'),
         Output('hash-rate-context', 'children'), Output('hash-rate-chart', 'figure')],
        Input('onchain-data-store', 'data')
    )
    def update_hash_rate(data):
        value_style = {'fontSize': '1.4em', 'fontWeight': 'bold', 'color': '#212529', 'marginBottom': '5px'}
        defaults = ("--", value_style, "--", {}, "--", go.Figure())
        if not data or 'hash_rate' not in data or not data['hash_rate']:
            return defaults
        try:
            df = pd.DataFrame(data['hash_rate'])
            if df.empty or 'hash_rate_eh' not in df.columns:
                return defaults
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            current = df['hash_rate_eh'].iloc[-1]
            ath = df['hash_rate_eh'].max()
            delta_pct = (current - ath) / ath * 100 if ath > 0 else 0
            delta_text, delta_style = format_delta(delta_pct, "ATH", f"{ath:.1f}")
            context = f"% from Peak: {delta_pct:+.1f}%"
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['date'], y=df['hash_rate_eh'], mode='lines', fill='tozeroy', line=dict(color=COLOR_BLUE, width=2), fillcolor='rgba(0,123,255,0.15)', name='Hash Rate'))
            fig.update_layout(**get_chart_layout('Hash Rate (EH/s)'))
            return (f"{current:,.1f} EH/s", value_style, delta_text, delta_style, context, fig)
        except Exception as e:
            logger.error(f"Hash rate error: {e}")
            return defaults

    @callback(
        [Output('difficulty-current', 'children'), Output('difficulty-current', 'style'),
         Output('difficulty-delta', 'children'), Output('difficulty-delta', 'style'),
         Output('difficulty-context', 'children'), Output('difficulty-chart', 'figure')],
        Input('onchain-data-store', 'data')
    )
    def update_difficulty(data):
        value_style = {'fontSize': '1.4em', 'fontWeight': 'bold', 'color': '#212529', 'marginBottom': '5px'}
        defaults = ("--", value_style, "--", {}, "--", go.Figure())
        if not data or 'difficulty' not in data or not data['difficulty']:
            return defaults
        try:
            df = pd.DataFrame(data['difficulty'])
            if df.empty or 'difficulty' not in df.columns:
                return defaults
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            current = df['difficulty'].iloc[-1]
            adj = df['adjustment_pct'].iloc[-1] if 'adjustment_pct' in df.columns else 0
            if adj > 0.5:
                arrow, color, sign = ARROW_UP, COLOR_GREEN, "+"
            elif adj < -0.5:
                arrow, color, sign = ARROW_DOWN, COLOR_RED, ""
            else:
                arrow, color, sign = "", COLOR_NEUTRAL, ""
            delta_text = f"{arrow} {sign}{adj:.2f}% (last adjustment)"
            delta_style = {'color': color, 'fontSize': '0.75em', 'fontWeight': '500', 'marginBottom': '3px'}
            first = df['difficulty'].iloc[0]
            ytd = (current - first) / first * 100 if first > 0 else 0
            context = f"YTD Change: {ytd:+.1f}%"
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['date'], y=df['difficulty'], mode='lines', line=dict(color=COLOR_BLUE, width=2), name='Difficulty'))
            if 'adjustment_pct' in df.columns:
                fig.add_trace(go.Bar(x=df['date'], y=df['adjustment_pct'], name='Adjustment %', yaxis='y2', marker_color=[COLOR_GREEN if v > 0 else COLOR_RED for v in df['adjustment_pct']], opacity=0.4))
            layout = get_chart_layout('Difficulty')
            layout['yaxis2'] = dict(title='Adjustment %', side='right', overlaying='y', showgrid=False)
            fig.update_layout(**layout)
            return (f"{current/1e12:.2f}T", value_style, delta_text, delta_style, context, fig)
        except Exception as e:
            logger.error(f"Difficulty error: {e}")
            return defaults

    @callback(
        [Output('nvt-current', 'children'), Output('nvt-current', 'style'),
         Output('nvt-delta', 'children'), Output('nvt-delta', 'style'),
         Output('nvt-context', 'children'), Output('nvt-chart', 'figure')],
        Input('onchain-data-store', 'data')
    )
    def update_nvt(data):
        value_style = {'fontSize': '1.4em', 'fontWeight': 'bold', 'color': '#212529', 'marginBottom': '5px'}
        defaults = ("--", value_style, "--", {}, "--", go.Figure())
        if not data or 'nvt_ratio' not in data or not data['nvt_ratio']:
            return defaults
        try:
            df = pd.DataFrame(data['nvt_ratio'])
            if df.empty or 'nvt_ratio' not in df.columns:
                return defaults
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            current = df['nvt_ratio'].iloc[-1]
            median = df['nvt_ratio'].median()
            mean, std = df['nvt_ratio'].mean(), df['nvt_ratio'].std()
            delta_pct = (current - median) / median * 100 if median > 0 else 0
            delta_text, delta_style = format_delta(delta_pct, "Median", f"{median:.1f}")
            z = (current - mean) / std if std > 0 else 0
            extreme = " (extreme)" if abs(z) > 3 else ""
            context = f"Z-Score: {z:+.1f}s{extreme}"
            fig = go.Figure()
            y_max = max(df['nvt_ratio'].max(), 100)
            fig.add_hrect(y0=0, y1=55, fillcolor=COLOR_GREEN, opacity=0.08, line_width=0)
            fig.add_hrect(y0=55, y1=75, fillcolor=COLOR_NEUTRAL, opacity=0.08, line_width=0)
            fig.add_hrect(y0=75, y1=y_max, fillcolor=COLOR_RED, opacity=0.08, line_width=0)
            fig.add_trace(go.Scatter(x=df['date'], y=df['nvt_ratio'], mode='lines', line=dict(color=COLOR_BLUE, width=2), name='NVT Ratio'))
            fig.update_layout(**get_chart_layout('NVT Ratio'))
            return (f"{current:.1f}", value_style, delta_text, delta_style, context, fig)
        except Exception as e:
            logger.error(f"NVT error: {e}")
            return defaults

    @callback(
        [Output('miners-rev-current', 'children'), Output('miners-rev-current', 'style'),
         Output('miners-rev-delta', 'children'), Output('miners-rev-delta', 'style'),
         Output('miners-rev-context', 'children'), Output('miners-revenue-chart', 'figure')],
        Input('onchain-data-store', 'data')
    )
    def update_miners_revenue(data):
        value_style = {'fontSize': '1.4em', 'fontWeight': 'bold', 'color': '#212529', 'marginBottom': '5px'}
        defaults = ("--", value_style, "--", {}, "--", go.Figure())
        if not data or 'miners_revenue' not in data or not data['miners_revenue']:
            return defaults
        try:
            df = pd.DataFrame(data['miners_revenue'])
            if df.empty or 'revenue_usd' not in df.columns:
                return defaults
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            df['ma90'] = df['revenue_usd'].rolling(90, min_periods=1).mean()
            current = df['revenue_usd'].iloc[-1]
            ma90 = df['ma90'].iloc[-1]
            delta_pct = (current - ma90) / ma90 * 100 if ma90 > 0 else 0
            delta_text, delta_style = format_delta(delta_pct, "90d MA", f"${ma90/1e6:.1f}M")
            if len(df) >= 365:
                yoy = df['revenue_usd'].iloc[-365]
                yoy_chg = (current - yoy) / yoy * 100 if yoy > 0 else 0
                context = f"YoY Change: {yoy_chg:+.1f}%"
            else:
                last_30 = df['revenue_usd'].tail(30)
                context = f"30d Range: ${last_30.min()/1e6:.1f}M - ${last_30.max()/1e6:.1f}M"
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['date'], y=df['revenue_usd'], mode='lines', fill='tozeroy', line=dict(color=COLOR_BLUE, width=2), fillcolor='rgba(0,123,255,0.15)', name='Revenue'))
            fig.add_trace(go.Scatter(x=df['date'], y=df['ma90'], mode='lines', line=dict(color=COLOR_ORANGE, width=2, dash='dot'), name='MA90'))
            fig.update_layout(**get_chart_layout('Miners Revenue (USD)'))
            return (f"${current/1e6:.2f}M", value_style, delta_text, delta_style, context, fig)
        except Exception as e:
            logger.error(f"Miners revenue error: {e}")
            return defaults

    logger.info("On-Chain Metrics callbacks registered (Academic Style)")
