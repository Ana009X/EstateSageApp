import os
import requests
from typing import Optional, Dict, Any, List
from models import PropertyFacts, MarketStats
from datetime import datetime


RENTCAST_API_KEY = os.getenv('RENTCAST_API_KEY')
RENTCAST_BASE_URL = "https://api.rentcast.io/v1"


def get_property_by_address(address: str) -> Optional[PropertyFacts]:
    """
    Fetch property data from RentCast API by address.
    
    Returns PropertyFacts with real data if API key exists, None otherwise.
    """
    
    if not RENTCAST_API_KEY:
        return None
    
    try:
        headers = {
            'X-Api-Key': RENTCAST_API_KEY,
            'Accept': 'application/json'
        }
        
        # Get property records
        response = requests.get(
            f"{RENTCAST_BASE_URL}/properties",
            headers=headers,
            params={'address': address},
            timeout=10
        )
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        if not data:
            return None
        
        # Extract property data
        prop = data[0] if isinstance(data, list) else data
        
        # Parse last sold date
        last_sold_date = None
        if prop.get('lastSaleDate'):
            try:
                last_sold_date = datetime.strptime(prop['lastSaleDate'], '%Y-%m-%d').date()
            except:
                pass
        
        # Determine status and prices
        status = 'active' if prop.get('listingStatus') == 'Active' else 'off_market'
        active_price = prop.get('price') if status == 'active' else None
        sold_price = prop.get('lastSalePrice')
        list_price = active_price or sold_price
        
        return PropertyFacts(
            address=prop.get('formattedAddress', address),
            lat=prop.get('latitude'),
            lon=prop.get('longitude'),
            beds=prop.get('bedrooms'),
            baths=prop.get('bathrooms'),
            sqft=prop.get('squareFootage'),
            year_built=prop.get('yearBuilt'),
            lot_size_sqft=prop.get('lotSize'),
            property_type=prop.get('propertyType', 'Unknown'),
            description=prop.get('description', ''),
            hoa_monthly=prop.get('hoaFee'),
            taxes_annual=prop.get('taxAssessedValue', 0) * 0.012 if prop.get('taxAssessedValue') else None,
            list_price=list_price,
            rent_estimate=prop.get('rentEstimate'),
            days_on_market=prop.get('daysOnMarket'),
            last_sold_price=sold_price,
            last_sold_date=last_sold_date,
            status=status,
            active_price=active_price,
            sold_price=sold_price,
            last_listed_price=prop.get('lastListPrice')
        )
        
    except Exception as e:
        print(f"RentCast API error: {e}")
        return None


def get_market_stats_by_location(lat: float, lon: float, city: str = None) -> Optional[MarketStats]:
    """
    Fetch market statistics from RentCast API by location.
    """
    
    if not RENTCAST_API_KEY:
        return None
    
    try:
        headers = {
            'X-Api-Key': RENTCAST_API_KEY,
            'Accept': 'application/json'
        }
        
        # Get market statistics
        response = requests.get(
            f"{RENTCAST_BASE_URL}/markets",
            headers=headers,
            params={
                'latitude': lat,
                'longitude': lon
            },
            timeout=10
        )
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        if not data:
            return None
        
        market = data[0] if isinstance(data, list) else data
        
        # Calculate supply/demand ratio
        active_listings = market.get('activeListings', 0)
        sold_last_90d = market.get('soldLast90Days', 0)
        supply_demand_ratio = active_listings / max(sold_last_90d, 1) if sold_last_90d > 0 else None
        
        return MarketStats(
            neighborhood=market.get('neighborhood') or city,
            city=market.get('city') or city,
            median_list_price=market.get('medianListPrice'),
            median_sold_price=market.get('medianSoldPrice'),
            price_per_sqft_median=market.get('medianPricePerSqFt'),
            active_listings=active_listings,
            sold_last_90d=sold_last_90d,
            dom_median=market.get('medianDaysOnMarket'),
            supply_to_demand_ratio=supply_demand_ratio,
            price_trend_12m_pct=market.get('priceChange12Month'),
            price_trend_5y_pct=market.get('priceChange5Year')
        )
        
    except Exception as e:
        print(f"RentCast market stats error: {e}")
        return None


def get_comparable_sales(address: str, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch comparable sales from RentCast API.
    """
    
    if not RENTCAST_API_KEY:
        return None
    
    try:
        headers = {
            'X-Api-Key': RENTCAST_API_KEY,
            'Accept': 'application/json'
        }
        
        # Get comparable properties
        response = requests.get(
            f"{RENTCAST_BASE_URL}/properties/comps",
            headers=headers,
            params={
                'address': address,
                'limit': limit
            },
            timeout=10
        )
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        if not data:
            return None
        
        comps = []
        for comp in data:
            comp_price = comp.get('lastSalePrice') or comp.get('price', 0)
            comp_sqft = comp.get('squareFootage', 1)
            
            # Calculate days ago from sale date
            days_ago = 0
            if comp.get('lastSaleDate'):
                try:
                    sale_date = datetime.strptime(comp['lastSaleDate'], '%Y-%m-%d')
                    days_ago = (datetime.now() - sale_date).days
                except:
                    pass
            
            comps.append({
                'price': comp_price,
                'price_per_sqft': comp_price / comp_sqft if comp_sqft > 0 else 0,
                'status': 'sold' if comp.get('lastSalePrice') else 'active',
                'beds': comp.get('bedrooms'),
                'baths': comp.get('bathrooms'),
                'sqft': comp_sqft,
                'days_ago': days_ago,
                'address': comp.get('formattedAddress')
            })
        
        return comps
        
    except Exception as e:
        print(f"RentCast comps error: {e}")
        return None
