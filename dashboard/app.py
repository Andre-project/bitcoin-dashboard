import dash
from dash import dcc, html, Input, Output, callback, callback_context, State
import os
import sys
from datetime import datetime

# --- PATH CONFIGURATION ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- DASH APP INITIALIZATION (SANS BOOTSTRAP) ---
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)

app.title = "Bitcoin Dashboard"
server = app.server  # For production deployment

# --- LAYOUT PRINCIPAL AVEC SIDEBAR ---
app.layout = html.Div([
    # Sidebar verticale à gauche
    html.Div([
        html.Div([
            html.H2("Bitcoin Dashboard", style={'margin': '0', 'padding': '20px', 'textAlign': 'center', 'fontSize': '2em', 'borderBottom': '1px solid #dee2e6'}),
        ]),
        html.Div([
            html.Div([
                html.A("Price", id="nav-price", href="#", className="nav-link", **{'data-value': 'price'}),
            ], className="nav-item"),
            # html.Div([
            #     html.A("Network", id="nav-network", href="#", className="nav-link", **{'data-value': 'network'}),
            # ], className="nav-item"),
            # html.Div([
            #     html.A("ETF Flows", id="nav-etf", href="#", className="nav-link", **{'data-value': 'etf'}),
            # ], className="nav-item"),
        ], id="nav-menu", style={'padding': '10px 0'}),
    ], id="sidebar", className="sidebar"),
    
    # Bouton toggle pour plier/déplier la sidebar
    html.Button("", id="toggle-sidebar", className="toggle-btn"),
    
    # Contenu principal à droite
    html.Div([
        # Contenu dynamique
        html.Div(id="tab-content", style={'padding': '20px'}),
        
        # Store pour garder l'onglet actif
        dcc.Store(id='active-tab', data='price'),
        dcc.Store(id='sidebar-collapsed', data=False),
    ], id="main-content", className="main-content"),
], style={'display': 'flex', 'minHeight': '100vh'})

# --- CALLBACK POUR TOGGLE SIDEBAR ---
@callback(
    Output('sidebar', 'className'),
    Output('main-content', 'className'),
    Output('sidebar-collapsed', 'data'),
    Input('toggle-sidebar', 'n_clicks'),
    State('sidebar-collapsed', 'data'),
    prevent_initial_call=True
)
def toggle_sidebar(n_clicks, collapsed):
    """Toggle sidebar visibility"""
    if n_clicks:
        collapsed = not collapsed
        if collapsed:
            return 'sidebar sidebar-collapsed', 'main-content main-content-expanded', collapsed
        else:
            return 'sidebar', 'main-content', collapsed
    return 'sidebar', 'main-content', False

# --- CALLBACK POUR NAVIGATION ---
@callback(
    Output('tab-content', 'children'),
    Output('active-tab', 'data'),
    Input('nav-price', 'n_clicks'),
    # Input('nav-network', 'n_clicks'),
    # Input('nav-etf', 'n_clicks'),
    prevent_initial_call=False
)
def render_tab_content(price_clicks):
    """Load the appropriate tab layout based on navigation clicks"""
    ctx = callback_context
    
    if not ctx.triggered:
        # Initial load - show price tab
        from dashboard.tabs.tab_price_dash import layout
        return layout, 'price'
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'nav-price':
        from dashboard.tabs.tab_price_dash import layout
        return layout, 'price'
    # elif button_id == 'nav-network':
    #     return html.Div("Network tab not implemented yet"), 'network'
    # elif button_id == 'nav-etf':
    #     return html.Div("ETF tab not implemented yet"), 'etf'
    else:
        from dashboard.tabs.tab_price_dash import layout
        return layout, 'price'

# Enregistrer les callbacks des tabs
from dashboard.tabs.tab_price_dash_callbacks import register_callbacks
register_callbacks(app)

# --- RUN SERVER ---
if __name__ == '__main__':
    print("📋 Registered callbacks:", list(app.callback_map.keys()))
    app.run(debug=True, port=8050, host='127.0.0.1')
