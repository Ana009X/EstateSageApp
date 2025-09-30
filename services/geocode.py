from typing import Tuple, Optional
from models import PropertyFacts
import requests
import logging
import os

logger = logging.getLogger(__name__)


def geocode_address(address: str) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """
    Geocode an address to lat/lon and neighborhood using OpenStreetMap Nominatim (free).
    
    Returns: (latitude, longitude, neighborhood_name)
    """
    
    try:
        # Use OpenStreetMap Nominatim (free, no API key required)
        headers = {
            'User-Agent': 'RealEstateEvaluator/1.0'
        }
        
        response = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params={
                'q': address,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            },
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                result = data[0]
                lat = float(result.get('lat'))
                lon = float(result.get('lon'))
                
                # Extract neighborhood/city
                address_parts = result.get('address', {})
                neighborhood = (
                    address_parts.get('neighbourhood') or
                    address_parts.get('suburb') or
                    address_parts.get('city') or
                    address_parts.get('town')
                )
                
                return (lat, lon, neighborhood)
    
    except Exception as e:
        logger.warning(f"Geocoding error for address {address}: {e}")
    
    # Fallback: simple city/state extraction for mock neighborhood
    parts = address.split(',')
    neighborhood = parts[-2].strip() if len(parts) >= 2 else None
    
    # Return mock coordinates as fallback
    return (37.7749, -122.4194, neighborhood)


def lookup_property_facts(address: str) -> PropertyFacts:
    """
    Lookup property facts from address.
    First tries RentCast API, then falls back to geocoding only.
    """
    
    # Try RentCast first
    try:
        from services.rentcast import get_property_by_address
        facts = get_property_by_address(address)
        if facts:
            return facts
    except Exception as e:
        logger.warning(f"RentCast lookup error for address {address}: {e}")
    
    # Fallback to basic geocoding
    lat, lon, neighborhood = geocode_address(address)
    
    return PropertyFacts(
        address=address,
        lat=lat,
        lon=lon
    )
