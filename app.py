import streamlit as st
from models import PropertyInput, PropertyFacts, MarketStats, Evaluation
from services import scrape, geocode, market, ai, metrics
from utils.ui_components import render_status_bar, render_flags, render_metric_card, render_property_header
from utils.mock_data import generate_mock_property_facts, generate_flags
from datetime import datetime


# Page configuration
st.set_page_config(
    page_title="Real Estate Evaluator",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def main():
    """Main application entry point."""
    
    # Initialize session state
    if 'evaluation_data' not in st.session_state:
        st.session_state.evaluation_data = None
    
    # Routing
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'home'
    
    if st.session_state.current_page == 'home':
        render_home()
    elif st.session_state.current_page in ['rent', 'buy', 'sell', 'investment']:
        render_evaluation_form(st.session_state.current_page)
    elif st.session_state.current_page == 'result':
        render_result()


def render_home():
    """Render home page with 4 flow cards."""
    
    st.title("🏠 Real Estate Evaluator")
    st.markdown("### Evaluate properties with AI-powered insights")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Create 4 columns for the main flows
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container():
            st.markdown(
                '<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
                'padding: 30px; border-radius: 12px; color: white; margin-bottom: 20px;">',
                unsafe_allow_html=True
            )
            st.markdown("### 🔑 Rent Evaluation")
            st.markdown("Find fair rental rates and market insights")
            if st.button("Evaluate Rental", key="rent_btn", use_container_width=True):
                st.session_state.current_page = 'rent'
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown(
                '<div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); '
                'padding: 30px; border-radius: 12px; color: white; margin-bottom: 20px;">',
                unsafe_allow_html=True
            )
            st.markdown("### 💰 Sell Evaluation")
            st.markdown("Get optimal pricing for your property")
            if st.button("Evaluate Selling", key="sell_btn", use_container_width=True):
                st.session_state.current_page = 'sell'
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        with st.container():
            st.markdown(
                '<div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); '
                'padding: 30px; border-radius: 12px; color: white; margin-bottom: 20px;">',
                unsafe_allow_html=True
            )
            st.markdown("### 🏡 Buy Evaluation")
            st.markdown("Assess if a property is worth buying")
            if st.button("Evaluate Purchase", key="buy_btn", use_container_width=True):
                st.session_state.current_page = 'buy'
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown(
                '<div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); '
                'padding: 30px; border-radius: 12px; color: white; margin-bottom: 20px;">',
                unsafe_allow_html=True
            )
            st.markdown("### 📈 Investment Analysis")
            st.markdown("Calculate ROI and investment metrics")
            if st.button("Analyze Investment", key="invest_btn", use_container_width=True):
                st.session_state.current_page = 'investment'
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.info("💡 **Tip:** This app works with or without API keys. For enhanced AI insights, set your OPENAI_API_KEY environment variable.")


def render_evaluation_form(flow: str):
    """Render input form for property evaluation."""
    
    flow_titles = {
        'rent': '🔑 Rent Evaluation',
        'buy': '🏡 Buy Evaluation',
        'sell': '💰 Sell Evaluation',
        'investment': '📈 Investment Analysis'
    }
    
    # Back button
    if st.button("← Back to Home"):
        st.session_state.current_page = 'home'
        st.rerun()
    
    st.title(flow_titles[flow])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Input form
    with st.form(key=f"{flow}_form"):
        st.markdown("### Property Information")
        
        url = st.text_input(
            "Listing URL (optional)",
            placeholder="https://www.zillow.com/homedetails/...",
            help="Paste a property listing URL for automatic data extraction"
        )
        
        st.markdown('<p style="text-align: center; color: #6b7280;">— or —</p>', unsafe_allow_html=True)
        
        address = st.text_input(
            "Property Address",
            placeholder="123 Main St, San Francisco, CA 94102",
            help="Enter the full property address"
        )
        
        submit = st.form_submit_button("Evaluate Property", use_container_width=True)
        
        if submit:
            if not url and not address:
                st.error("Please provide either a listing URL or property address")
            else:
                with st.spinner("Analyzing property..."):
                    evaluate_property(flow, url, address)


def evaluate_property(flow: str, url: str = None, address: str = None):
    """Process property evaluation."""
    
    # Step 1: Get property facts
    if url:
        facts = scrape.parse_listing_url(url)
    elif address:
        facts = geocode.lookup_property_facts(address)
    else:
        st.error("No input provided")
        return
    
    # Step 2: Get market stats
    if facts.lat and facts.lon:
        stats = market.fetch_area_stats(facts.lat, facts.lon, facts.address.split(',')[-2].strip() if ',' in facts.address else None)
    else:
        stats = MarketStats(city="Unknown")
    
    # Step 3: Get comparables
    comps = market.get_comps(facts)
    
    # Step 4: Calculate metrics
    price_position = market.calculate_price_position(
        facts.list_price or facts.rent_estimate or 500000,
        comps
    )
    
    demand_supply = market.calculate_demand_supply_index(stats)
    
    # Step 5: Generate flags
    red_flags, green_flags = generate_flags(facts, stats, price_position, demand_supply)
    
    # Step 6: Flow-specific calculations
    details = {}
    bars = {
        'price_position': price_position,
        'demand_supply': demand_supply
    }
    
    if flow == 'rent':
        rent_est = metrics.estimate_rent(facts, comps)
        facts.rent_estimate = rent_est
        details['estimated_rent'] = rent_est
        details['condition'] = metrics.analyze_condition(facts)
        
    elif flow == 'buy':
        if facts.list_price:
            payment_info = metrics.calculate_monthly_payment(
                facts.list_price,
                taxes_annual=facts.taxes_annual or 0,
                hoa_monthly=facts.hoa_monthly or 0
            )
            details['monthly_payment'] = payment_info
            details['condition'] = metrics.analyze_condition(facts)
            
            # Calculate potential rental ROI
            if facts.rent_estimate or facts.sqft:
                rent = facts.rent_estimate or facts.sqft * 2.0
                cap_rate = (rent * 12 - (facts.taxes_annual or 0)) / facts.list_price * 100
                details['potential_cap_rate'] = cap_rate
    
    elif flow == 'sell':
        pricing_info = metrics.calculate_suggested_list_price(facts, stats, comps)
        details['suggested_pricing'] = pricing_info
        details['market_summary'] = {
            'active_listings': stats.active_listings,
            'sold_90d': stats.sold_last_90d,
            'dom_median': stats.dom_median
        }
    
    elif flow == 'investment':
        rent = facts.rent_estimate or metrics.estimate_rent(facts, comps)
        price = facts.list_price or 500000
        
        inv_metrics = metrics.calculate_investment_metrics(
            purchase_price=price,
            monthly_rent=rent,
            taxes_annual=facts.taxes_annual or price * 0.012,
            hoa_monthly=facts.hoa_monthly or 0
        )
        details['investment_metrics'] = inv_metrics
    
    # Step 7: Generate AI summary
    payload = {
        'facts': facts.dict(),
        'stats': stats.dict(),
        'metrics': details,
        'price_position': price_position,
        'demand_supply': demand_supply
    }
    
    summary = ai.ai_summarize(flow, payload)
    
    # Step 8: Create evaluation
    evaluation = Evaluation(
        summary=summary,
        bars=bars,
        red_flags=red_flags,
        green_flags=green_flags,
        details=details
    )
    
    # Store in session state
    st.session_state.evaluation_data = {
        'flow': flow,
        'facts': facts,
        'stats': stats,
        'evaluation': evaluation
    }
    
    # Navigate to results
    st.session_state.current_page = 'result'
    st.rerun()


def render_result():
    """Render evaluation results."""
    
    if not st.session_state.evaluation_data:
        st.error("No evaluation data found")
        if st.button("← Back to Home"):
            st.session_state.current_page = 'home'
            st.rerun()
        return
    
    data = st.session_state.evaluation_data
    flow = data['flow']
    facts = data['facts']
    stats = data['stats']
    evaluation = data['evaluation']
    
    # Back button
    if st.button("← Back to Home"):
        st.session_state.current_page = 'home'
        st.rerun()
    
    # Property header
    photo_url = facts.photos[0] if facts.photos else None
    render_property_header(facts, photo_url)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # AI Summary
    st.markdown("### 📊 Analysis Summary")
    st.info(evaluation.summary)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Status bars
    st.markdown("### 📈 Market Position")
    col1, col2 = st.columns(2)
    
    with col1:
        if flow == 'buy':
            render_status_bar(
                evaluation.bars['price_position'],
                labels=["Underpriced", "Average", "Overpriced"],
                title="Price Position"
            )
        else:
            render_status_bar(
                evaluation.bars['price_position'],
                labels=["Low", "Normal", "High"],
                title="Price Position"
            )
    
    with col2:
        render_status_bar(
            evaluation.bars['demand_supply'],
            labels=["Low Demand", "Balanced", "High Demand"],
            title="Market Demand"
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Flags
    render_flags(evaluation.red_flags, evaluation.green_flags)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Flow-specific details
    st.markdown("### 💼 Detailed Metrics")
    
    if flow == 'rent':
        render_rent_details(facts, stats, evaluation.details)
    elif flow == 'buy':
        render_buy_details(facts, stats, evaluation.details)
    elif flow == 'sell':
        render_sell_details(facts, stats, evaluation.details)
    elif flow == 'investment':
        render_investment_details(facts, stats, evaluation.details)
    
    # Market context
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🏘️ Market Context")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        render_metric_card("Active Listings", f"{stats.active_listings or 'N/A'}")
    with col2:
        render_metric_card("Sold (90d)", f"{stats.sold_last_90d or 'N/A'}")
    with col3:
        render_metric_card("Median DOM", f"{stats.dom_median or 'N/A'} days")
    with col4:
        if stats.price_trend_12m_pct is not None:
            delta_str = f"{stats.price_trend_12m_pct:+.1f}%"
            render_metric_card("1Y Price Trend", delta_str)
        else:
            render_metric_card("1Y Price Trend", "N/A")


def render_rent_details(facts, stats, details):
    """Render rent-specific details."""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'estimated_rent' in details:
            st.metric("Est. Monthly Rent", f"${details['estimated_rent']:,.0f}")
    
    with col2:
        if 'condition' in details:
            st.metric("Property Condition", details['condition'])
    
    with col3:
        if stats.median_list_price:
            st.metric("Area Median Price", f"${stats.median_list_price:,.0f}")


def render_buy_details(facts, stats, details):
    """Render buy-specific details."""
    
    if 'monthly_payment' in details:
        payment = details['monthly_payment']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Monthly", f"${payment['total_monthly']:,.0f}")
        with col2:
            st.metric("Mortgage", f"${payment['mortgage_payment']:,.0f}")
        with col3:
            st.metric("Property Tax", f"${payment['property_tax']:,.0f}")
        with col4:
            st.metric("Down Payment", f"${payment['down_payment']:,.0f}")
        
        if 'potential_cap_rate' in details:
            st.info(f"💡 If rented out, estimated cap rate: {details['potential_cap_rate']:.2f}%")


def render_sell_details(facts, stats, details):
    """Render sell-specific details."""
    
    if 'suggested_pricing' in details:
        pricing = details['suggested_pricing']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Suggested List Price", f"${pricing['suggested_price']:,.0f}")
        
        with col2:
            st.metric(
                "Price Range",
                f"${pricing['price_range_low']:,.0f} - ${pricing['price_range_high']:,.0f}"
            )
        
        if pricing['reasons']:
            st.markdown("**Pricing Rationale:**")
            for reason in pricing['reasons']:
                st.markdown(f"• {reason}")
    
    if 'market_summary' in details:
        summary = details['market_summary']
        st.markdown("**Market Summary:**")
        st.markdown(f"• Active listings: {summary.get('active_listings', 'N/A')}")
        st.markdown(f"• Sold last 90 days: {summary.get('sold_90d', 'N/A')}")
        st.markdown(f"• Median days on market: {summary.get('dom_median', 'N/A')}")


def render_investment_details(facts, stats, details):
    """Render investment-specific details."""
    
    if 'investment_metrics' in details:
        inv = details['investment_metrics']
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Cap Rate", f"{inv['cap_rate']:.2f}%")
        with col2:
            st.metric("Cash-on-Cash", f"{inv['cash_on_cash']:.2f}%")
        with col3:
            st.metric("Monthly NOI", f"${inv['monthly_noi']:,.0f}")
        with col4:
            st.metric("Annual Cash Flow", f"${inv['annual_cash_flow']:,.0f}")
        
        # Operating expenses
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**Operating Expenses (Annual):**")
        
        expenses = inv['operating_expenses']
        exp_col1, exp_col2, exp_col3 = st.columns(3)
        
        with exp_col1:
            st.markdown(f"• Property Tax: ${expenses['taxes']:,.0f}")
            st.markdown(f"• Insurance: ${expenses['insurance']:,.0f}")
        with exp_col2:
            st.markdown(f"• Maintenance: ${expenses['maintenance']:,.0f}")
            st.markdown(f"• Vacancy: ${expenses['vacancy']:,.0f}")
        with exp_col3:
            st.markdown(f"• Management: ${expenses['management']:,.0f}")
            st.markdown(f"• HOA: ${expenses['hoa']:,.0f}")
        
        st.markdown(f"**Total Operating Expenses: ${expenses['total']:,.0f}/year**")


if __name__ == "__main__":
    main()
