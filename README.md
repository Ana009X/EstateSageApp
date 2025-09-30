# Real Estate Evaluator

A Streamlit-based real estate evaluation tool with AI-powered insights for Rent, Buy, Sell, and Investment analysis.

## Features

- **Four Evaluation Flows:**
  - 🔑 **Rent**: Estimate fair rental rates and market insights
  - 🏡 **Buy**: Assess purchase value and affordability
  - 💰 **Sell**: Get optimal pricing recommendations
  - 📈 **Investment**: Calculate NOI, Cap Rate, and Cash-on-Cash returns

- **Dual Input Options:**
  - Listing URL scraping (best-effort with BeautifulSoup)
  - Manual address entry

- **AI-Powered Analysis:**
  - OpenAI GPT-5 integration for natural language summaries
  - Automatic fallback to rule-based heuristics without API key

- **Visual Insights:**
  - Status bars for price positioning and market demand
  - Red/green flags for quick decision-making
  - Comprehensive financial metrics

## Installation & Setup

### Prerequisites
- Python 3.8+
- pip

### Install Dependencies

The application will automatically install required packages. Key dependencies:
- streamlit
- pydantic
- requests
- beautifulsoup4
- openai (optional, for AI features)

### Running the Application

```bash
streamlit run app.py --server.port 5000
