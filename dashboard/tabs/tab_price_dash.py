"""
Bitcoin Price Dashboard Layout - Academic Style

Features:
- 4 Key Metrics (compact, grey background)
- Period selector
- Statistics & Risk with explanations under each card
"""

from dash import dcc, html

# --- STYLES ---
LABEL_STYLE = {
    'fontSize': '0.65em',
    'fontWeight': '600',
    'color': '#6c757d',
    'textTransform': 'uppercase',
    'letterSpacing': '0.5px',
    'marginBottom': '6px',
    'textAlign': 'center'
}

SUBTEXT_STYLE = {
    'fontSize': '0.7em',
    'color': '#868e96',
    'textAlign': 'center'
}

EXPLANATION_HIDDEN = {'display': 'none'}

def create_stat_card_with_explanation(label, value_id, value_default, subtext, explanation_id, expl_title, expl_text, expl_formula, margin_left='0%', value_color='#212529'):
    """Create a stat card with explanation panel below."""
    return html.Div([
        # Card
        html.Div([
            html.P(label, style=LABEL_STYLE),
            html.H3(id=value_id, children=value_default, style={
                'fontSize': '1.4em', 'fontWeight': 'bold', 'color': value_color,
                'marginBottom': '5px', 'textAlign': 'center'
            }),
            html.P(subtext, style=SUBTEXT_STYLE)
        ], style={
            'padding': '15px',
            'border': '1px solid #dee2e6',
            'backgroundColor': '#ffffff',
            'minHeight': '100px'
        }),
        
        # Explanation (hidden by default)
        html.Div(
            id=explanation_id,
            children=[
                html.H6(expl_title, style={'fontSize': '0.8em', 'fontWeight': 'bold', 'color': '#212529', 'marginBottom': '5px'}),
                html.P(expl_text, style={'fontSize': '0.75em', 'color': '#6c757d', 'marginBottom': '5px', 'lineHeight': '1.4'}),
                html.P(expl_formula, style={'fontSize': '0.7em', 'fontFamily': 'monospace', 'color': '#868e96'})
            ],
            style=EXPLANATION_HIDDEN
        )
    ], style={
        'width': '32%',
        'display': 'inline-block',
        'verticalAlign': 'top',
        'marginLeft': margin_left
    })


# --- LAYOUT ---
layout = html.Div([

    # ===== HEADER =====
    html.H1("Bitcoin Price Dashboard", style={'marginBottom': '20px', 'fontWeight': '600'}),
    html.Hr(),
    
    html.Div(id="error-alert", style={'marginBottom': '15px'}),
    
    # Intervals
    dcc.Interval(id="initial-load", interval=1000, max_intervals=1, n_intervals=0),
    dcc.Interval(id="live-update-interval", interval=60000, n_intervals=0),
    dcc.Store(id="live-price-store"),
    
    # ===== KEY METRICS (COMPACT + GREY BACKGROUND) =====
    html.Div([
        # Current
        html.Div([
            html.P("CURRENT", style=LABEL_STYLE),
            html.H3(id="current-price", children="--", style={
                'fontSize': '1.3em', 'fontWeight': 'bold', 'color': '#212529',
                'marginBottom': '4px', 'textAlign': 'center'
            }),
            html.P(id="price-delta", children="-- vs avg", style={
                'fontSize': '0.7em', 'color': '#6c757d', 'fontWeight': '500', 'textAlign': 'center'
            })
        ], style={'width': '23%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '12px'}),
        
        # Average
        html.Div([
            html.P("AVERAGE", style=LABEL_STYLE),
            html.H4(id="avg-price", children="--", style={
                'fontSize': '1.2em', 'fontWeight': 'bold', 'color': '#212529',
                'marginBottom': '4px', 'textAlign': 'center'
            }),
            html.P(id="avg-period", children="(365d)", style=SUBTEXT_STYLE)
        ], style={'width': '23%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '12px'}),
        
        # Lowest
        html.Div([
            html.P("LOWEST", style=LABEL_STYLE),
            html.H4(id="min-price", children="--", style={
                'fontSize': '1.2em', 'fontWeight': 'bold', 'color': '#212529',
                'marginBottom': '4px', 'textAlign': 'center'
            }),
            html.P(id="min-period", children="(365d)", style=SUBTEXT_STYLE)
        ], style={'width': '23%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '12px'}),
        
        # Highest
        html.Div([
            html.P("HIGHEST", style=LABEL_STYLE),
            html.H4(id="max-price", children="--", style={
                'fontSize': '1.2em', 'fontWeight': 'bold', 'color': '#212529',
                'marginBottom': '4px', 'textAlign': 'center'
            }),
            html.P(id="max-period", children="(365d)", style=SUBTEXT_STYLE)
        ], style={'width': '23%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '12px'}),
    ], style={
        'border': '1px solid #dee2e6',
        'marginBottom': '25px',
        'backgroundColor': '#f8f9fa',
        'display': 'flex',
        'justifyContent': 'space-around'
    }),
    
    # ===== CHART SECTION =====
    html.Div([
        html.Div([
            html.Span("Price Evolution ", style={'fontSize': '1.2em', 'fontWeight': 'bold', 'color': '#212529'}),
            html.Span(id="live-indicator", children="", style={'fontSize': '0.95em', 'fontWeight': 'bold', 'color': '#28a745', 'marginLeft': '10px'}),
            
            html.Button('Refresh Data', id='refresh-btn', n_clicks=0, style={
                'marginLeft': 'auto', 'padding': '8px 16px', 'backgroundColor': '#007bff',
                'color': 'white', 'border': 'none', 'borderRadius': '4px', 'cursor': 'pointer',
                'fontSize': '0.85em', 'fontWeight': '500'
            }),
            html.Button('Full History', id='full-history-btn', n_clicks=0, style={
                'marginLeft': '10px', 'padding': '8px 16px', 'backgroundColor': '#28a745',
                'color': 'white', 'border': 'none', 'borderRadius': '4px', 'cursor': 'pointer',
                'fontSize': '0.85em', 'fontWeight': '500'
            })
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '15px'}),
        
        dcc.Checklist(
            id="ma-checkbox",
            options=[{"label": " Show moving averages (adaptive to timeframe)", "value": "show_ma"}],
            value=[],
            inline=True,
            style={'marginBottom': '15px', 'fontSize': '0.85em'}
        ),
        
        dcc.Loading(id="loading-chart", type="default", children=[dcc.Graph(id="price-chart")])
    ], style={'marginBottom': '25px'}),
    
    # ===== PERIOD SELECTOR =====
    html.Div([
        html.Div([
            html.Span("Period (days) - Displaying: ", style={'fontSize': '0.9em', 'fontWeight': '500', 'color': '#495057'}),
            html.Span(id='slider-info', children='365 days', style={'fontSize': '0.9em', 'fontWeight': 'bold', 'color': '#212529'})
        ], style={'marginBottom': '10px'}),
        
        dcc.Slider(
            id="days-slider", min=7, max=4000, value=365,
            marks={7: '7d', 30: '1m', 90: '3m', 180: '6m', 365: '1y', 730: '2y', 1095: '3y', 1460: '4y', 2920: '8y', 4000: 'All'},
            tooltip={"placement": "bottom", "always_visible": False}
        )
    ], style={'marginBottom': '30px', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'border': '1px solid #dee2e6', 'borderRadius': '4px'}),
    
    # ===== STATISTICS & RISK METRICS =====
    html.Hr(),
    html.Div([
        # Header with toggle
        html.Div([
            html.H3("STATISTICS & RISK METRICS", style={
                'fontSize': '1em', 'fontWeight': 'bold', 'color': '#212529',
                'display': 'inline-block', 'marginRight': '20px',
                'textTransform': 'uppercase', 'letterSpacing': '0.5px'
            }),
            dcc.Checklist(
                id='show-stats-explanations-toggle',
                options=[{'label': ' Show Formulas & Explanations', 'value': 'show'}],
                value=[],
                inline=True,
                style={'fontSize': '0.85em', 'display': 'inline-block'}
            )
        ], style={'marginBottom': '20px'}),
        
        # ROW 1: Period Range, Median, Volatility (with explanations)
        html.Div([
            # Period Range (homogeneous)
            html.Div([
                html.Div([
                    html.P("PERIOD RANGE", style=LABEL_STYLE),
                    html.H3(id="period-days-count", children="365 days", style={
                        'fontSize': '1.4em', 'fontWeight': 'bold', 'color': '#212529',
                        'marginBottom': '5px', 'textAlign': 'center'
                    }),
                    html.P(id="period-date-range", children="-- to --", style=SUBTEXT_STYLE)
                ], style={'padding': '15px', 'border': '1px solid #dee2e6', 'backgroundColor': '#ffffff', 'minHeight': '100px'}),
                
                html.Div(id='period-range-explanation', children=[
                    html.H6("Period Range", style={'fontSize': '0.8em', 'fontWeight': 'bold', 'color': '#212529', 'marginBottom': '5px'}),
                    html.P("Time window for all displayed metrics.", style={'fontSize': '0.75em', 'color': '#6c757d', 'marginBottom': '5px'}),
                    html.P("Start = Today - Period | End = Today", style={'fontSize': '0.7em', 'fontFamily': 'monospace', 'color': '#868e96'})
                ], style=EXPLANATION_HIDDEN)
            ], style={'width': '32%', 'display': 'inline-block', 'verticalAlign': 'top'}),
            
            # Median Price
            html.Div([
                html.Div([
                    html.P("MEDIAN PRICE", style=LABEL_STYLE),
                    html.H3(id="median-price", children="--", style={
                        'fontSize': '1.4em', 'fontWeight': 'bold', 'color': '#212529',
                        'marginBottom': '5px', 'textAlign': 'center'
                    }),
                    html.P("(period)", style=SUBTEXT_STYLE)
                ], style={'padding': '15px', 'border': '1px solid #dee2e6', 'backgroundColor': '#ffffff', 'minHeight': '100px'}),
                
                html.Div(id='median-price-explanation', children=[
                    html.H6("Median Price", style={'fontSize': '0.8em', 'fontWeight': 'bold', 'color': '#212929', 'marginBottom': '5px'}),
                    html.P("Middle value, less affected by outliers than average.", style={'fontSize': '0.75em', 'color': '#6c757d', 'marginBottom': '5px'}),
                    html.P("Median = 50th percentile of sorted prices", style={'fontSize': '0.7em', 'fontFamily': 'monospace', 'color': '#868e96'})
                ], style=EXPLANATION_HIDDEN)
            ], style={'width': '32%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '2%'}),
            
            # Volatility
            html.Div([
                html.Div([
                    html.P("VOLATILITY (ANN.)", style=LABEL_STYLE),
                    html.H3(id="volatility", children="--", style={
                        'fontSize': '1.4em', 'fontWeight': 'bold', 'color': '#212529',
                        'marginBottom': '5px', 'textAlign': 'center'
                    }),
                    html.P("(annualized)", style=SUBTEXT_STYLE)
                ], style={'padding': '15px', 'border': '1px solid #dee2e6', 'backgroundColor': '#ffffff', 'minHeight': '100px'}),
                
                html.Div(id='volatility-explanation', children=[
                    html.H6("Volatility (Annualized)", style={'fontSize': '0.8em', 'fontWeight': 'bold', 'color': '#212529', 'marginBottom': '5px'}),
                    html.P("Price fluctuation intensity, annualized for comparability.", style={'fontSize': '0.75em', 'color': '#6c757d', 'marginBottom': '5px'}),
                    html.P("Vol = StdDev x sqrt(365 / Period)", style={'fontSize': '0.7em', 'fontFamily': 'monospace', 'color': '#868e96'})
                ], style=EXPLANATION_HIDDEN)
            ], style={'width': '32%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '2%'})
        ], style={'marginBottom': '15px'}),
        
        # ROW 2: Std Dev, Max Drawdown, Sharpe Ratio (with explanations)
        html.Div([
            # Standard Deviation
            html.Div([
                html.Div([
                    html.P("STANDARD DEVIATION", style=LABEL_STYLE),
                    html.H3(id="std-dev", children="--", style={
                        'fontSize': '1.4em', 'fontWeight': 'bold', 'color': '#212529',
                        'marginBottom': '5px', 'textAlign': 'center'
                    }),
                    html.P("(period)", style=SUBTEXT_STYLE)
                ], style={'padding': '15px', 'border': '1px solid #dee2e6', 'backgroundColor': '#ffffff', 'minHeight': '100px'}),
                
                html.Div(id='std-dev-explanation', children=[
                    html.H6("Standard Deviation", style={'fontSize': '0.8em', 'fontWeight': 'bold', 'color': '#212529', 'marginBottom': '5px'}),
                    html.P("Average distance of prices from the mean.", style={'fontSize': '0.75em', 'color': '#6c757d', 'marginBottom': '5px'}),
                    html.P("s = sqrt(sum((x - mean)^2) / N)", style={'fontSize': '0.7em', 'fontFamily': 'monospace', 'color': '#868e96'})
                ], style=EXPLANATION_HIDDEN)
            ], style={'width': '32%', 'display': 'inline-block', 'verticalAlign': 'top'}),
            
            # Max Drawdown
            html.Div([
                html.Div([
                    html.P("MAX DRAWDOWN", style=LABEL_STYLE),
                    html.H3(id="max-drawdown", children="--", style={
                        'fontSize': '1.4em', 'fontWeight': 'bold', 'color': '#dc3545',
                        'marginBottom': '5px', 'textAlign': 'center'
                    }),
                    html.P("(from ATH)", style=SUBTEXT_STYLE)
                ], style={'padding': '15px', 'border': '1px solid #dee2e6', 'backgroundColor': '#ffffff', 'minHeight': '100px'}),
                
                html.Div(id='max-drawdown-explanation', children=[
                    html.H6("Max Drawdown", style={'fontSize': '0.8em', 'fontWeight': 'bold', 'color': '#212529', 'marginBottom': '5px'}),
                    html.P("Largest peak-to-trough decline, measures downside risk.", style={'fontSize': '0.75em', 'color': '#6c757d', 'marginBottom': '5px'}),
                    html.P("DD = (Peak - Current) / Peak x 100", style={'fontSize': '0.7em', 'fontFamily': 'monospace', 'color': '#868e96'})
                ], style=EXPLANATION_HIDDEN)
            ], style={'width': '32%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '2%'}),
            
            # Sharpe Ratio
            html.Div([
                html.Div([
                    html.P("SHARPE RATIO", style=LABEL_STYLE),
                    html.H3(id="sharpe-ratio", children="--", style={
                        'fontSize': '1.4em', 'fontWeight': 'bold', 'color': '#212529',
                        'marginBottom': '5px', 'textAlign': 'center'
                    }),
                    html.P("(risk-adjusted)", style=SUBTEXT_STYLE)
                ], style={'padding': '15px', 'border': '1px solid #dee2e6', 'backgroundColor': '#ffffff', 'minHeight': '100px'}),
                
                html.Div(id='sharpe-ratio-explanation', children=[
                    html.H6("Sharpe Ratio", style={'fontSize': '0.8em', 'fontWeight': 'bold', 'color': '#212529', 'marginBottom': '5px'}),
                    html.P("Risk-adjusted return. Higher is better (>1 is good).", style={'fontSize': '0.75em', 'color': '#6c757d', 'marginBottom': '5px'}),
                    html.P("Sharpe = (Return - Rf) / Volatility", style={'fontSize': '0.7em', 'fontFamily': 'monospace', 'color': '#868e96'})
                ], style=EXPLANATION_HIDDEN)
            ], style={'width': '32%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '2%'})
        ], style={'marginBottom': '20px'}),
        
    ], style={'marginBottom': '30px'}),
    
    # ===== HIDDEN ELEMENTS =====
    html.Div(id="refresh-status", style={'display': 'none'}),
    html.Div(id="data-table-container", style={'display': 'none'}),
    dcc.Download(id="download-dataframe"),
    html.Button(id="download-btn", style={'display': 'none'}),
    dcc.Checklist(id="show-data-checkbox", options=[], value=[], style={'display': 'none'}),
    html.Div(id="stats-period", style={'display': 'none'}),
    html.Div(id="stats-price", style={'display': 'none'}),
    html.Div(id="stats-volatility", style={'display': 'none'}),
    html.Div(id="stats-explanations-panel", style={'display': 'none'}),
])
