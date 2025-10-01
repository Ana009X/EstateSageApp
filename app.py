import streamlit as st
from models import PropertyInput, PropertyFacts, MarketStats, Evaluation
from services import scrape, geocode, market, ai, metrics
from utils.ui_components import render_status_bar, render_flags, render_metric_card, render_property_header, render_property_status_and_pricing
from utils.mock_data import generate_mock_property_facts, generate_flags
from datetime import datetime
import database
import uuid


# Page configuration
st.set_page_config(
    page_title="Real Estate Evaluator",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def main():
    """Main application entry point."""
    
    # Initialize database
    try:
        database.init_database()
    except Exception as e:
        st.error(f"Database initialization error: {e}")
    
    # Initialize session state
    if 'evaluation_data' not in st.session_state:
        st.session_state.evaluation_data = None
    
    # Generate session ID if not exists
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    # Routing
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'home'
    
    if st.session_state.current_page == 'home':
        render_home()
    elif st.session_state.current_page in ['rent', 'buy', 'sell', 'investment']:
        render_evaluation_form(st.session_state.current_page)
    elif st.session_state.current_page == 'result':
        render_result()
    elif st.session_state.current_page == 'history':
        render_history()
    elif st.session_state.current_page == 'compare':
        render_compare()


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
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("💡 **Tip:** This app works with or without API keys. For enhanced AI insights, set your OPENAI_API_KEY environment variable.")
    with col2:
        if st.button("📚 View History", use_container_width=True):
            st.session_state.current_page = 'history'
            st.rerun()


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
    
    # Assumptions sidebar for Buy and Investment flows
    assumptions = {}
    if flow in ['buy', 'investment']:
        with st.sidebar:
            st.markdown("### 🎛️ Adjust Assumptions")
            st.markdown("Customize financial parameters for your calculation")
            
            assumptions['interest_rate'] = st.slider(
                "Interest Rate (%)",
                min_value=3.0,
                max_value=12.0,
                value=7.0,
                step=0.25,
                help="Annual mortgage interest rate"
            ) / 100
            
            assumptions['down_payment_pct'] = st.slider(
                "Down Payment (%)",
                min_value=0,
                max_value=50,
                value=20 if flow == 'buy' else 25,
                step=5,
                help="Percentage of purchase price as down payment"
            ) / 100
            
            assumptions['loan_term_years'] = st.selectbox(
                "Loan Term (years)",
                options=[15, 20, 30],
                index=2,
                help="Mortgage loan term in years"
            )
            
            if flow == 'investment':
                st.markdown("---")
                st.markdown("**Operating Expenses**")
                
                assumptions['vacancy_rate'] = st.slider(
                    "Vacancy Rate (%)",
                    min_value=0,
                    max_value=20,
                    value=5,
                    step=1,
                    help="Expected vacancy as % of annual rent"
                ) / 100
                
                assumptions['management_fee'] = st.slider(
                    "Property Management (%)",
                    min_value=0,
                    max_value=15,
                    value=8,
                    step=1,
                    help="Management fee as % of annual rent"
                ) / 100
                
                assumptions['maintenance_rate'] = st.slider(
                    "Maintenance Reserve (%)",
                    min_value=0,
                    max_value=20,
                    value=8,
                    step=1,
                    help="Maintenance budget as % of annual rent"
                ) / 100
    
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
                    evaluate_property(flow, url, address, assumptions)


def evaluate_property(flow: str, url: str | None = None, address: str | None = None, assumptions: dict = None):
    """Process property evaluation."""
    
    if assumptions is None:
        assumptions = {}
    
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
                down_payment_pct=assumptions.get('down_payment_pct', 0.20),
                interest_rate=assumptions.get('interest_rate', 0.07),
                loan_term_years=assumptions.get('loan_term_years', 30),
                taxes_annual=facts.taxes_annual or 0,
                hoa_monthly=facts.hoa_monthly or 0
            )
            details['monthly_payment'] = payment_info
            details['condition'] = metrics.analyze_condition(facts)
            details['assumptions'] = assumptions
            
            # Calculate potential rental ROI
            if facts.rent_estimate or facts.sqft:
                rent = facts.rent_estimate or (facts.sqft * 2.0 if facts.sqft else 2500.0)
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
        
        # Build investment metrics with custom assumptions
        inv_kwargs = {
            'purchase_price': price,
            'monthly_rent': rent,
            'taxes_annual': facts.taxes_annual or price * 0.012,
            'hoa_monthly': facts.hoa_monthly or 0,
            'down_payment_pct': assumptions.get('down_payment_pct', 0.25),
            'interest_rate': assumptions.get('interest_rate', 0.07),
            'loan_term_years': assumptions.get('loan_term_years', 30),
            'vacancy_rate': assumptions.get('vacancy_rate', 0.05),
            'management_fee': assumptions.get('management_fee', 0.08),
            'maintenance_rate': assumptions.get('maintenance_rate', 0.08)
        }
        
        inv_metrics = metrics.calculate_investment_metrics(**inv_kwargs)
        details['investment_metrics'] = inv_metrics
        details['assumptions'] = assumptions
    
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
    
    # Step 9: Save to database
    try:
        eval_id = database.save_evaluation(
            session_id=st.session_state.session_id,
            flow=flow,
            facts=facts.dict(),
            stats=stats.dict(),
            evaluation=evaluation.dict(),
            assumptions=assumptions
        )
        st.session_state.last_saved_id = eval_id
    except Exception as e:
        st.warning(f"Could not save evaluation: {e}")
    
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
    
    # Property Status & Pricing (for all flows)
    render_property_status_and_pricing(facts)
    
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


def render_history():
    """Render saved evaluations history."""
    
    if st.button("← Back to Home"):
        st.session_state.current_page = 'home'
        st.rerun()
    
    st.title("📚 Evaluation History")
    st.markdown("Review your previously saved property evaluations")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    try:
        evaluations = database.get_evaluations_by_session(st.session_state.session_id)
        
        if not evaluations:
            st.info("No saved evaluations yet. Evaluate a property to start building your history!")
            return
        
        # Display count and compare button
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{len(evaluations)} saved evaluation{'s' if len(evaluations) != 1 else ''}**")
        with col2:
            if len(evaluations) >= 2 and st.button("📊 Compare Properties", use_container_width=True):
                st.session_state.current_page = 'compare'
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Display evaluations
        for eval_data in evaluations:
            flow_icons = {'rent': '🔑', 'buy': '🏡', 'sell': '💰', 'investment': '📈'}
            icon = flow_icons.get(eval_data['flow'], '📄')
            
            with st.expander(f"{icon} {eval_data['address']} ({eval_data['flow'].title()}) - {eval_data['created_at'][:10]}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    eval_dict = eval_data['evaluation_data']
                    st.markdown(f"**Summary:** {eval_dict.get('summary', 'N/A')[:200]}...")
                    
                    if 'red_flags' in eval_dict and eval_dict['red_flags']:
                        st.markdown(f"**Red Flags:** {', '.join(eval_dict['red_flags'][:2])}")
                    
                    if 'green_flags' in eval_dict and eval_dict['green_flags']:
                        st.markdown(f"**Green Flags:** {', '.join(eval_dict['green_flags'][:2])}")
                
                with col2:
                    if st.button("🗑️ Delete", key=f"del_{eval_data['id']}"):
                        database.delete_evaluation(eval_data['id'], st.session_state.session_id)
                        st.rerun()
    
    except Exception as e:
        st.error(f"Error loading evaluations: {e}")


def render_compare():
    """Render side-by-side comparison of saved evaluations."""
    
    if st.button("← Back to History"):
        st.session_state.current_page = 'history'
        st.rerun()
    
    st.title("📊 Compare Properties")
    
    try:
        evaluations = database.get_evaluations_by_session(st.session_state.session_id)
        
        if len(evaluations) < 2:
            st.warning("You need at least 2 saved evaluations to compare. Evaluate more properties first!")
            return
        
        # Selection dropdowns
        col1, col2 = st.columns(2)
        
        with col1:
            options1 = [f"{e['address']} ({e['flow'].title()})" for e in evaluations]
            selected1 = st.selectbox("Property 1", options1, key="prop1")
            idx1 = options1.index(selected1) if selected1 else 0
            eval1 = evaluations[idx1]
        
        with col2:
            options2 = [f"{e['address']} ({e['flow'].title()})" for e in evaluations]
            selected2 = st.selectbox("Property 2", options2, index=min(1, len(options2)-1), key="prop2")
            idx2 = options2.index(selected2) if selected2 else 1
            eval2 = evaluations[idx2]
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Comparison table
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"### {eval1['address']}")
            st.markdown(f"**Flow:** {eval1['flow'].title()}")
            prop1 = eval1['property_data']
            st.markdown(f"**Price:** ${prop1.get('list_price', 'N/A'):,.0f}" if prop1.get('list_price') else "**Price:** N/A")
            st.markdown(f"**Beds/Baths:** {prop1.get('beds', 'N/A')}/{prop1.get('baths', 'N/A')}")
            st.markdown(f"**Size:** {prop1.get('sqft', 'N/A'):,} sqft" if prop1.get('sqft') else "**Size:** N/A")
        
        with col2:
            st.markdown(f"### {eval2['address']}")
            st.markdown(f"**Flow:** {eval2['flow'].title()}")
            prop2 = eval2['property_data']
            st.markdown(f"**Price:** ${prop2.get('list_price', 'N/A'):,.0f}" if prop2.get('list_price') else "**Price:** N/A")
            st.markdown(f"**Beds/Baths:** {prop2.get('beds', 'N/A')}/{prop2.get('baths', 'N/A')}")
            st.markdown(f"**Size:** {prop2.get('sqft', 'N/A'):,} sqft" if prop2.get('sqft') else "**Size:** N/A")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Evaluation summaries
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Evaluation Summary:**")
            st.info(eval1['evaluation_data'].get('summary', 'N/A'))
        
        with col2:
            st.markdown("**Evaluation Summary:**")
            st.info(eval2['evaluation_data'].get('summary', 'N/A'))
        
        # Flags comparison
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            flags1 = eval1['evaluation_data']
            if flags1.get('red_flags'):
                st.markdown("**⚠️ Red Flags:**")
                for flag in flags1['red_flags']:
                    st.markdown(f"• {flag}")
            if flags1.get('green_flags'):
                st.markdown("**✅ Green Flags:**")
                for flag in flags1['green_flags']:
                    st.markdown(f"• {flag}")
        
        with col2:
            flags2 = eval2['evaluation_data']
            if flags2.get('red_flags'):
                st.markdown("**⚠️ Red Flags:**")
                for flag in flags2['red_flags']:
                    st.markdown(f"• {flag}")
            if flags2.get('green_flags'):
                st.markdown("**✅ Green Flags:**")
                for flag in flags2['green_flags']:
                    st.markdown(f"• {flag}")
    
    except Exception as e:
        st.error(f"Error loading comparison: {e}")


if __name__ == "__main__":
    main()
