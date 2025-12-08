"""
Bitcoin Treasuries Dashboard Callbacks - Final Version

Callbacks for:
- Key metrics
- Category bar chart (Top Holdings by Category)
- Category pie chart
- Holdings Evolution line chart (time series)
- 6 category tables (always visible, 2x3 grid)
- Proof of Reserve data
"""

from dash import html, callback, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from data_collectors.treasury_entities import (
    entities_manager, get_entities_data, get_category_dataframe,
    get_category_summary, CATEGORY_SECTIONS
)
from data_collectors.treasury_data import treasury_manager
from data_collectors.blockchain_com_api import get_circulating_supply
from data_collectors.proof_score import get_proof_score_for_entity, format_proof_score_display, create_proof_score_tooltip

from utils.logger import get_logger
logger = get_logger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

MAX_BTC_SUPPLY = 21_000_000

CATEGORY_ID_MAPPING = {
    'public-co': 'public_companies',
    'etfs': 'etfs',
    'private-co': 'private_companies',
    'countries': 'countries',
    'defi': 'defi',
    'mining': 'mining_companies'
}

CATEGORY_DISPLAY = {
    'public_companies': {'name': 'Public Companies', 'color': '#28a745'},
    'etfs': {'name': 'ETFs', 'color': '#007bff'},
    'private_companies': {'name': 'Private Companies', 'color': '#17a2b8'},
    'countries': {'name': 'Countries', 'color': '#ffc107'},
    'defi': {'name': 'DeFi', 'color': '#6f42c1'},
    'mining_companies': {'name': 'Mining Companies', 'color': '#fd7e14'}
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def format_btc(value: float) -> str:
    """Format BTC value with K/M suffix."""
    if pd.isna(value) or value == 0:
        return "0"
    if value >= 1_000_000:
        return f"{value/1_000_000:.2f}M"
    if value >= 1_000:
        return f"{value/1_000:.1f}K"
    return f"{int(value):,}"


def format_usd(value: float) -> str:
    """Format USD value with B/M suffix."""
    if pd.isna(value) or value == 0:
        return "$0"
    if value >= 1_000_000_000_000:
        return f"${value/1_000_000_000_000:.2f}T"
    if value >= 1_000_000_000:
        return f"${value/1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"${value/1_000_000:.1f}M"
    return f"${value:,.0f}"


def format_pct(value: float) -> str:
    """Format percentage value."""
    if pd.isna(value):
        return "0.00%"
    return f"{value:.2f}%"


def create_empty_figure(message: str = "No data available") -> go.Figure:
    """Create an empty placeholder figure."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=14, color="#6c757d")
    )
    fig.update_layout(
        height=350,
        template="plotly_white",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(l=20, r=20, t=20, b=20)
    )
    return fig


def get_historical_evolution_data() -> pd.DataFrame:
    """
    Get historical holdings evolution by category.
    Uses treasury_data module if available, otherwise generates sample data.
    """
    try:
        # Try to get historical data from treasury_data module
        hist_df = treasury_manager.get_historical_data(days=90)
        
        if hist_df is not None and not hist_df.empty and 'timestamp' in hist_df.columns:
            # Convert wide format to long format for plotting
            value_cols = [c for c in hist_df.columns if c != 'timestamp']
            
            if value_cols:
                # Melt to long format
                long_df = hist_df.melt(
                    id_vars=['timestamp'],
                    value_vars=value_cols,
                    var_name='category',
                    value_name='btc_holdings'
                )
                
                # Map category names to display names
                category_name_map = {
                    'etfs': 'ETFs',
                    'public_companies': 'Public Companies',
                    'private_companies': 'Private Companies',
                    'countries': 'Countries',
                    'defi': 'DeFi',
                    'mining_companies': 'Mining Companies'
                }
                long_df['category'] = long_df['category'].map(lambda x: category_name_map.get(x, x))
                
                # Clean data
                long_df = long_df.dropna()
                long_df = long_df.sort_values('timestamp')
                
                logger.info(f"Loaded {len(long_df)} historical data points")
                return long_df
        
        # Generate sample data if no historical data available
        logger.info("Generating sample evolution data...")
        return generate_sample_evolution_data()
        
    except Exception as e:
        logger.error(f"Error loading historical data: {e}")
        return generate_sample_evolution_data()


def generate_sample_evolution_data() -> pd.DataFrame:
    """Generate sample evolution data for demonstration."""
    # Generate 90 days of sample data
    dates = pd.date_range(end=datetime.now(), periods=90, freq='D')
    
    categories = {
        'ETFs': 1_200_000,
        'Public Companies': 750_000,
        'Countries': 520_000,
        'Private Companies': 400_000,
        'DeFi': 250_000,
        'Mining Companies': 100_000
    }
    
    data = []
    for i, date in enumerate(dates):
        for category, base_value in categories.items():
            # Add some random variation and slight upward trend
            noise = np.random.normal(0, 0.02)  # 2% noise
            trend = 1 + (i / 90) * 0.05  # 5% growth over period
            value = base_value * trend * (1 + noise)
            
            data.append({
                'timestamp': date,
                'category': category,
                'btc_holdings': max(0, value)
            })
    
    return pd.DataFrame(data)


# =============================================================================
# CALLBACK REGISTRATION
# =============================================================================

def register_callbacks(app):
    """Register all callbacks for the Companies tab."""
    
    # =========================================================================
    # MAIN DATA LOADING CALLBACK
    # =========================================================================
    
    @app.callback(
        [
            # Key metrics
            Output('treasury-total-entities', 'children'),
            Output('treasury-entities-subtitle', 'children'),
            Output('treasury-total-btc', 'children'),
            Output('treasury-btc-subtitle', 'children'),
            Output('treasury-total-value', 'children'),
            Output('treasury-value-subtitle', 'children'),
            Output('treasury-supply-pct', 'children'),
            Output('treasury-supply-subtitle', 'children'),
            # Charts
            Output('treasury-category-bar', 'figure'),
            Output('treasury-pie-chart', 'figure'),
            # Evolution data store (chart generated by separate callback)
            Output('evolution-data-store', 'data'),
            # Category tables - data
            Output('public-co-table', 'data'),
            Output('etfs-table', 'data'),
            Output('private-co-table', 'data'),
            Output('countries-table', 'data'),
            Output('defi-table', 'data'),
            Output('mining-table', 'data'),
            # Category tables - tooltips
            Output('public-co-table', 'tooltip_data'),
            Output('etfs-table', 'tooltip_data'),
            Output('private-co-table', 'tooltip_data'),
            Output('countries-table', 'tooltip_data'),
            Output('defi-table', 'tooltip_data'),
            Output('mining-table', 'tooltip_data'),
            # Status
            Output('treasury-btc-price', 'children'),
            Output('treasury-last-update', 'children'),
            Output('treasury-error-alert', 'children'),
            Output('treasury-entities-store', 'data'),
        ],
        [Input('treasury-refresh-btn', 'n_clicks')],
        prevent_initial_call=False
    )
    def load_treasury_data(n_clicks):
        """Load all treasury data and populate all components."""
        
        try:
            force_refresh = n_clicks is not None and n_clicks > 0
            data = get_entities_data(force_refresh=force_refresh)
            
            if not data:
                logger.warning("No treasury data available")
                empty_fig = create_empty_figure()
                return (
                    "--", "", "--", "", "--", "", "--", "",
                    empty_fig, empty_fig, None,  # bar, pie, evolution data
                    [], [], [], [], [], [],  # table data
                    [], [], [], [], [], [],  # tooltip data
                    "", "Last update: N/A",
                    html.Div("No data available", style={'color': '#dc3545'}),
                    None
                )
            
            btc_price = entities_manager.btc_price
            
            # === CALCULATE TOTALS ===
            total_entities = 0
            total_btc = 0
            category_totals = []
            
            for cat_key in CATEGORY_ID_MAPPING.values():
                stats = get_category_summary(cat_key)
                total_entities += stats['count']
                if cat_key != 'mining_companies':
                    total_btc += stats['total_btc']
                
                category_totals.append({
                    'category': CATEGORY_DISPLAY[cat_key]['name'],
                    'btc': stats['total_btc'],
                    'color': CATEGORY_DISPLAY[cat_key]['color']
                })
            
            total_value = total_btc * btc_price
            
            # Get circulating supply dynamically (not 21M max)
            circulating_supply = get_circulating_supply()
            supply_pct = (total_btc / circulating_supply * 100) if circulating_supply > 0 else 0
            
            # === KEY METRICS ===
            entities_str = str(total_entities)
            entities_sub = "companies, ETFs, countries"
            btc_str = format_btc(total_btc)
            btc_sub = "across all holders"
            value_str = format_usd(total_value)
            value_sub = f"@ ${btc_price:,.0f}/BTC"
            supply_str = format_pct(supply_pct)
            supply_sub = f"of {circulating_supply/1_000_000:.2f}M circulating"
            
            # === CATEGORY BAR CHART ===
            cat_df = pd.DataFrame(category_totals)
            cat_df = cat_df.sort_values('btc', ascending=True)
            
            bar_fig = px.bar(
                cat_df,
                x='btc',
                y='category',
                orientation='h',
                color='category',
                color_discrete_map={row['category']: row['color'] for _, row in cat_df.iterrows()},
                labels={'btc': 'BTC Holdings', 'category': ''}
            )
            bar_fig.update_layout(
                height=380,
                template="plotly_white",
                margin=dict(l=20, r=40, t=10, b=20),
                showlegend=False,
                xaxis=dict(tickformat=',', showgrid=True, gridcolor='#f0f0f0'),
                yaxis=dict(showgrid=False)
            )
            bar_fig.update_traces(
                hovertemplate='<b>%{y}</b><br>%{x:,.0f} BTC<extra></extra>'
            )
            
            # === PIE CHART ===
            pie_df = cat_df.sort_values('btc', ascending=False)
            
            pie_fig = px.pie(
                pie_df,
                values='btc',
                names='category',
                hole=0.4,
                color='category',
                color_discrete_map={row['category']: row['color'] for _, row in pie_df.iterrows()}
            )
            pie_fig.update_layout(
                height=380,
                template="plotly_white",
                margin=dict(l=20, r=20, t=10, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
            )
            pie_fig.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>%{value:,.0f} BTC<br>%{percent}<extra></extra>'
            )
            
            # === EVOLUTION DATA (for separate chart callback) ===
            evolution_df = get_historical_evolution_data()
            
            if evolution_df.empty:
                evolution_store_data = None
            else:
                # Convert timestamps to ISO format strings for JSON storage
                evolution_df['timestamp'] = pd.to_datetime(evolution_df['timestamp'])
                evolution_df = evolution_df.sort_values('timestamp')
                evolution_store_data = {
                    'records': evolution_df.to_dict('records'),
                    'dates': evolution_df['timestamp'].dt.strftime('%Y-%m-%d').unique().tolist()
                }
                # Convert timestamp to string for JSON serialization
                for rec in evolution_store_data['records']:
                    if isinstance(rec.get('timestamp'), pd.Timestamp):
                        rec['timestamp'] = rec['timestamp'].isoformat()
            
            # === CATEGORY TABLES ===
            table_data = {}
            tooltip_data = {}
            global_total_btc = sum(s['total_btc'] for s in [get_category_summary(k) for k in CATEGORY_ID_MAPPING.values()])
            
            for layout_id, data_key in CATEGORY_ID_MAPPING.items():
                df = get_category_dataframe(data_key)
                
                if df.empty:
                    table_data[layout_id] = []
                    tooltip_data[layout_id] = []
                else:
                    df = df.copy()
                    df['pct_total'] = (df['btc'] / global_total_btc * 100 / 100) if global_total_btc > 0 else 0
                    
                    # Add proof score data with tooltips (new Bitcoin-maxi scoring)
                    def get_proof_score_for_row(name):
                        score = get_proof_score_for_entity(name)
                        return {
                            'display': format_proof_score_display(score['confidence_score']),
                            'tooltip': create_proof_score_tooltip(
                                score['confidence_score'],
                                score['max_possible'],
                                score['tier'],
                                score['public_addresses'],
                                score['concerns']
                            ),
                            'score_value': score['confidence_score']  # For filtering
                        }
                    
                    proof_info = df['name'].apply(get_proof_score_for_row)
                    df['proof_score'] = proof_info.apply(lambda x: x['display'])
                    df['proof_tooltip'] = proof_info.apply(lambda x: x['tooltip'])
                    df['proof_score_value'] = proof_info.apply(lambda x: x['score_value'])
                    
                    records = df[['rank', 'name', 'country', 'btc', 'value_usd', 'pct_total', 'proof_score', 'proof_score_value', 'proof_tooltip']].to_dict('records')
                    table_data[layout_id] = records
                    
                    # Build tooltip_data in Dash DataTable format
                    tooltip_data[layout_id] = [
                        {
                            'proof_score': {
                                'value': row['proof_tooltip'],
                                'type': 'text'
                            }
                        } for row in records
                    ]
            
            # === STATUS ===
            btc_price_str = f"BTC: ${btc_price:,.0f}"
            last_update = entities_manager.last_update
            if last_update:
                last_update_str = f"Last update: {last_update.strftime('%Y-%m-%d %H:%M')}"
            else:
                last_update_str = "Last update: Unknown"
            
            store_data = {'loaded': True, 'total_btc': total_btc, 'btc_price': btc_price}
            
            return (
                entities_str, entities_sub,
                btc_str, btc_sub,
                value_str, value_sub,
                supply_str, supply_sub,
                bar_fig, pie_fig, evolution_store_data,
                # Table data
                table_data.get('public-co', []),
                table_data.get('etfs', []),
                table_data.get('private-co', []),
                table_data.get('countries', []),
                table_data.get('defi', []),
                table_data.get('mining', []),
                # Tooltip data
                tooltip_data.get('public-co', []),
                tooltip_data.get('etfs', []),
                tooltip_data.get('private-co', []),
                tooltip_data.get('countries', []),
                tooltip_data.get('defi', []),
                tooltip_data.get('mining', []),
                # Status
                btc_price_str, last_update_str, None, store_data
            )
            
        except Exception as e:
            logger.error(f"Error loading treasury data: {e}", exc_info=True)
            empty_fig = create_empty_figure()
            return (
                "--", "", "--", "", "--", "", "--", "",
                empty_fig, empty_fig, empty_fig,
                [], [], [], [], [], [],  # table data
                [], [], [], [], [], [],  # tooltip data
                "", "Last update: Error",
                html.Div(f"Error: {str(e)}", style={'color': '#dc3545'}),
                None
            )
    # =========================================================================
    # EVOLUTION CHART CALLBACK (responds to category toggle + date slider)
    # =========================================================================
    
    @app.callback(
        Output('treasury-evolution-chart', 'figure'),
        [
            Input('evolution-data-store', 'data'),
            Input('evolution-category-toggle', 'value'),
            Input('evolution-date-slider', 'value')
        ],
        prevent_initial_call=False
    )
    def update_evolution_chart(evolution_data, selected_categories, end_date_idx):
        """
        Generate evolution chart based on selected categories and end date.
        Start date is always the beginning of available data.
        """
        # Create empty figure if no data
        if not evolution_data or not evolution_data.get('records'):
            return create_empty_figure("Historical data not available")
        
        if not selected_categories:
            return create_empty_figure("Select at least one category")
        
        # Convert records back to DataFrame
        df = pd.DataFrame(evolution_data['records'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Get unique dates for filtering
        dates = sorted(df['timestamp'].dt.date.unique())
        n_dates = len(dates)
        
        # Apply date filter (start is always 0, only end is adjustable)
        if end_date_idx is not None and n_dates > 0:
            end_idx = max(0, min(end_date_idx, n_dates - 1))
            selected_dates = dates[0:end_idx + 1]
            df = df[df['timestamp'].dt.date.isin(selected_dates)]
        
        # Filter by selected categories
        df = df[df['category'].isin(selected_categories)]
        
        if df.empty:
            return create_empty_figure("No data for selected filters")
        
        # Color map for categories
        color_map = {
            'ETFs': '#007bff',
            'Public Companies': '#28a745',
            'Private Companies': '#17a2b8',
            'Countries': '#ffc107',
            'DeFi': '#6f42c1',
            'Mining Companies': '#fd7e14'
        }
        
        # Create figure
        fig = go.Figure()
        
        for category in selected_categories:
            cat_data = df[df['category'] == category]
            if not cat_data.empty:
                fig.add_trace(go.Scatter(
                    x=cat_data['timestamp'],
                    y=cat_data['btc_holdings'],
                    name=category,
                    mode='lines',
                    line=dict(
                        color=color_map.get(category, '#6c757d'),
                        width=2
                    ),
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                  'Date: %{x|%b %d, %Y}<br>' +
                                  'Holdings: %{y:,.0f} BTC<br>' +
                                  '<extra></extra>'
                ))
        
        # Layout
        fig.update_layout(
            height=400,
            template="plotly_white",
            margin=dict(l=60, r=20, t=20, b=40),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.18,
                xanchor="center",
                x=0.5
            ),
            hovermode='x unified',
            xaxis=dict(
                showgrid=True,
                gridcolor='#f0f0f0',
                title=''
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#f0f0f0',
                tickformat=',',
                title='BTC Holdings'
            ),
            plot_bgcolor='#ffffff',
            paper_bgcolor='#ffffff'
        )
        
        return fig
    
    # =========================================================================
    # DATE SLIDER INITIALIZATION CALLBACK
    # =========================================================================
    
    @app.callback(
        [
            Output('evolution-date-slider', 'min'),
            Output('evolution-date-slider', 'max'),
            Output('evolution-date-slider', 'value'),
            Output('evolution-date-slider', 'marks'),
            Output('evolution-date-display', 'children')
        ],
        [
            Input('evolution-data-store', 'data'),
            Input('evolution-date-slider', 'value')
        ],
        prevent_initial_call=False
    )
    def update_date_slider(evolution_data, current_value):
        """
        Initialize and update the date slider based on available data.
        Slider controls end date only - start is always first available date.
        """
        from dash import callback_context
        
        # Default empty state
        if not evolution_data or not evolution_data.get('dates'):
            return 0, 1, 1, {}, "No data available"
        
        dates = evolution_data['dates']
        n_dates = len(dates)
        
        if n_dates == 0:
            return 0, 1, 1, {}, "No data available"
        
        # Create marks (show ~5-6 evenly spaced dates)
        marks = {}
        step = max(1, n_dates // 5)
        for i in range(0, n_dates, step):
            date_str = dates[i]
            try:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                marks[i] = {'label': dt.strftime('%b %d'), 'style': {'fontSize': '0.75em'}}
            except:
                marks[i] = {'label': date_str[:5], 'style': {'fontSize': '0.75em'}}
        
        # Always add last date
        if n_dates - 1 not in marks:
            try:
                dt = datetime.strptime(dates[-1], '%Y-%m-%d')
                marks[n_dates - 1] = {'label': dt.strftime('%b %d'), 'style': {'fontSize': '0.75em'}}
            except:
                marks[n_dates - 1] = {'label': dates[-1][:5], 'style': {'fontSize': '0.75em'}}
        
        # Determine if this is initialization or slider update
        ctx = callback_context
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
        
        if triggered_id == 'evolution-date-slider' and current_value is not None:
            # Slider was moved, keep current value
            end_idx = max(0, min(current_value, n_dates - 1))
        else:
            # Data store updated, reset to full range (end at last date)
            end_idx = n_dates - 1
        
        # Format display text (start is always first date)
        try:
            start_date = datetime.strptime(dates[0], '%Y-%m-%d').strftime('%B %d, %Y')
            end_date = datetime.strptime(dates[end_idx], '%Y-%m-%d').strftime('%B %d, %Y')
            display_text = f"Showing {start_date} to {end_date}"
        except:
            display_text = f"Showing {dates[0]} to {dates[end_idx]}"
        
        return 0, n_dates - 1, end_idx, marks, display_text
    
    # =========================================================================
    # PROOF CALCULATION PANEL TOGGLE CALLBACK
    # =========================================================================
    
    @app.callback(
        [
            Output('proof-calculation-panel', 'style'),
            Output('proof-calculation-toggle', 'children')
        ],
        Input('proof-calculation-toggle', 'n_clicks'),
        prevent_initial_call=False
    )
    def toggle_proof_calculation_panel(n_clicks):
        """
        Toggle visibility of the Proof Calculation explanation panel.
        """
        if n_clicks is None:
            n_clicks = 0
        
        # Panel is hidden by default, toggle on odd clicks
        is_visible = n_clicks % 2 == 1
        
        if is_visible:
            new_style = {
                'display': 'block',
                'border': '1px solid #dee2e6',
                'borderRadius': '4px',
                'padding': '12px 15px',
                'backgroundColor': '#f8f9fa',
                'marginBottom': '15px'
            }
            new_label = "Hide details"
        else:
            new_style = {
                'display': 'none',
                'border': '1px solid #dee2e6',
                'borderRadius': '4px',
                'padding': '12px 15px',
                'backgroundColor': '#f8f9fa',
                'marginBottom': '15px'
            }
            new_label = "Show details"
        
        return new_style, new_label
    
    logger.info("Treasury/Companies callbacks registered (with proof score system)")
