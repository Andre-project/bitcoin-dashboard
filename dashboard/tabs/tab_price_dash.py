from dash import dcc, html, Input, Output, callback, dash_table
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from data_collectors.price_data import get_bitcoin_price_series, download_full_bitcoin_history, load_local_history
from dash.exceptions import PreventUpdate

# --- LAYOUT ---
layout = html.Div([
    # Header
    html.H1("₿ Bitcoin Price Dashboard", style={'marginBottom': '20px'}),
    html.Hr(),
    
    # Error alert
    html.Div(id="error-alert", style={'marginBottom': '15px'}),
    
    # Initial load trigger
    dcc.Interval(id="initial-load", interval=1000, max_intervals=1, n_intervals=0),
    
    # Live price update interval (every 60 seconds)
    dcc.Interval(id="live-update-interval", interval=60*1000, n_intervals=0),
    
    # Store for live price data
    dcc.Store(id="live-price-store"),
    
    # All metrics in one compact row
    html.Div([
        # Row 1: Key Metrics
        html.Div([
            html.P("Current", style={'fontSize': '0.75em', 'marginBottom': '5px', 'fontWeight': 'bold', 'color': '#6c757d'}),
            html.H4(id="current-price", style={'fontSize': '1em', 'marginBottom': '3px'}),
            html.P(id="price-delta", style={'fontSize': '0.7em', 'marginBottom': '0px'})
        ], style={'width': '12%', 'display': 'inline-block', 'padding': '12px', 'verticalAlign': 'top'}),
        html.Div([
            html.P("Average", style={'fontSize': '0.75em', 'marginBottom': '5px', 'fontWeight': 'bold', 'color': '#6c757d'}),
            html.H4(id="avg-price", style={'fontSize': '1em', 'marginBottom': '3px'}),
            html.P(id="avg-period", style={'fontSize': '0.7em', 'marginBottom': '0px'})
        ], style={'width': '12%', 'display': 'inline-block', 'padding': '12px', 'verticalAlign': 'top'}),
        html.Div([
            html.P("Lowest", style={'fontSize': '0.75em', 'marginBottom': '5px', 'fontWeight': 'bold', 'color': '#6c757d'}),
            html.H4(id="min-price", style={'fontSize': '1em', 'marginBottom': '3px'}),
            html.P(id="min-period", style={'fontSize': '0.7em', 'marginBottom': '0px'})
        ], style={'width': '12%', 'display': 'inline-block', 'padding': '12px', 'verticalAlign': 'top'}),
        html.Div([
            html.P("Highest", style={'fontSize': '0.75em', 'marginBottom': '5px', 'fontWeight': 'bold', 'color': '#6c757d'}),
            html.H4(id="max-price", style={'fontSize': '1em', 'marginBottom': '3px'}),
            html.P(id="max-period", style={'fontSize': '0.7em', 'marginBottom': '0px'})
        ], style={'width': '12%', 'display': 'inline-block', 'padding': '12px', 'verticalAlign': 'top'}),
        
        # Row 2: Period
        html.Div([
            html.P("📅 Period", style={'fontSize': '0.75em', 'marginBottom': '5px', 'fontWeight': 'bold', 'color': '#6c757d'}),
            html.Div(id="stats-period", style={'fontSize': '0.7em'})
        ], style={'width': '15%', 'display': 'inline-block', 'padding': '12px', 'verticalAlign': 'top'}),
        
        # Row 3: Price Statistics
        html.Div([
            html.P("📊 Statistics", style={'fontSize': '0.75em', 'marginBottom': '5px', 'fontWeight': 'bold', 'color': '#6c757d'}),
            html.Div(id="stats-price", style={'fontSize': '0.7em'})
        ], style={'width': '18%', 'display': 'inline-block', 'padding': '12px', 'verticalAlign': 'top'}),
        
        # Row 4: Volatility & Risk
        html.Div([
            html.P("⚡ Risk", style={'fontSize': '0.75em', 'marginBottom': '5px', 'fontWeight': 'bold', 'color': '#6c757d'}),
            html.Div(id="stats-volatility", style={'fontSize': '0.7em'})
        ], style={'width': '18%', 'display': 'inline-block', 'padding': '12px', 'verticalAlign': 'top'}),
    ], style={'marginBottom': '20px', 'display': 'flex', 'justifyContent': 'space-between', 'border': '1px solid #dee2e6', 'padding': '5px'}),
    
    # Chart section
    html.Hr(),
    html.Div([
        html.H4("Price Evolution", style={'marginBottom': '15px', 'display': 'inline-block'}),
        html.Span(id="live-indicator", style={'marginLeft': '15px', 'color': '#28a745', 'fontSize': '0.9em', 'fontWeight': 'bold'}),
    ], style={'display': 'flex', 'alignItems': 'center'}),
    dcc.Checklist(
        id="ma-checkbox",
        options=[{"label": " Show moving averages (adaptive to timeframe)", "value": "show_ma"}],
        value=[],
        inline=True,
        style={'marginBottom': '15px'}
    ),
    dcc.Loading(
        id="loading-chart",
        type="default",
        children=[dcc.Graph(id="price-chart", style={'marginBottom': '20px'})]
    ),
    
    # Period slider - right under the graph
    html.Div([
        html.Label("Period (days)", style={'marginBottom': '10px', 'fontSize': '0.875em', 'fontWeight': 'bold', 'display': 'block'}),
        dcc.Slider(
            id="days-slider",
            min=7,
            max=4000,
            value=365,
            marks={7: '7d', 30: '1m', 90: '3m', 180: '6m', 365: '1y', 730: '2y', 1095: '3y', 1460: '4y', 2920: '8y', 4000: 'All'},
            tooltip={"placement": "bottom", "always_visible": True},
            className="slider"
        ),
        html.Div(id="slider-info", style={'color': '#6c757d', 'fontSize': '0.875em', 'marginTop': '10px'}),
    ], style={'marginBottom': '30px', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'border': '1px solid #dee2e6'}),
    
    # Export section
    html.Hr(),
    html.H5("Export Data", style={'marginBottom': '10px'}),
    html.P("Download the current dataset as a CSV file or refresh data from the API.", 
           style={'color': '#6c757d', 'fontSize': '0.875em', 'marginBottom': '15px'}),
    html.Div([
        html.Button(
            "Refresh Data",
            id="refresh-btn",
            className="button",
            style={'padding': '10px 20px', 'backgroundColor': '#007bff', 'color': 'white', 'border': 'none', 'cursor': 'pointer', 'fontFamily': 'Courier New, monospace'}
        ),
        html.Button(
            "Full History (2010+)",
            id="full-history-btn",
            className="button",
            style={'padding': '10px 20px', 'backgroundColor': '#28a745', 'color': 'white', 'border': 'none', 'cursor': 'pointer', 'fontFamily': 'Courier New, monospace'}
        ),
        html.Button(
            "Download CSV",
            id="download-btn",
            style={'padding': '10px 20px', 'backgroundColor': '#6c757d', 'color': 'white', 'border': 'none', 'cursor': 'pointer', 'fontFamily': 'Courier New, monospace'}
        ),
    ], style={'display': 'flex', 'gap': '10px', 'marginBottom': '15px'}),
    html.Div(id="refresh-status", style={'marginBottom': '10px'}),
    dcc.Download(id="download-dataframe"),
])
