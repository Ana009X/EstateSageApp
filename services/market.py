from models import PropertyFacts, MarketStats
from typing import List, Dict
from datetime import datetime, timedelta
import random


def get_comps(facts: PropertyFacts, radius_km: float = 1.5, lookback_days: int = 120) -> List[Dict]:
    """
    Get comparable properties.
    First tries RentCast API, then falls back to mock data.
    
    Returns list of comparable properties with: price, price_per_sqft, status, beds, baths, sqft
    """
    
    # Try RentCast first
    try:
        from services.rentcast import get_comparable_sales
        comps = get_comparable_sales(facts.address)
        if comps and len(comps) > 0:
            return comps
    except Exception as e:
        print(f"RentCast comps error: {e}")
    
    # Fallback to mock comparable properties
    if not facts.list_price:
        base_price = 500000
    else:
        base_price = facts.list_price
    
    comps = []
    for i in range(8):
        price_variance = random.uniform(0.85, 1.15)
        comp_price = base_price * price_variance
        comp_sqft = facts.sqft if facts.sqft else random.randint(1200, 2500)
        
        comps.append({
            'price': comp_price,
            'price_per_sqft': comp_price / comp_sqft,
            'status': random.choice(['sold', 'sold', 'sold', 'active']),
            'beds': facts.beds if facts.beds else random.choice([2, 3, 4]),
            'baths': facts.baths if facts.baths else random.choice([1.5, 2, 2.5]),
            'sqft': comp_sqft,
            'days_ago': random.randint(0, lookback_days)
        })
    
    return comps


def fetch_area_stats(lat: float, lon: float, city: str | None = None) -> MarketStats:
    """
    Fetch market statistics for an area.
    First tries RentCast API, then falls back to mock data.
    """
    
    # Try RentCast first
    try:
        from services.rentcast import get_market_stats_by_location
        stats = get_market_stats_by_location(lat, lon, city)
        if stats:
            return stats
    except Exception as e:
        print(f"RentCast market stats error: {e}")
    
    # Fallback to mock market statistics
    median_price = random.randint(450000, 750000)
    
    return MarketStats(
        neighborhood=city or "Downtown",
        city=city or "San Francisco",
        median_list_price=median_price,
        median_sold_price=median_price * 0.98,
        price_per_sqft_median=random.randint(400, 600),
        active_listings=random.randint(25, 150),
        sold_last_90d=random.randint(40, 180),
        dom_median=random.randint(15, 45),
        supply_to_demand_ratio=random.uniform(0.5, 8.0),
        price_trend_12m_pct=random.uniform(-3.5, 12.0),
        price_trend_5y_pct=random.uniform(8.0, 45.0)
    )


def calculate_price_position(subject_price: float, comps: List[Dict]) -> str:
    """Calculate if property is underpriced, average, or overpriced vs comps."""
    
    if not comps:
        return "normal"
    
    comp_prices = [c['price'] for c in comps if c['status'] == 'sold']
    if not comp_prices:
        comp_prices = [c['price'] for c in comps]
    
    comp_prices.sort()
    median_idx = len(comp_prices) // 2
    median_price = comp_prices[median_idx]
    
    q1_idx = len(comp_prices) // 4
    q3_idx = (3 * len(comp_prices)) // 4
    
    if subject_price < comp_prices[q1_idx]:
        return "low"
    elif subject_price > comp_prices[q3_idx]:
        return "high"
    else:
        return "normal"


def calculate_demand_supply_index(stats: MarketStats) -> str:
    """Calculate demand vs supply indicator."""
    
    if not stats.active_listings or not stats.sold_last_90d:
        return "normal"
    
    dsi = stats.active_listings / max(stats.sold_last_90d, 1)
    
    if dsi < 3:
        return "high"  # Tight demand
    elif dsi > 6:
        return "low"  # Loose market
    else:
        return "normal"
