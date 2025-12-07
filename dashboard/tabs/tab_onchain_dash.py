"""
On-Chain Metrics Dashboard Layout - Academic Style

Displays 6 Bitcoin blockchain metrics with:
- Rigorous statistical comparisons
- Explanation panels UNDER each chart (toggle-based)
- Single-line Summary section with inline methodology
- Footer with last update timestamp
"""

from dash import html, dcc

# --- STYLES ---
LABEL_STYLE = {
    'fontSize': '0.7em',
    'fontWeight': '600',
    'color': '#6c757d',
    'textTransform': 'uppercase',
    'letterSpacing': '0.5px',
    'marginBottom': '8px',
    'marginTop': '0px'
}

VALUE_STYLE = {
    'fontSize': '1.4em',
    'fontWeight': 'bold',
    'color': '#212529',
    'marginBottom': '5px',
    'marginTop': '0px'
}

DELTA_STYLE = {
    'fontSize': '0.75em',
    'fontWeight': '500',
    'marginBottom': '3px',
    'marginTop': '0px'
}

CONTEXT_STYLE = {
    'fontSize': '0.65em',
    'color': '#868e96',
    'marginBottom': '0px',
    'marginTop': '0px'
}

CARD_STYLE = {
    'width': '32%',
    'display': 'inline-block',
    'padding': '16px',
    'verticalAlign': 'top',
    'boxSizing': 'border-box',
    'border': '1px solid #dee2e6',
    'backgroundColor': '#ffffff'
}

CHART_LEFT_STYLE = {
    'width': '48%',
    'display': 'inline-block',
    'verticalAlign': 'top'
}

CHART_RIGHT_STYLE = {
    'width': '48%',
    'display': 'inline-block',
    'verticalAlign': 'top',
    'marginLeft': '4%'
}

SECTION_TITLE_STYLE = {
    'marginBottom': '20px',
    'fontWeight': '600',
    'color': '#495057',
    'textTransform': 'uppercase',
    'letterSpacing': '0.5px'
}

EXPLANATION_HIDDEN_STYLE = {'display': 'none'}

EXPL_TITLE_STYLE = {
    'fontSize': '0.75em',
    'fontWeight': 'bold',
    'color': '#495057',
    'textTransform': 'uppercase',
    'letterSpacing': '0.3px',
    'marginBottom': '5px',
    'marginTop': '12px'
}

EXPL_TITLE_FIRST_STYLE = {
    'fontSize': '0.75em',
    'fontWeight': 'bold',
    'color': '#495057',
    'textTransform': 'uppercase',
    'letterSpacing': '0.3px',
    'marginBottom': '5px',
    'marginTop': '0px'
}

EXPL_TEXT_STYLE = {
    'fontSize': '0.72em',
    'color': '#6c757d',
    'lineHeight': '1.4',
    'marginBottom': '8px',
    'marginTop': '0px'
}

EXPL_FORMULA_STYLE = {
    'fontSize': '0.68em',
    'color': '#868e96',
    'fontFamily': 'Courier New, monospace',
    'lineHeight': '1.6',
    'marginBottom': '8px',
    'marginTop': '0px'
}

EXPL_LIST_STYLE = {
    'fontSize': '0.72em',
    'color': '#6c757d',
    'paddingLeft': '20px',
    'marginBottom': '0px',
    'marginTop': '0px'
}

# --- EXPLANATION CONTENT ---
EXPLANATIONS = {
    'active_addr': {
        'what': "Number of unique Bitcoin addresses that performed at least one transaction in the last 24 hours.",
        'why': "Proxy for network adoption. Higher values suggest growing ecosystem activity.",
        'calc': ["Delta: (Current - MA30) / MA30 x 100", "MA30: 30-day simple moving average", "Range: min/max over last 30 days"],
        'interp': ["Above +20% vs MA30: Strong growth", "Within +/-10%: Normal activity", "Below -20% vs MA30: Declining"]
    },
    'tx_count': {
        'what': "Total number of confirmed Bitcoin transactions in the last 24 hours.",
        'why': "Direct measure of blockchain utility and economic activity.",
        'calc': ["Delta: (Current - MA50) / MA50 x 100", "MA50: 50-day simple moving average", "StdDev: Z-score from mean"],
        'interp': ["Above +15% vs MA50: High utilization", "Within +/-10%: Baseline", "Below -15% vs MA50: Reduced usage"]
    },
    'hash_rate': {
        'what': "Computational power dedicated to mining, measured in Exahashes per second (EH/s).",
        'why': "Primary indicator of network security. Higher = more expensive to attack.",
        'calc': ["Delta: (Current - ATH) / ATH x 100", "ATH: All-Time High recorded", "% from Peak: Distance from max"],
        'interp': ["Within 5% of ATH: Maximum security", "10-20% below: Moderate", "Above 30% below: Miner stress"]
    },
    'difficulty': {
        'what': "Target difficulty for miners. Adjusts every ~2 weeks to maintain 10-min blocks.",
        'why': "Rising = more miners joining (bullish). Falling = miner exits (bearish).",
        'calc': ["Adjustment: % change at last epoch", "YTD: Year-to-date cumulative", "Next Est: Based on block time"],
        'interp': ["Positive: Hashrate increasing", "Negative: Hashrate decreasing", "Large (>10%): Major shift"]
    },
    'nvt': {
        'what': "Network Value to Transactions ratio. Market cap / daily TX volume (USD).",
        'why': "Valuation metric. High = overvalued, Low = undervalued.",
        'calc': ["NVT = Market Cap / TX Volume", "Delta: vs historical median", "Z-Score: Standard deviations"],
        'interp': ["NVT < 55: Undervalued", "55-75: Fair value", "NVT > 75: Overheated"]
    },
    'miners_rev': {
        'what': "Total USD earned by miners: block rewards + transaction fees.",
        'why': "Indicates mining profitability. Low revenue may cause miner capitulation.",
        'calc': ["Revenue = Rewards + Fees (USD)", "Delta: vs 90d moving average", "YoY: Year-over-year change"],
        'interp': ["Above +30% vs MA90: Highly profitable", "Within +/-20%: Baseline", "Below -30%: Stress"]
    }
}


def create_explanation_panel(metric_key, panel_id):
    """Create explanation panel (placed under chart)."""
    exp = EXPLANATIONS[metric_key]
    return html.Div(
        id=panel_id,
        children=[
            html.H5("WHAT IT MEASURES", style=EXPL_TITLE_FIRST_STYLE),
            html.P(exp['what'], style=EXPL_TEXT_STYLE),
            html.H5("WHY IT MATTERS", style=EXPL_TITLE_STYLE),
            html.P(exp['why'], style=EXPL_TEXT_STYLE),
            html.H5("CALCULATION", style=EXPL_TITLE_STYLE),
            html.P([exp['calc'][0], html.Br(), exp['calc'][1], html.Br(), exp['calc'][2]], style=EXPL_FORMULA_STYLE),
            html.H5("INTERPRETATION", style=EXPL_TITLE_STYLE),
            html.Ul([html.Li(exp['interp'][0]), html.Li(exp['interp'][1]), html.Li(exp['interp'][2])], style=EXPL_LIST_STYLE)
        ],
        style=EXPLANATION_HIDDEN_STYLE
    )


# --- LAYOUT ---
layout = html.Div([

    # ===== HEADER =====
    html.H1("On-Chain Metrics", style={'marginBottom': '15px', 'fontWeight': '600'}),
    
    # ===== TOGGLE CHECKBOX =====
    dcc.Checklist(
        id='show-chart-explanations-toggle',
        options=[{'label': '  Show Chart Explanations', 'value': 'show'}],
        value=[],
        inline=True,
        style={'marginBottom': '20px', 'fontSize': '0.9em', 'fontWeight': '500', 'color': '#495057'}
    ),
    
    html.Hr(),
    html.Div(id="onchain-error-alert", style={'marginBottom': '15px'}),
    
    # ===== KEY METRICS SUMMARY (ALL IN GREY BOX) =====
    html.Div([
        # Title + Metrics all in grey box
        html.Span("KEY METRICS SUMMARY", style={
            'fontSize': '0.9em', 'fontWeight': 'bold', 'textTransform': 'uppercase',
            'letterSpacing': '1px', 'color': '#495057', 'marginRight': '20px'
        }),
        
        html.Span([
            html.Span("Network Activity: ", style={'fontWeight': '500', 'color': '#495057'}),
            html.Span(id='summary-network', children='--', style={'fontWeight': 'bold'}),
            html.Span(id='summary-network-detail', children=' (Addr+TX avg)', 
                      style={'fontSize': '0.8em', 'color': '#868e96', 'fontStyle': 'italic'})
        ]),
        
        html.Span(" | ", style={'color': '#dee2e6', 'margin': '0 12px'}),
        
        html.Span([
            html.Span("Security: ", style={'fontWeight': '500', 'color': '#495057'}),
            html.Span(id='summary-security', children='--', style={'fontWeight': 'bold'}),
            html.Span(id='summary-security-detail', children=' (Hash+Diff avg)', 
                      style={'fontSize': '0.8em', 'color': '#868e96', 'fontStyle': 'italic'})
        ]),
        
        html.Span(" | ", style={'color': '#dee2e6', 'margin': '0 12px'}),
        
        html.Span([
            html.Span("Valuation: ", style={'fontWeight': '500', 'color': '#495057'}),
            html.Span(id='summary-valuation', children='--', style={'fontWeight': 'bold'}),
            html.Span(id='summary-valuation-detail', children=' (NVT vs median)', 
                      style={'fontSize': '0.8em', 'color': '#868e96', 'fontStyle': 'italic'})
        ]),
        
        html.Span(" | ", style={'color': '#dee2e6', 'margin': '0 12px'}),
        
        html.Span([
            html.Span("Economics: ", style={'fontWeight': '500', 'color': '#495057'}),
            html.Span(id='summary-economics', children='--', style={'fontWeight': 'bold'}),
            html.Span(id='summary-economics-detail', children=' (Rev vs 90d MA)', 
                      style={'fontSize': '0.8em', 'color': '#868e96', 'fontStyle': 'italic'})
        ]),
        
    ], style={
        'display': 'flex',
        'alignItems': 'center',
        'fontSize': '0.85em',
        'marginBottom': '25px',
        'backgroundColor': '#f8f9fa',
        'padding': '12px 18px',
        'border': '1px solid #dee2e6',
        'borderRadius': '4px'
    }),
    
    # ===== METRICS CARDS (6 cards - NO explanations here) =====
    html.Div([
        html.Div([
            html.P("ACTIVE ADDRESSES", style=LABEL_STYLE),
            html.H4(id="active-addr-current", children="--", style=VALUE_STYLE),
            html.P(id="active-addr-delta", children="--", style=DELTA_STYLE),
            html.P(id="active-addr-context", children="--", style=CONTEXT_STYLE)
        ], style=CARD_STYLE),
        
        html.Div([
            html.P("TRANSACTION COUNT", style=LABEL_STYLE),
            html.H4(id="tx-count-current", children="--", style=VALUE_STYLE),
            html.P(id="tx-count-delta", children="--", style=DELTA_STYLE),
            html.P(id="tx-count-context", children="--", style=CONTEXT_STYLE)
        ], style=CARD_STYLE),
        
        html.Div([
            html.P("HASH RATE (EH/S)", style=LABEL_STYLE),
            html.H4(id="hash-rate-current", children="--", style=VALUE_STYLE),
            html.P(id="hash-rate-delta", children="--", style=DELTA_STYLE),
            html.P(id="hash-rate-context", children="--", style=CONTEXT_STYLE)
        ], style=CARD_STYLE),
        
        html.Div([
            html.P("MINING DIFFICULTY", style=LABEL_STYLE),
            html.H4(id="difficulty-current", children="--", style=VALUE_STYLE),
            html.P(id="difficulty-delta", children="--", style=DELTA_STYLE),
            html.P(id="difficulty-context", children="--", style=CONTEXT_STYLE)
        ], style=CARD_STYLE),
        
        html.Div([
            html.P("NVT RATIO", style=LABEL_STYLE),
            html.H4(id="nvt-current", children="--", style=VALUE_STYLE),
            html.P(id="nvt-delta", children="--", style=DELTA_STYLE),
            html.P(id="nvt-context", children="--", style=CONTEXT_STYLE)
        ], style=CARD_STYLE),
        
        html.Div([
            html.P("MINERS REVENUE (USD)", style=LABEL_STYLE),
            html.H4(id="miners-rev-current", children="--", style=VALUE_STYLE),
            html.P(id="miners-rev-delta", children="--", style=DELTA_STYLE),
            html.P(id="miners-rev-context", children="--", style=CONTEXT_STYLE)
        ], style=CARD_STYLE),
        
    ], style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'space-between', 'marginBottom': '25px'}),
    
    # ===== SECTION 1: NETWORK ACTIVITY =====
    html.Hr(),
    html.H3("NETWORK ACTIVITY", style=SECTION_TITLE_STYLE),
    html.Div([
        html.Div([
            html.H4("Active Addresses", style={'marginBottom': '15px', 'fontSize': '1em', 'fontWeight': '500'}),
            dcc.Loading(id="loading-active-addresses", type="default",
                       children=[dcc.Graph(id="active-addresses-chart")]),
            create_explanation_panel('active_addr', 'active-addr-explanation')
        ], style=CHART_LEFT_STYLE),
        
        html.Div([
            html.H4("Transaction Count", style={'marginBottom': '15px', 'fontSize': '1em', 'fontWeight': '500'}),
            dcc.Loading(id="loading-tx-count", type="default",
                       children=[dcc.Graph(id="tx-count-chart")]),
            create_explanation_panel('tx_count', 'tx-count-explanation')
        ], style=CHART_RIGHT_STYLE),
    ], style={'marginBottom': '30px'}),
    
    # ===== SECTION 2: NETWORK SECURITY =====
    html.Hr(),
    html.H3("NETWORK SECURITY", style=SECTION_TITLE_STYLE),
    html.Div([
        html.Div([
            html.H4("Hash Rate (EH/s)", style={'marginBottom': '15px', 'fontSize': '1em', 'fontWeight': '500'}),
            dcc.Loading(id="loading-hash-rate", type="default",
                       children=[dcc.Graph(id="hash-rate-chart")]),
            create_explanation_panel('hash_rate', 'hash-rate-explanation')
        ], style=CHART_LEFT_STYLE),
        
        html.Div([
            html.H4("Mining Difficulty", style={'marginBottom': '15px', 'fontSize': '1em', 'fontWeight': '500'}),
            dcc.Loading(id="loading-difficulty", type="default",
                       children=[dcc.Graph(id="difficulty-chart")]),
            create_explanation_panel('difficulty', 'difficulty-explanation')
        ], style=CHART_RIGHT_STYLE),
    ], style={'marginBottom': '30px'}),
    
    # ===== SECTION 3: VALUATION & ECONOMICS =====
    html.Hr(),
    html.H3("VALUATION AND ECONOMICS", style=SECTION_TITLE_STYLE),
    html.Div([
        html.Div([
            html.H4("NVT Ratio", style={'marginBottom': '15px', 'fontSize': '1em', 'fontWeight': '500'}),
            dcc.Loading(id="loading-nvt", type="default",
                       children=[dcc.Graph(id="nvt-chart")]),
            create_explanation_panel('nvt', 'nvt-explanation')
        ], style=CHART_LEFT_STYLE),
        
        html.Div([
            html.H4("Miners Revenue (USD)", style={'marginBottom': '15px', 'fontSize': '1em', 'fontWeight': '500'}),
            dcc.Loading(id="loading-miners-revenue", type="default",
                       children=[dcc.Graph(id="miners-revenue-chart")]),
            create_explanation_panel('miners_rev', 'miners-rev-explanation')
        ], style=CHART_RIGHT_STYLE),
    ], style={'marginBottom': '30px'}),
    
    # ===== FOOTER =====
    html.Hr(),
    html.Div([
        html.P(id='last-update-footer', children='Last Update: --',
               style={'textAlign': 'center', 'fontSize': '0.75em', 'color': '#868e96', 
                      'marginTop': '20px', 'marginBottom': '20px'})
    ]),
    
    # ===== DATA MANAGEMENT =====
    dcc.Store(id='onchain-data-store'),
    dcc.Interval(id='onchain-refresh-interval', interval=3600000, n_intervals=0),
])
