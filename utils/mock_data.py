from models import PropertyFacts, MarketStats
from datetime import datetime, timedelta
import random


def generate_mock_property_facts(address: str | None = None, flow: str = "buy") -> PropertyFacts:
    """Generate mock property facts for testing."""
    
    base_price = random.randint(400000, 900000)
    
    return PropertyFacts(
        address=address or "123 Main Street, San Francisco, CA 94102",
        lat=37.7749 + random.uniform(-0.05, 0.05),
        lon=-122.4194 + random.uniform(-0.05, 0.05),
        beds=random.choice([2, 3, 4]),
        baths=random.choice([1.5, 2, 2.5, 3]),
        sqft=random.randint(1200, 2800),
        year_built=random.randint(1960, 2020),
        lot_size_sqft=random.randint(3000, 8000),
        property_type=random.choice(["Single Family", "Condo", "Townhouse"]),
        photos=["https://via.placeholder.com/400x300"],
        description="Charming property with updated kitchen and original hardwood floors. Great neighborhood with parks nearby.",
        hoa_monthly=random.choice([0, 200, 350, 500]),
        taxes_annual=base_price * 0.012,
        list_price=base_price,
        rent_estimate=base_price * 0.009,
        days_on_market=random.randint(5, 60),
        last_sold_price=base_price * random.uniform(0.85, 0.95),
        last_sold_date=datetime.now().date() - timedelta(days=random.randint(365, 1825))
    )


def generate_flags(facts: PropertyFacts, stats: MarketStats, price_position: str, demand_supply: str):
    """Generate red and green flags based on property analysis."""
    
    red_flags = []
    green_flags = []
    
    # Price-based flags
    if price_position == 'high':
        red_flags.append("Priced above market average")
    elif price_position == 'low':
        green_flags.append("Below market value - potential deal")
    
    # Market condition flags
    if demand_supply == 'low':
        red_flags.append("High inventory - buyer's market")
    elif demand_supply == 'high':
        green_flags.append("Low inventory - competitive market")
    
    # Days on market
    if facts.days_on_market and facts.days_on_market > 60:
        red_flags.append(f"Long time on market ({facts.days_on_market} days)")
    elif facts.days_on_market and facts.days_on_market < 15:
        green_flags.append("Recently listed - move quickly")
    
    # Price trends
    if stats.price_trend_12m_pct and stats.price_trend_12m_pct > 5:
        green_flags.append(f"Strong appreciation (+{stats.price_trend_12m_pct:.1f}% 1yr)")
    elif stats.price_trend_12m_pct and stats.price_trend_12m_pct < -2:
        red_flags.append(f"Declining prices ({stats.price_trend_12m_pct:.1f}% 1yr)")
    
    # HOA
    if facts.hoa_monthly and facts.hoa_monthly > 500:
        red_flags.append(f"High HOA fees (${facts.hoa_monthly:,.0f}/mo)")
    elif facts.hoa_monthly and facts.hoa_monthly < 200:
        green_flags.append("Reasonable HOA fees")
    
    # Property age and condition
    if facts.year_built and facts.year_built > 2015:
        green_flags.append("Modern construction")
    elif facts.year_built and facts.year_built < 1970:
        red_flags.append("Older property - may need updates")
    
    # Ensure we have 2-4 of each
    return red_flags[:4], green_flags[:4]
