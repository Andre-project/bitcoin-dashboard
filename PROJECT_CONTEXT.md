# Bitcoin Ecosystem Dashboard - Developer Context

## PROJECT OVERVIEW

**Project Name**: Bitcoin Ecosystem Dashboard - Network + Institutions
**Type**: Data Science / QuantFin Portfolio Project
**Status**: In Development (MVP Phase)
**Language**: Python 3.11
**Primary Framework**: Dash (Plotly) with dash-bootstrap-components
**Target**: Open-source portfolio showcase for QuantFin Master's student

### Project Goal
Build a comprehensive Bitcoin analytics dashboard combining 3 data sources:
1. On-Chain Metrics (Glassnode API)
2. ETF Flows (US Spot Bitcoin ETFs)
3. Strategic Reserves (Corporate + Government holdings)

### Unique Value Proposition
Multi-source convergence analysis - combining blockchain data, institutional flows, 
and treasury holdings to provide holistic Bitcoin ecosystem view. Very few projects 
do this integration.

### Architecture Overview
The project follows a modular architecture for scalability and maintainability:

- **data_collectors/**: Centralized data collection modules (e.g., `price_data.py` for CoinGecko API)
- **utils/**: Shared utilities (e.g., `logger.py` for logging)
- **dashboard/**: Dash application
  - `app.py`: Main Dash server with routing via callbacks
  - `tabs/*_dash.py`: Individual tab modules (e.g., `tab_price_dash.py`) with `layout` variable and callbacks
  - `assets/`: Static files (CSS, images) auto-loaded by Dash
- **tests/**: Unit tests with pytest
- **logs/**: Application logs

To add a new tab:
1. Create `dashboard/tabs/tab_new_dash.py` with a `layout` variable (Dash components) and `@callback` functions
2. Import the tab's layout in `app.py`: `from dashboard.tabs.tab_new_dash import layout as tab_new_layout`
3. Add to the callback in `app.py` that switches tab content: `elif active_tab == "tab-new": return tab_new_layout`
4. Add a `dbc.Tab` entry to the `dbc.Tabs` component in `app.py` layout

---

## DEVELOPMENT ENVIRONMENT

### Hardware & OS
- **Machine**: MacBook (M1/M2 or Intel)
- **OS**: macOS (Sonoma/Ventura)
- **Terminal**: Default macOS Terminal or iTerm2

### Python Setup
- **Version**: Python 3.11.x
- **Package Manager**: pip
- **Virtual Environment**: venv (not conda)
- **Environment Location**: `./venv/` (at project root)

### IDE Configuration
- **Primary IDE**: Visual Studio Code 1.85+
- **Extensions Installed**:
  - Python (Microsoft) - Core Python support
  - Pylance - Advanced IntelliSense
  - Python Indent - Auto-indentation
  - GitLens - Git integration

### VS Code Settings
{
"python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
"python.formatting.provider": "black",
"python.linting.enabled": true,
"python.linting.pylintEnabled": false,
"python.linting.flake8Enabled": true,
"editor.formatOnSave": true,
"files.exclude": {
"/pycache": true,
"/*.pyc": true
}
}

text

---

## PROJECT STRUCTURE

bitcoin-ecosystem-dashboard/
│
├── venv/ # Virtual environment (IGNORED BY GIT)
│
├── data/ # Raw data storage (IGNORED BY GIT)
│ ├── on_chain/ # Glassnode data cache
│ │ ├── mvrv.csv
│ │ ├── sopr.csv
│ │ └── hodl_waves.csv
│ ├── etf_flows/ # ETF daily flows
│ │ └── flows_history.csv
│ └── strategic_reserves/ # Corporate/govt holdings
│ └── holdings.csv
│
├── data_collectors/ # Data fetching modules
│ ├── init.py
│ ├── glassnode_api.py # On-chain data via Glassnode
│ ├── etf_scraper.py # ETF flows scraping
│ ├── treasury_scraper.py # Corporate holdings scraping
│ └── price_data.py # Bitcoin price (yfinance)
│
├── processors/ # Data processing & calculations
│ ├── init.py
│ ├── on_chain_metrics.py # MVRV, SOPR, NVT calculations
│ ├── etf_analytics.py # Flow analysis, correlations
│ └── convergence.py # Multi-signal scoring system
│
├── dashboard/ # Streamlit application
│ ├── app.py # Main dashboard entry point
│ ├── tab_network.py # On-chain metrics tab
│ ├── tab_etf.py # ETF flows tab
│ ├── tab_strategic.py # Strategic reserves tab
│ └── tab_convergence.py # Convergence analysis tab
│
├── utils/ # Helper utilities
│ ├── init.py
│ ├── database.py # SQLite helper (optional)
│ ├── config.py # Configuration loader
│ └── logger.py # Logging setup
│
├── tests/ # Unit tests (pytest)
│ ├── init.py
│ └── test_collectors.py
│
├── .env # Environment variables (NEVER COMMIT)
├── .gitignore # Git ignore rules
├── requirements.txt # Python dependencies
├── README.md # Project documentation
├── PROJECT_CONTEXT.md # This file (AI context)
└── config.yaml # App configuration (optional)

text

---

## DEPENDENCIES (requirements.txt)

Core Data Science
pandas==2.1.4
numpy==1.26.2

API & Web Scraping
requests==2.31.0
beautifulsoup4==4.12.2
selenium==4.15.2 # If dynamic scraping needed

Data Visualization
plotly==5.18.0
matplotlib==3.8.2
seaborn==0.13.0

Dashboard Framework
dash==2.14.2
dash-bootstrap-components==1.5.0
dash-bootstrap-themes==1.1.0

Database (Optional)
sqlalchemy==2.0.23

Utilities
python-dateutil==2.8.2
python-dotenv==1.0.0
pyyaml==6.0.1

Optional: Statistics/ML
scikit-learn==1.3.2
scipy==1.11.4
statsmodels==0.14.1

Development
pytest==7.4.3
black==23.12.0
flake8==6.1.0

text

---

## ENVIRONMENT VARIABLES (.env)

API Keys (NEVER COMMIT THIS FILE)
GLASSNODE_API_KEY=your_glassnode_api_key_here

Optional
COINMETRICS_API_KEY=
BLOCKCHAIN_API_KEY=

Database (if used)
DATABASE_URL=sqlite:///data/bitcoin_dashboard.db

Logging
LOG_LEVEL=INFO

text

---

## DATA SOURCES

### 1. On-Chain Data
- **Primary**: Glassnode API (free tier: 10 metrics, daily updates)
- **Endpoint**: `https://api.glassnode.com/v1/metrics/`
- **Auth**: API key in header `?api_key=YOUR_KEY`
- **Rate Limit**: 10 requests/minute (free tier)
- **Metrics tracked**:
  - MVRV Ratio (market cap / realized cap)
  - SOPR (Spent Output Profit Ratio)
  - HODL Waves (supply age distribution)
  - Hash Ribbons (miner capitulation)
  - Active Addresses (network activity)
  - NVT Ratio (network value / transactions)

### 2. ETF Flows
- **Source**: Web scraping (Farside Investors, SEC filings)
- **Update**: Daily (market close)
- **ETFs tracked**:
  - IBIT (BlackRock)
  - FBTC (Fidelity)
  - GBTC (Grayscale)
  - ARKB (ARK Invest)
  - BITB (Bitwise)
  - Others: HODL, BRRR, EZBC
- **Data format**: CSV with columns [date, etf_ticker, net_flow_usd]

### 3. Strategic Reserves
- **Source**: Manual entry + web scraping (Bitcoin Treasuries)
- **Update**: Weekly/Monthly
- **Categories**:
  - Public companies (MicroStrategy, Tesla, Block, etc.)
  - Governments (USA, El Salvador, Bhutan, etc.)
- **Data format**: CSV with columns [entity, type, btc_holdings, last_update]

### 4. Price Data
- **Source**: yfinance library
- **Ticker**: BTC-USD
- **Frequency**: Daily
- **Backup**: CoinGecko API if yfinance fails

---

## WORKFLOW

### Daily Development Workflow

1. Start session
cd ~/Desktop/bitcoin-ecosystem-dashboard
source venv/bin/activate

2. Pull latest changes (if collaborating)
git pull

3. Open VS Code
code .

4. Run tests before coding
pytest tests/

5. Work on features
Edit files, test locally
6. Run dashboard for testing
python dashboard/app.py

7. Commit progress
git add .
git commit -m "Descriptive message"
git push

8. End session
deactivate

text

### Data Collection Workflow

Manual data refresh (run daily/weekly)
python data_collectors/glassnode_api.py
python data_collectors/etf_scraper.py
python data_collectors/treasury_scraper.py

Or automated (cron job / GitHub Actions)
text

### Testing Workflow

Run all tests
pytest

Run specific test file
pytest tests/test_collectors.py

Run with coverage
pytest --cov=data_collectors --cov-report=html

text

---

## CODING STANDARDS

### Python Style
- **Style Guide**: PEP 8
- **Formatter**: Black (line length: 88)
- **Linter**: Flake8
- **Docstrings**: Google style

### Example Function Template
def fetch_bitcoin_price(start_date: str, end_date: str) -> pd.DataFrame:
"""
Fetch Bitcoin price data for given date range.

text
Args:
    start_date (str): Start date in 'YYYY-MM-DD' format
    end_date (str): End date in 'YYYY-MM-DD' format

Returns:
    pd.DataFrame: Price data with columns [date, open, high, low, close, volume]

Raises:
    ValueError: If date format is invalid
    requests.RequestException: If API call fails

Example:
    >>> df = fetch_bitcoin_price('2024-01-01', '2024-12-31')
    >>> print(df.head())
"""
try:
    # Implementation
    pass
except Exception as e:
    logger.error(f"Error fetching price: {e}")
    return None
text

### Error Handling
- **Always** use try/except for API calls
- **Always** validate data before processing
- **Always** log errors with context
- **Never** let exceptions crash the dashboard

### Git Commit Messages
feat: Add Glassnode MVRV data collector
fix: Handle API timeout in ETF scraper
docs: Update README with setup instructions
refactor: Simplify convergence scoring logic
test: Add unit tests for on-chain metrics

text

---

## COMMON COMMANDS

### Python Environment
Activate venv
source venv/bin/activate

Deactivate
deactivate

Install new package
pip install package-name

Update requirements.txt
pip freeze > requirements.txt

Install from requirements
pip install -r requirements.txt

text

### Dash
Run dashboard locally
python dashboard/app.py

Run on specific port
python dashboard/app.py --port 8502

Run in debug mode (auto-reload on file changes)
python dashboard/app.py --debug

text

### Git
Status
git status

Stage all changes
git add .

Commit
git commit -m "Message"

Push
git push origin main

Pull
git pull

Create branch
git checkout -b feature/new-metric

Switch branch
git checkout main

text

---

## DEBUGGING TIPS

### Common Issues

**1. Import errors**
If "ModuleNotFoundError: No module named 'X'"
→ Check venv is activated (should see (venv) in prompt)
→ Reinstall: pip install X
text

**2. API timeouts**
Always set timeout
response = requests.get(url, timeout=10)

Retry logic
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

retry_strategy = Retry(total=3, backoff_factor=1)
adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
session.mount("https://", adapter)

text

**3. Dash callbacks**
Use dcc.Store for data caching across callbacks
layout = html.Div([
    dcc.Store(id='data-store'),
    # other components
])

@callback(
    Output('data-store', 'data'),
    Input('refresh-btn', 'n_clicks')
)
def load_data(n_clicks):
    df = pd.read_csv('data.csv')
    return df.to_dict('records')  # Serialize for JSON

text

**4. DateTime issues**
Always parse dates consistently
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date')
df.set_index('date', inplace=True)

text

---

## PERFORMANCE CONSIDERATIONS

### Data Caching Strategy
- **Cache API responses** to disk (CSV) for 24h
- **Check cache** before making API call
- **Invalidate cache** if > 24h old or on manual refresh

### Rate Limiting
- **Glassnode**: Max 10 requests/minute
- **Use**: `time.sleep(6)` between requests
- **Or**: `ratelimit` library decorator

### Dashboard Optimization
- **Load data once** with `dcc.Store` + `dcc.Interval` for initial load
- **Use callback context** to prevent unnecessary updates (`PreventUpdate`, `no_update`)
- **Lazy load tabs** via conditional callbacks (only execute when tab active)
- **Limit data points** in charts (resample if > 1000 points)
- **Use `prevent_initial_call=True`** on callbacks that require user input

---

## PROJECT PHASES

### Phase 1: MVP (Week 1-2) - CURRENT
- [ ] Setup complete (Python, VS Code, Git)
- [ ] Bitcoin price fetcher (yfinance)
- [ ] Basic Streamlit dashboard (1 chart)
- [ ] Glassnode API connector (1 metric: MVRV)
- [ ] Display MVRV in dashboard
- [ ] Git + GitHub setup

### Phase 2: Core Features (Week 3-4)
- [ ] 5+ on-chain metrics (SOPR, HODL Waves, etc.)
- [ ] Tab 1: Network Health (on-chain dashboard)
- [ ] Tab 2: ETF Flows (scraper + visualization)
- [ ] Tab 3: Strategic Reserves (manual data entry)
- [ ] Basic convergence scoring

### Phase 3: Polish (Week 5-6)
- [ ] Tab 4: Convergence Analysis (traffic light system)
- [ ] Alert system (email/Telegram)
- [ ] README with screenshots
- [ ] Unit tests (>70% coverage)
- [ ] Deploy (Streamlit Cloud or Render)
- [ ] LinkedIn post + GitHub release

---

## DEPLOYMENT

### Local Development
python dashboard/app.py

Access: http://localhost:8050
text

### Production Deployment Options

**Option 1: Render (Free Tier)**
1. Push code to GitHub
2. Create new Web Service on render.com
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python dashboard/app.py`
5. Add environment variables in Render dashboard

**Option 2: Railway**
1. Connect GitHub repo to Railway
2. Auto-detects Python + requirements.txt
3. Set `PYTHONUNBUFFERED=1` in environment
4. Runs `python dashboard/app.py` automatically

**Option 3: Heroku**
1. Create `Procfile`: `web: python dashboard/app.py`
2. Push to Heroku: `git push heroku main`
3. Set environment variables: `heroku config:set GLASSNODE_API_KEY=your_key`

### Environment Variables in Production
- Set in hosting platform's dashboard (not in .env)
- Access in code: `os.getenv("GLASSNODE_API_KEY")`

---

## TROUBLESHOOTING

### VS Code Not Using venv
Command Palette (Cmd+Shift+P)
Type: Python: Select Interpreter
Choose: Python 3.11.x ('venv': venv)
text

### Dash Port Already in Use
Kill process on port 8050
lsof -ti:8050 | xargs kill -9

Or use different port in app.py
app.run_server(debug=True, port=8502)

text

### Git Push Rejected
If diverged from remote
git pull --rebase origin main
git push origin main

text

---

## RESOURCES

### Documentation
- Dash: https://dash.plotly.com/
- Dash Bootstrap Components: https://dash-bootstrap-components.opensource.faculty.ai/
- Pandas: https://pandas.pydata.org/docs/
- Plotly: https://plotly.com/python/
- Glassnode API: https://docs.glassnode.com/api/

### Learning Resources
- Pandas 10min: https://pandas.pydata.org/docs/user_guide/10min.html
- Dash Tutorial: https://dash.plotly.com/tutorial
- Dash Gallery: https://dash-gallery.plotly.host/Portal/
- Dash Callbacks: https://dash.plotly.com/basic-callbacks
- Python Error Handling: https://realpython.com/python-exceptions/

---

## CONTACT & COLLABORATION

**Project Owner**: [Your Name]
**GitHub**: https://github.com/yourusername/bitcoin-ecosystem-dashboard
**LinkedIn**: [Your LinkedIn URL]

**Collaboration**: Open to suggestions, PRs welcome
**License**: MIT (open source)

---

## NOTES FOR AI ASSISTANT

### When Helping with Code:
1. Always assume macOS environment (use `source venv/bin/activate`, not Windows commands)
2. Follow PEP 8 style guide
3. Add docstrings to all functions
4. Use type hints where possible
5. Include error handling (try/except) for API calls
6. Use logging instead of print statements for production code
7. Check if venv is activated before suggesting pip install
8. Use `dcc.Store` for data caching in Dash (serialize with `.to_dict('records')`)
9. Remind to add new dependencies to requirements.txt
10. Follow project structure (don't create files outside defined folders)
11. **Dash-specific**: Always use `@callback` decorator from `dash`, not `@app.callback`
12. **Dash-specific**: Use `prevent_initial_call=True` for callbacks requiring user input
13. **Dash-specific**: Place CSS files in `dashboard/assets/` for auto-loading
14. **Dash-specific**: Use `dash-bootstrap-components` (dbc) for layout (not raw html.Div)
15. **Dash-specific**: Serialize DataFrames with `.to_dict('records')` before storing in dcc.Store

### Current Development Priority:
Focus on Phase 1 MVP - Getting basic data collection + simple dashboard working before 
adding complexity. Start with Bitcoin price (yfinance) → Simple line chart → Then 
add Glassnode data.

### Known Limitations:
- Glassnode free tier: Only 10 metrics, daily updates (no intraday)
- ETF data: Manual scraping (no official API)
- Strategic reserves: Manual entry required (no real-time updates)
- Performance: Not optimized for mobile (desktop-first dashboard)

---

**Last Updated**: November 24, 2024
**Version**: 0.2.0 (Dash Migration Phase)