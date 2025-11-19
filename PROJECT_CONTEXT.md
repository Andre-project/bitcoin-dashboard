# Bitcoin Ecosystem Dashboard - Developer Context

## PROJECT OVERVIEW

**Project Name**: Bitcoin Ecosystem Dashboard - Network + Institutions
**Type**: Data Science / QuantFin Portfolio Project
**Status**: In Development (MVP Phase)
**Language**: Python 3.11
**Primary Framework**: Streamlit
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
streamlit==1.29.0

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
streamlit run dashboard/app.py

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

### Streamlit
Run dashboard locally
streamlit run dashboard/app.py

Run on specific port
streamlit run dashboard/app.py --server.port 8502

Clear cache
streamlit cache clear

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

**3. Streamlit caching**
Use @st.cache_data for data functions
@st.cache_data(ttl=3600) # Cache 1 hour
def load_data():
return pd.read_csv('data.csv')

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
- **Load data once** at startup (not on every interaction)
- **Use Streamlit caching** (`@st.cache_data`)
- **Lazy load tabs** (only compute when tab opened)
- **Limit data points** in charts (resample if > 1000 points)

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
streamlit run dashboard/app.py

Access: http://localhost:8501
text

### Streamlit Cloud (Free Hosting)
1. Push code to GitHub
2. Go to share.streamlit.io
3. Connect GitHub repo
4. Deploy (auto-updates on git push)

### Environment Variables on Streamlit Cloud
- Go to App Settings → Secrets
- Add: `GLASSNODE_API_KEY = "your_key"`
- Access in code: `st.secrets["GLASSNODE_API_KEY"]`

---

## TROUBLESHOOTING

### VS Code Not Using venv
Command Palette (Cmd+Shift+P)
Type: Python: Select Interpreter
Choose: Python 3.11.x ('venv': venv)
text

### Streamlit Port Already in Use
Kill process on port 8501
lsof -ti:8501 | xargs kill -9

Or use different port
streamlit run dashboard/app.py --server.port 8502

text

### Git Push Rejected
If diverged from remote
git pull --rebase origin main
git push origin main

text

---

## RESOURCES

### Documentation
- Streamlit: https://docs.streamlit.io/
- Pandas: https://pandas.pydata.org/docs/
- Plotly: https://plotly.com/python/
- Glassnode API: https://docs.glassnode.com/api/

### Learning Resources
- Pandas 10min: https://pandas.pydata.org/docs/user_guide/10min.html
- Streamlit Gallery: https://streamlit.io/gallery
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
8. Suggest caching for expensive operations
9. Remind to add new dependencies to requirements.txt
10. Follow project structure (don't create files outside defined folders)

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

**Last Updated**: November 19, 2025
**Version**: 0.1.0 (MVP Phase)