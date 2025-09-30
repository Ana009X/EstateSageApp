# Real Estate Evaluator

## Overview

A Streamlit-based real estate evaluation platform that provides AI-powered insights for property analysis across four distinct workflows: Rent, Buy, Sell, and Investment. The application offers dual input methods (URL scraping or manual address entry) and generates comprehensive evaluations with financial metrics, market analysis, and visual insights to support real estate decision-making.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Framework
- **Frontend**: Streamlit web framework with custom UI components for interactive property evaluation
- **Session Management**: Streamlit session state for navigation routing and data persistence across page transitions
- **Database**: PostgreSQL for storing evaluation history with JSONB columns for flexible property and market data storage
- **Data Validation**: Pydantic models for type-safe data structures and API contracts

### Core Architectural Patterns

**Page Routing System**
- Session-based navigation using `st.session_state.current_page` to manage multi-page flows
- Main pages: home, evaluation forms (rent/buy/sell/investment), results, history, and comparison views
- UUID-based session tracking for user journey analytics and evaluation history

**Data Input Pipeline**
- Dual input strategy: URL scraping with BeautifulSoup fallback or manual address entry
- Best-effort web scraping with respectful headers and error handling
- Geocoding via OpenStreetMap Nominatim API (free, no API key required)
- Data enrichment through RentCast API when credentials are available

**AI Integration Layer**
- OpenAI GPT-5 integration for natural language property summaries and insights
- Graceful degradation to rule-based heuristics when API key is unavailable
- JSON-structured responses for consistent parsing
- Error handling ensures application continues functioning without AI features

**Market Analysis Engine**
- Comparable properties (comps) analysis with RentCast API primary, mock data fallback
- Statistical calculations: median prices, price per sqft, days on market, supply-demand ratios
- Price positioning logic (underpriced/average/overpriced) based on market percentiles
- Trend analysis for 12-month and 5-year price movements

**Financial Metrics Calculation**
- Mortgage payment calculations with PITI (Principal, Interest, Taxes, Insurance)
- Investment metrics: NOI (Net Operating Income), Cap Rate, Cash-on-Cash returns
- Rent estimation algorithms using comp-based analysis and price-to-rent ratios
- Configurable assumptions for interest rates, down payments, and loan terms

**Visual Components**
- Custom status bars using Streamlit columns with color-coded segments (green/amber/red)
- Flag system for red/green indicators highlighting risks and opportunities
- Metric cards for displaying financial KPIs
- Property headers with formatted address and key attributes

**Database Schema Design**
- Single `evaluations` table with UUID primary keys
- JSONB columns for flexible storage of property_data, market_stats, evaluation_data, and assumptions
- Indexed on session_id for user history retrieval and created_at for chronological sorting
- Supports multiple evaluation types through `flow` column (rent/buy/sell/investment)

### Error Handling Strategy
- Try-catch blocks with fallback mechanisms at each integration point
- Database initialization errors displayed to user via Streamlit error messages
- API failures gracefully degrade to mock/sample data
- Timeout configurations on external requests (5-10 seconds)

### Scalability Considerations
- PostgreSQL connection pooling through psycopg2 for concurrent users
- Stateless evaluation logic allowing horizontal scaling
- API rate limiting handled through provider-agnostic service layer
- JSONB storage enables schema evolution without migrations

## External Dependencies

### Required Services
- **PostgreSQL Database**: Primary data store accessed via `DATABASE_URL` environment variable
- **Streamlit Cloud/Server**: Application hosting platform running on port 5000

### Optional API Integrations
- **OpenAI API** (`OPENAI_API_KEY`): GPT-5 model for AI-powered property summaries and insights
- **RentCast API** (`RENTCAST_API_KEY`): Real estate data provider for property facts, comparable sales, and market statistics
- **OpenStreetMap Nominatim**: Free geocoding service for address-to-coordinates conversion (no authentication required)

### Python Package Dependencies
- `streamlit`: Web application framework
- `pydantic`: Data validation and settings management
- `requests`: HTTP client for API calls and web scraping
- `beautifulsoup4`: HTML parsing for listing URL scraping
- `openai`: Official OpenAI Python client
- `psycopg2`: PostgreSQL database adapter with RealDictCursor support

### Data Provider Strategy
- Application designed with provider-agnostic service layer for future integration flexibility
- Documented TODOs for production-ready integrations: Zillow API, Redfin Data API, Realtor.com API, ATTOM Data Solutions
- Mock data generators ensure full functionality without external dependencies
- All external API calls include timeout configurations and error handling with fallbacks