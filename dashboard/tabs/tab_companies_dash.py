"""
Bitcoin Treasuries Dashboard Layout - Final Version

Displays Bitcoin treasury holdings with:
- Key metrics cards
- Top Holdings by Category bar chart
- Category distribution pie chart  
- Holdings Evolution line chart (time series)
- 6 category tables in 2x3 grid (always visible)
"""

from dash import html, dcc, dash_table
from dash.dash_table.Format import Format, Scheme
from dash.dash_table import FormatTemplate

# =============================================================================
# STYLES
# =============================================================================

LABEL_STYLE = {
    'fontSize': '0.65em',
    'fontWeight': '600',
    'color': '#6c757d',
    'textTransform': 'uppercase',
    'letterSpacing': '0.5px',
    'marginBottom': '6px',
    'textAlign': 'center'
}

VALUE_STYLE = {
    'fontSize': '1.4em',
    'fontWeight': 'bold',
    'color': '#212529',
    'marginBottom': '5px',
    'textAlign': 'center'
}

SUBTEXT_STYLE = {
    'fontSize': '0.7em',
    'color': '#868e96',
    'textAlign': 'center'
}

CARD_STYLE = {
    'flex': '1',
    'padding': '20px',
    'border': '1px solid #dee2e6',
    'borderRadius': '4px',
    'backgroundColor': '#ffffff',
    'minHeight': '100px'
}

CHART_CONTAINER_STYLE = {
    'border': '1px solid #dee2e6',
    'borderRadius': '4px',
    'backgroundColor': '#ffffff',
    'padding': '20px'
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_metric_card(title: str, value_id: str, subtitle_id: str, value_color: str = '#212529') -> html.Div:
    """Create a metric card with title, value, and subtitle."""
    return html.Div([
        html.P(title, style=LABEL_STYLE),
        html.H3(id=value_id, children="--", style={**VALUE_STYLE, 'color': value_color}),
        html.P(id=subtitle_id, children="", style=SUBTEXT_STYLE)
    ], style=CARD_STYLE)


def create_category_table(category_name: str, category_id: str) -> html.Div:
    """Create a category section with table always visible."""
    return html.Div([
        # Simple header
        html.Div([
            html.H4(category_name, style={
                'fontSize': '1.1em',
                'fontWeight': '600',
                'color': '#212529',
                'margin': '0'
            })
        ], style={
            'padding': '12px 15px',
            'backgroundColor': '#f8f9fa',
            'borderBottom': '2px solid #007bff',
            'borderRadius': '4px 4px 0 0'
        }),
        
        # Table (always visible)
        html.Div([
            dash_table.DataTable(
                id=f'{category_id}-table',
                columns=[
                    {'name': '#', 'id': 'rank', 'type': 'numeric'},
                    {'name': 'Name', 'id': 'name'},
                    {'name': 'Country', 'id': 'country'},
                    {'name': 'BTC', 'id': 'btc', 'type': 'numeric',
                     'format': Format(group=',', scheme=Scheme.fixed, precision=0)},
                    {'name': 'Value (USD)', 'id': 'value_usd', 'type': 'numeric',
                     'format': FormatTemplate.money(0)},
                    {'name': '% Total', 'id': 'pct_total', 'type': 'numeric',
                     'format': FormatTemplate.percentage(2)},
                    {'name': 'Proof Score', 'id': 'proof_score', 'type': 'text'}
                ],
                data=[],
                style_table={'overflowX': 'auto', 'minHeight': '150px'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '8px 10px',
                    'fontFamily': 'system-ui, -apple-system, "Segoe UI", Roboto',
                    'fontSize': '0.85em',
                    'whiteSpace': 'normal',
                    'height': 'auto'
                },
                style_cell_conditional=[
                    {'if': {'column_id': 'rank'}, 'textAlign': 'center', 'width': '40px'},
                    {'if': {'column_id': 'btc'}, 'textAlign': 'right'},
                    {'if': {'column_id': 'value_usd'}, 'textAlign': 'right'},
                    {'if': {'column_id': 'pct_total'}, 'textAlign': 'right'},
                    {'if': {'column_id': 'proof_score'}, 'textAlign': 'center', 'width': '90px', 'fontWeight': '500'}
                ],
                style_header={
                    'backgroundColor': '#ffffff',
                    'fontWeight': 'bold',
                    'borderBottom': '2px solid #dee2e6',
                    'color': '#495057',
                    'fontSize': '0.8em'
                },
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa'},
                    {'if': {'column_id': 'rank'}, 'fontWeight': 'bold', 'color': '#007bff'},
                    {'if': {'column_id': 'name'}, 'fontWeight': '500'},
                    # Proof Score colors - High score (green, >=85%)
                    {'if': {'column_id': 'proof_score', 'filter_query': '{proof_score_value} >= 85'},
                     'color': '#198754', 'fontWeight': '600'},
                    # Proof Score colors - Medium score (orange, 60-84%)
                    {'if': {'column_id': 'proof_score', 'filter_query': '{proof_score_value} >= 60 && {proof_score_value} < 85'},
                     'color': '#fd7e14', 'fontWeight': '500'},
                    # Proof Score colors - Low score (red, <60%)
                    {'if': {'column_id': 'proof_score', 'filter_query': '{proof_score_value} < 60'},
                     'color': '#dc3545', 'fontWeight': '500'}
                ],
                # Tooltip configuration
                tooltip_data=[],
                tooltip_duration=None,
                tooltip_delay=0,
                css=[{
                    'selector': '.dash-table-tooltip',
                    'rule': '''
                        background-color: #2c3e50 !important;
                        color: white !important;
                        border-radius: 4px;
                        padding: 10px;
                        max-width: 350px;
                        white-space: pre-wrap;
                        font-size: 0.85em;
                        line-height: 1.5;
                    '''
                }],
                sort_action='native',
                sort_mode='single',
                page_action='none'
            )
        ], style={
            'backgroundColor': '#ffffff',
            'padding': '10px',
            'borderRadius': '0 0 4px 4px'
        })
        
    ], style={
        'border': '1px solid #dee2e6',
        'borderRadius': '4px',
        'backgroundColor': '#ffffff',
        'minHeight': '250px'
    })


# =============================================================================
# LAYOUT
# =============================================================================

layout = html.Div([

    # ===== HEADER =====
    html.Div([
        html.H1("Bitcoin Treasuries", style={'fontWeight': '600', 'marginBottom': '5px'}),
        html.P("Corporate and Institutional Bitcoin Holdings",
               style={'color': '#6c757d', 'fontSize': '1.05em', 'marginBottom': '15px'}),
        
        html.Div([
            html.Button(
                "Refresh Data",
                id='treasury-refresh-btn',
                n_clicks=0,
                style={
                    'padding': '8px 16px',
                    'backgroundColor': '#007bff',
                    'color': 'white',
                    'border': 'none',
                    'borderRadius': '4px',
                    'cursor': 'pointer',
                    'fontSize': '0.85em'
                }
            ),
            html.Span(id='treasury-last-update', children='Last update: --',
                      style={'marginLeft': '15px', 'fontSize': '0.85em', 'color': '#6c757d'}),
            html.Span(id='treasury-btc-price', children='',
                      style={'marginLeft': '15px', 'fontSize': '0.85em', 'color': '#28a745', 'fontWeight': '500'})
        ])
    ], style={'marginBottom': '25px'}),
    
    html.Hr(),
    
    # Error alert
    html.Div(id="treasury-error-alert", style={'marginBottom': '15px'}),
    
    # ===== KEY METRICS (4 cards) =====
    html.Div([
        create_metric_card("TOTAL ENTITIES", "treasury-total-entities", "treasury-entities-subtitle"),
        create_metric_card("TOTAL BTC HOLDINGS", "treasury-total-btc", "treasury-btc-subtitle", "#007bff"),
        create_metric_card("TOTAL VALUE (USD)", "treasury-total-value", "treasury-value-subtitle"),
        create_metric_card("% OF BTC SUPPLY", "treasury-supply-pct", "treasury-supply-subtitle", "#28a745"),
    ], style={
        'display': 'flex',
        'gap': '15px',
        'marginBottom': '30px'
    }),
    
    # ===== CHARTS ROW: Category Holdings Bar + Category Pie (CSS Grid) =====
    html.Div([
        # Left: Top Holdings by Category (bar chart)
        html.Div([
            html.H4("Top Holdings by Category", style={'marginBottom': '15px', 'fontWeight': '500'}),
            dcc.Loading(
                type="default",
                children=[dcc.Graph(id="treasury-category-bar", config={'displayModeBar': False}, style={'height': '400px'})]
            )
        ], style=CHART_CONTAINER_STYLE),
        
        # Right: Distribution pie chart
        html.Div([
            html.H4("Distribution by Category", style={'marginBottom': '15px', 'fontWeight': '500'}),
            dcc.Loading(
                type="default",
                children=[dcc.Graph(id="treasury-pie-chart", config={'displayModeBar': False}, style={'height': '400px'})]
            )
        ], style=CHART_CONTAINER_STYLE),
    ], style={
        'display': 'grid',
        'gridTemplateColumns': '1fr 1fr',
        'gap': '20px',
        'marginBottom': '30px'
    }),
    
    # ===== EVOLUTION CHART WITH CONTROLS =====
    html.Div([
        # Header with title + category checkboxes
        html.Div([
            # Title (left)
            html.H4("BTC Holdings Evolution by Category", style={
                'fontWeight': '500',
                'marginBottom': '0',
                'marginRight': '20px'
            }),
            
            # Category toggle checkboxes (right, inline)
            dcc.Checklist(
                id='evolution-category-toggle',
                options=[
                    {'label': ' ETFs', 'value': 'ETFs'},
                    {'label': ' Public', 'value': 'Public Companies'},
                    {'label': ' Private', 'value': 'Private Companies'},
                    {'label': ' Countries', 'value': 'Countries'},
                    {'label': ' Mining', 'value': 'Mining Companies'},
                    {'label': ' DeFi', 'value': 'DeFi'}
                ],
                value=['ETFs', 'Public Companies', 'Private Companies', 
                       'Countries', 'Mining Companies', 'DeFi'],
                inline=True,
                labelStyle={
                    'display': 'inline-flex',
                    'alignItems': 'center',
                    'marginRight': '12px',
                    'fontSize': '0.82em',
                    'cursor': 'pointer',
                    'color': '#495057'
                },
                inputStyle={
                    'marginRight': '4px',
                    'cursor': 'pointer'
                },
                style={'display': 'flex', 'flexWrap': 'wrap', 'alignItems': 'center'}
            )
        ], style={
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'space-between',
            'flexWrap': 'wrap',
            'gap': '10px',
            'padding': '15px 20px',
            'backgroundColor': '#f8f9fa',
            'borderRadius': '4px 4px 0 0',
            'borderBottom': '1px solid #dee2e6'
        }),
        
        # Chart
        dcc.Loading(
            type="default",
            children=[
                dcc.Graph(
                    id="treasury-evolution-chart",
                    config={'displayModeBar': False},
                    style={'height': '400px'}
                )
            ]
        ),
        
        # Date Range Slider (below chart) - only end date adjustable
        html.Div([
            html.Div([
                html.Label("Date Range:", style={
                    'fontSize': '0.85em',
                    'fontWeight': '500',
                    'marginRight': '15px',
                    'color': '#495057'
                }),
                html.Span(id='evolution-date-display', style={
                    'fontSize': '0.85em',
                    'color': '#6c757d'
                })
            ], style={
                'display': 'flex',
                'alignItems': 'center',
                'marginBottom': '15px'
            }),
            
            dcc.Slider(
                id='evolution-date-slider',
                min=0,
                max=89,
                step=1,
                value=89,
                marks={},
                tooltip={'placement': 'bottom', 'always_visible': False},
                updatemode='mouseup'
            )
        ], style={
            'padding': '15px 25px 25px 25px',
            'backgroundColor': '#ffffff',
            'borderTop': '1px solid #e9ecef'
        })
        
    ], style={
        'border': '1px solid #dee2e6',
        'borderRadius': '4px',
        'backgroundColor': '#ffffff',
        'marginBottom': '40px'
    }),
    
    # ===== HOLDINGS BY CATEGORY (2x3 Grid - REORDERED) =====
    html.Hr(),
    html.H3("Holdings by Category", style={
        'fontSize': '1.3em',
        'fontWeight': '600',
        'marginBottom': '10px',
        'marginTop': '20px',
        'color': '#495057'
    }),
    
    # Proof Calculation collapsible block
    html.Div([
        html.Div([
            html.Span("Proof Calculation", style={
                'fontWeight': '600',
                'fontSize': '0.95em',
                'marginRight': '10px',
                'color': '#495057'
            }),
            html.Button(
                "Show details",
                id="proof-calculation-toggle",
                n_clicks=0,
                style={
                    'border': '1px solid #dee2e6',
                    'borderRadius': '4px',
                    'backgroundColor': '#f8f9fa',
                    'padding': '3px 10px',
                    'fontSize': '0.8em',
                    'cursor': 'pointer',
                    'color': '#495057'
                }
            )
        ], style={
            'display': 'flex',
            'alignItems': 'center',
            'marginBottom': '8px',
            'marginTop': '5px'
        }),
        
        html.Div(
            id="proof-calculation-panel",
            children=[
                dcc.Markdown(
                    """
**Score** = Public addresses (25%) + On-chain verification (25%) + Custody transparency (20%) + Official disclosure (15%) + Audit history (15%)

**Hard constraint:** If no public addresses disclosed, score capped at 75%
                    """.strip(),
                    style={
                        'fontSize': '0.85em',
                        'color': '#495057',
                        'lineHeight': '1.5'
                    }
                )
            ],
            style={
                'display': 'none',
                'border': '1px solid #dee2e6',
                'borderRadius': '4px',
                'padding': '10px 12px',
                'backgroundColor': '#f8f9fa',
                'marginBottom': '20px'
            }
        )
    ]),
    
    # Row 1: Public Companies + ETFs
    html.Div([
        create_category_table("Public Companies", "public-co"),
        create_category_table("ETFs", "etfs")
    ], style={
        'display': 'grid',
        'gridTemplateColumns': '1fr 1fr',
        'gap': '20px',
        'marginBottom': '20px'
    }),
    
    # Row 2: Private Companies + Mining Companies (SWITCHED)
    html.Div([
        create_category_table("Private Companies", "private-co"),
        create_category_table("Mining Companies", "mining")
    ], style={
        'display': 'grid',
        'gridTemplateColumns': '1fr 1fr',
        'gap': '20px',
        'marginBottom': '20px'
    }),
    
    # Row 3: DeFi + Countries (SWITCHED)
    html.Div([
        create_category_table("DeFi Protocols", "defi"),
        create_category_table("Countries", "countries")
    ], style={
        'display': 'grid',
        'gridTemplateColumns': '1fr 1fr',
        'gap': '20px'
    }),
    
    # ===== FOOTER =====
    html.Hr(style={'marginTop': '40px'}),
    html.Div([
        html.P(
            "Data source: BitcoinTreasuries.com | Sample data for demonstration",
            style={'textAlign': 'center', 'fontSize': '0.75em', 'color': '#868e96', 'margin': '20px 0'}
        )
    ]),
    
    # ===== DATA STORES =====
    dcc.Store(id='treasury-entities-store'),
    dcc.Store(id='evolution-data-store'),
])
