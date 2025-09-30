from pydantic import BaseModel, HttpUrl
from typing import Optional, Literal
from datetime import date


class PropertyInput(BaseModel):
    url: Optional[HttpUrl] = None
    address: Optional[str] = None
    flow: Literal["rent", "buy", "sell", "investment"]


class PropertyFacts(BaseModel):
    address: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    beds: Optional[float] = None
    baths: Optional[float] = None
    sqft: Optional[int] = None
    year_built: Optional[int] = None
    lot_size_sqft: Optional[int] = None
    property_type: Optional[str] = None
    photos: list[str] = []
    description: Optional[str] = None
    hoa_monthly: Optional[float] = None
    taxes_annual: Optional[float] = None
    list_price: Optional[float] = None
    rent_estimate: Optional[float] = None
    days_on_market: Optional[int] = None
    last_sold_price: Optional[float] = None
    last_sold_date: Optional[date] = None


class MarketStats(BaseModel):
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    median_list_price: Optional[float] = None
    median_sold_price: Optional[float] = None
    price_per_sqft_median: Optional[float] = None
    active_listings: Optional[int] = None
    sold_last_90d: Optional[int] = None
    dom_median: Optional[int] = None
    supply_to_demand_ratio: Optional[float] = None  # >1 = more supply than demand
    price_trend_12m_pct: Optional[float] = None  # % change last 12 months
    price_trend_5y_pct: Optional[float] = None


class Evaluation(BaseModel):
    summary: str
    bars: dict  # {'price_position': 'low|normal|high', 'demand_vs_supply': 'low|normal|high', ...}
    red_flags: list[str]
    green_flags: list[str]
    details: dict  # flow-specific details/metrics
