"""Callbacks pour l'onglet Price Dashboard"""
from dash import Input, Output, dcc, html, dash_table
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from data_collectors.price_data_v2 import get_bitcoin_price_series, download_full_bitcoin_history, load_local_history, fetch_live_binance_data


def register_callbacks(app):
    """Enregistre tous les callbacks pour l'onglet Price"""
    
    # Callback for live price updates
    @app.callback(
        [Output('live-price-store', 'data'),
         Output('live-indicator', 'children')],
        [Input('live-update-interval', 'n_intervals'),
         Input('initial-load', 'n_intervals')]
    )
    def update_live_price(live_intervals, initial_intervals):
        """Fetch live price from Binance every 60 seconds"""
        try:
            live_df = fetch_live_binance_data(limit=60)
            
            if live_df is not None and not live_df.empty:
                latest_price = live_df['price'].iloc[-1]
                latest_time = live_df['timestamp'].iloc[-1]
                
                return (
                    {'price': latest_price, 'time': latest_time.isoformat()},
                    f"🔴 LIVE: ${latest_price:,.2f}"
                )
            else:
                return None, ""
        except Exception as e:
            print(f"❌ Live price update error: {e}")
            return None, ""
    
    # Callback principal : graphique + métriques
    @app.callback(
        [Output('price-chart', 'figure'),
         Output('current-price', 'children'),
         Output('price-delta', 'children'),
         Output('avg-price', 'children'),
         Output('avg-period', 'children'),
         Output('min-price', 'children'),
         Output('min-period', 'children'),
         Output('max-price', 'children'),
         Output('max-period', 'children'),
         Output('slider-info', 'children'),
         Output('error-alert', 'children')],
        [Input('refresh-btn', 'n_clicks'),
         Input('full-history-btn', 'n_clicks'),
         Input('days-slider', 'value'),
         Input('ma-checkbox', 'value'),
         Input('initial-load', 'n_intervals'),
         Input('live-update-interval', 'n_intervals'),
         Input('live-price-store', 'data')]
    )
    def update_dashboard(refresh_clicks, full_history_clicks, days, show_ma, n_intervals, live_intervals, live_data):
        """Single callback to update everything with live price integration"""
        print(f"🔍 Dashboard update: refresh={refresh_clicks}, full_history={full_history_clicks}, days={days}, live={live_intervals}")
        
        try:
            # 1. Load data
            if full_history_clicks and full_history_clicks > 0:
                print("📥 Downloading full history from CryptoDataDownload/Yahoo...")
                df = download_full_bitcoin_history()
                if df is None or df.empty:
                    print("❌ Full history download failed")
                    return ({}, "N/A", "", "N/A", "", "N/A", "", "N/A", "", "No data", 
                           html.Div("⚠️ Error downloading full history", style={'color': 'red', 'padding': '10px', 'backgroundColor': '#f8d7da'}))
            elif refresh_clicks and refresh_clicks > 0:
                print("🔄 Refreshing data with live updates...")
                df = get_bitcoin_price_series(include_live=True)
                if df is None or df.empty:
                    print("❌ Data refresh failed")
                    return ({}, "N/A", "", "N/A", "", "N/A", "", "N/A", "", "No data", 
                           html.Div("⚠️ Error loading data", style={'color': 'red', 'padding': '10px', 'backgroundColor': '#f8d7da'}))
            else:
                print("📂 Loading from local cache with live update...")
                df = load_local_history()
                
                # Update with live price if available
                if live_data and df is not None and not df.empty:
                    today = pd.Timestamp.now().normalize()
                    if today in df['date'].values:
                        df.loc[df['date'] == today, 'price'] = live_data['price']
                        print(f"🔴 Updated with live price: ${live_data['price']:,.2f}")
                    else:
                        new_row = pd.DataFrame({'date': [today], 'price': [live_data['price']]})
                        df = pd.concat([df, new_row], ignore_index=True)
                        df = df.sort_values('date')
                        print(f"🔴 Added today with live price: ${live_data['price']:,.2f}")
                
                if df is None or df.empty:
                    print("⚠️ No cache, fetching with live updates...")
                    df = get_bitcoin_price_series(include_live=True)
                    if df is None or df.empty:
                        print("❌ Failed to load any data")
                        return ({}, "N/A", "", "N/A", "", "N/A", "", "N/A", "", "No data",
                               html.Div("⚠️ No data available. Click Refresh or Full History.", style={'color': 'red', 'padding': '10px', 'backgroundColor': '#f8d7da'}))
            
            print(f"✅ Loaded {len(df)} records")
            
            # 2. Filter by days
            df_filtered = df.tail(days).copy()
            actual_days = len(df_filtered)
            print(f"📊 Filtered to {actual_days} days")
            
            # 3. Calculate metrics
            current_price = df_filtered['price'].iloc[-1]
            avg_price = df_filtered['price'].mean()
            variation = ((current_price - avg_price) / avg_price) * 100
            min_price = df_filtered['price'].min()
            max_price = df_filtered['price'].max()
            
            # 4. Create chart
            df_filtered['date_str'] = df_filtered['date'].astype(str)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_filtered['date_str'],
                y=df_filtered['price'],
                mode='lines',
                name='Bitcoin Price',
                line=dict(color="#020C0D", width=2)
            ))
            
            # Add moving averages if checked
            if 'show_ma' in show_ma:
                # Calculate different MAs based on timeframe
                if actual_days <= 30:
                    # Short timeframe: 7 and 14 days
                    df_filtered['MA7'] = df_filtered['price'].rolling(window=7, min_periods=1).mean()
                    df_filtered['MA14'] = df_filtered['price'].rolling(window=14, min_periods=1).mean()
                    
                    fig.add_trace(go.Scatter(
                        x=df_filtered['date_str'], y=df_filtered['MA7'],
                        mode='lines', name='MA 7 days',
                        line=dict(color='#FFA500', width=2, dash='dash')
                    ))
                    fig.add_trace(go.Scatter(
                        x=df_filtered['date_str'], y=df_filtered['MA14'],
                        mode='lines', name='MA 14 days',
                        line=dict(color='#00FF00', width=2, dash='dot')
                    ))
                elif actual_days <= 90:
                    # Medium timeframe: 7, 30 days
                    df_filtered['MA7'] = df_filtered['price'].rolling(window=7, min_periods=1).mean()
                    df_filtered['MA30'] = df_filtered['price'].rolling(window=30, min_periods=1).mean()
                    
                    fig.add_trace(go.Scatter(
                        x=df_filtered['date_str'], y=df_filtered['MA7'],
                        mode='lines', name='MA 7 days',
                        line=dict(color='#FFA500', width=2, dash='dash')
                    ))
                    fig.add_trace(go.Scatter(
                        x=df_filtered['date_str'], y=df_filtered['MA30'],
                        mode='lines', name='MA 30 days',
                        line=dict(color='#00FF00', width=2, dash='dot')
                    ))
                elif actual_days <= 180:
                    # Long timeframe: 30, 50, 100 days
                    df_filtered['MA30'] = df_filtered['price'].rolling(window=30, min_periods=1).mean()
                    df_filtered['MA50'] = df_filtered['price'].rolling(window=50, min_periods=1).mean()
                    df_filtered['MA100'] = df_filtered['price'].rolling(window=100, min_periods=1).mean()
                    
                    fig.add_trace(go.Scatter(
                        x=df_filtered['date_str'], y=df_filtered['MA30'],
                        mode='lines', name='MA 30 days',
                        line=dict(color='#FFA500', width=2, dash='dash')
                    ))
                    fig.add_trace(go.Scatter(
                        x=df_filtered['date_str'], y=df_filtered['MA50'],
                        mode='lines', name='MA 50 days',
                        line=dict(color='#00FF00', width=2, dash='dot')
                    ))
                    fig.add_trace(go.Scatter(
                        x=df_filtered['date_str'], y=df_filtered['MA100'],
                        mode='lines', name='MA 100 days',
                        line=dict(color='#0066CC', width=2, dash='dashdot')
                    ))
                else:
                    # Long timeframe (180-365 days): 50, 100, 200 days
                    df_filtered['MA50'] = df_filtered['price'].rolling(window=50, min_periods=1).mean()
                    df_filtered['MA100'] = df_filtered['price'].rolling(window=100, min_periods=1).mean()
                    df_filtered['MA200'] = df_filtered['price'].rolling(window=200, min_periods=1).mean()
                    
                    fig.add_trace(go.Scatter(
                        x=df_filtered['date_str'], y=df_filtered['MA50'],
                        mode='lines', name='MA 50 days',
                        line=dict(color='#FFA500', width=2, dash='dash')
                    ))
                    fig.add_trace(go.Scatter(
                        x=df_filtered['date_str'], y=df_filtered['MA100'],
                        mode='lines', name='MA 100 days',
                        line=dict(color='#00FF00', width=2, dash='dot')
                    ))
                    fig.add_trace(go.Scatter(
                        x=df_filtered['date_str'], y=df_filtered['MA200'],
                        mode='lines', name='MA 200 days',
                        line=dict(color='#0066CC', width=2, dash='dashdot')
                    ))
            
            fig.update_layout(
                title=f'Bitcoin Price ({actual_days} days)',
                xaxis_title="Date",
                yaxis_title="Price (USD)",
                template='plotly_white',
                hovermode='x unified',
                height=400,
                showlegend=True,
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
                margin=dict(l=0, r=0, t=40, b=0)
            )
            
            print("✅ Dashboard updated successfully")
            
            return (
                fig,
                f"${current_price:,.2f}",
                f"{variation:+.2f}% vs average",
                f"${avg_price:,.2f}",
                f"({actual_days}d)",
                f"${min_price:,.2f}",
                f"({actual_days}d)",
                f"${max_price:,.2f}",
                f"({actual_days}d)",
                f"📊 Displaying: {actual_days} days",
                html.Div()
            )
            
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            return ({}, "N/A", "", "N/A", "", "N/A", "", "N/A", "", "Error",
                   html.Div(f"⚠️ Error: {str(e)}", style={'color': 'red', 'padding': '10px', 'backgroundColor': '#f8d7da'}))

    # Callback table
    @app.callback(
        Output('data-table-container', 'children'),
        [Input('refresh-btn', 'n_clicks'),
         Input('full-history-btn', 'n_clicks'),
         Input('days-slider', 'value'),
         Input('show-data-checkbox', 'value'),
         Input('initial-load', 'n_intervals')]
    )
    def update_table(refresh_clicks, full_history_clicks, days, show_data, n_intervals):
        if 'show_data' not in show_data:
            return html.Div()
        
        df = load_local_history()
        if df is None or df.empty:
            return html.Div("No data available")
        
        df_display = df.tail(days).copy()
        df_display['date_str'] = df_display['date'].dt.strftime('%Y-%m-%d')
        df_display = df_display.sort_values('date', ascending=False)
        
        return dash_table.DataTable(
            data=df_display[['date_str', 'price']].rename(columns={'date_str': 'date'}).to_dict('records'),
            columns=[{"name": "Date", "id": "date"}, {"name": "Price (USD)", "id": "price"}],
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '5px'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
            page_size=10
        )

    # Callback statistiques
    @app.callback(
        [Output('stats-period', 'children'),
         Output('stats-price', 'children'),
         Output('stats-volatility', 'children')],
        [Input('refresh-btn', 'n_clicks'),
         Input('full-history-btn', 'n_clicks'),
         Input('days-slider', 'value'),
         Input('initial-load', 'n_intervals'),
         Input('live-update-interval', 'n_intervals')]
    )
    def update_statistics(refresh_clicks, full_history_clicks, days, n_intervals, live_intervals):
        df = load_local_history()
        if df is None or df.empty:
            return "No data", "No data", "No data"
        
        df_stats = df.tail(days).copy()
        
        # Period Info - compact
        period_info = html.Div([
            html.P(df_stats['date'].iloc[0].strftime('%Y-%m-%d'), style={'marginBottom': '3px'}),
            html.P(df_stats['date'].iloc[-1].strftime('%Y-%m-%d'), style={'marginBottom': '3px'}),
            html.P(f"{len(df_stats)} days", style={'marginBottom': '0px', 'fontWeight': 'bold'})
        ])
        
        # Price Statistics - compact
        std_dev = df_stats['price'].std()
        median = df_stats['price'].median()
        range_price = df_stats['price'].max() - df_stats['price'].min()
        
        price_info = html.Div([
            html.P(f"Median: ${median:,.0f}", style={'marginBottom': '3px'}),
            html.P(f"Std Dev: ${std_dev:,.0f}", style={'marginBottom': '3px'}),
            html.P(f"Range: ${range_price:,.0f}", style={'marginBottom': '0px'})
        ])
        
        # Volatility & Risk - compact
        volatility = (std_dev / df_stats['price'].mean() * 100)
        daily_returns = df_stats['price'].pct_change().dropna()
        sharpe_approx = (daily_returns.mean() / daily_returns.std() * (252 ** 0.5)) if daily_returns.std() > 0 else 0
        max_drawdown = ((df_stats['price'].cummax() - df_stats['price']) / df_stats['price'].cummax() * 100).max()
        
        volatility_info = html.Div([
            html.P(f"Vol: {volatility:.1f}%", style={'marginBottom': '3px'}),
            html.P(f"Drawdown: {max_drawdown:.1f}%", style={'marginBottom': '3px'}),
            html.P(f"Sharpe: {sharpe_approx:.2f}", style={'marginBottom': '0px'})
        ])
        
        return period_info, price_info, volatility_info

    # Callback download
    @app.callback(
        Output('download-dataframe', 'data'),
        Input('download-btn', 'n_clicks'),
        prevent_initial_call=True
    )
    def download_csv(n_clicks):
        if not n_clicks:
            raise PreventUpdate
        
        df = load_local_history()
        if df is None:
            raise PreventUpdate
        
        df_export = df.copy()
        df_export['date'] = df_export['date'].dt.strftime('%Y-%m-%d')
        filename = f"bitcoin_price_{len(df_export)}d_{datetime.now().strftime('%Y%m%d')}.csv"
        
        return dcc.send_data_frame(df_export.to_csv, filename, index=False)

    # Callback refresh status
    @app.callback(
        Output('refresh-status', 'children'),
        Input('refresh-btn', 'n_clicks'),
        prevent_initial_call=True
    )
    def refresh_status(n_clicks):
        if not n_clicks:
            raise PreventUpdate
        
        return html.Div("Refreshing...", style={'color': 'blue', 'padding': '10px'})
    
    print("✅ Callbacks Price Dashboard enregistrés")
