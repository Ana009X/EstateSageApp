from models import PropertyFacts, MarketStats
from typing import Dict, Any, List
from datetime import datetime
import random


DEFAULT_INTEREST_RATE = 0.07  # 7% annual
DEFAULT_DOWN_PAYMENT_PCT = 0.20  # 20%
DEFAULT_LOAN_TERM_YEARS = 30


def estimate_rent(facts: PropertyFacts, comps: List[Dict]) -> float:
    """
    Estimate fair market rent based on property facts and comparables.
    
    TODO: Integrate with rental data providers:
    - Zillow Rental Manager API
    - Rentometer API
    - Local MLS rental data
    """
    
    # Simple estimation based on price or square footage
    if facts.rent_estimate:
        return facts.rent_estimate
    
    if facts.list_price:
        # Rule of thumb: 0.8-1.1% of property value per month
        return facts.list_price * 0.009
    
    if facts.sqft:
        # Estimate $1.50-$2.50 per sqft per month (varies by market)
        return facts.sqft * 2.0
    
    return 2500.0  # Default fallback


def calculate_monthly_payment(
    purchase_price: float,
    down_payment_pct: float = DEFAULT_DOWN_PAYMENT_PCT,
    interest_rate: float = DEFAULT_INTEREST_RATE,
    loan_term_years: int = DEFAULT_LOAN_TERM_YEARS,
    taxes_annual: float = 0,
    hoa_monthly: float = 0,
    insurance_annual: float = 0
) -> Dict[str, float]:
    """Calculate monthly mortgage payment with PITI."""
    
    down_payment = purchase_price * down_payment_pct
    loan_amount = purchase_price - down_payment
    
    # Monthly interest rate
    monthly_rate = interest_rate / 12
    num_payments = loan_term_years * 12
    
    # Mortgage payment formula: M = P[r(1+r)^n]/[(1+r)^n-1]
    if monthly_rate > 0:
        mortgage_payment = loan_amount * (
            monthly_rate * (1 + monthly_rate) ** num_payments
        ) / ((1 + monthly_rate) ** num_payments - 1)
    else:
        mortgage_payment = loan_amount / num_payments
    
    # Add property tax, insurance, HOA
    monthly_tax = taxes_annual / 12 if taxes_annual else purchase_price * 0.012 / 12  # 1.2% annual default
    monthly_insurance = insurance_annual / 12 if insurance_annual else purchase_price * 0.006 / 12  # 0.6% annual default
    monthly_hoa = hoa_monthly or 0
    
    total_monthly = mortgage_payment + monthly_tax + monthly_insurance + monthly_hoa
    
    return {
        'mortgage_payment': mortgage_payment,
        'property_tax': monthly_tax,
        'insurance': monthly_insurance,
        'hoa': monthly_hoa,
        'total_monthly': total_monthly,
        'down_payment': down_payment,
        'loan_amount': loan_amount
    }


def calculate_investment_metrics(
    purchase_price: float,
    monthly_rent: float,
    taxes_annual: float = 0,
    hoa_monthly: float = 0,
    down_payment_pct: float = 0.25,
    interest_rate: float = DEFAULT_INTEREST_RATE,
    loan_term_years: int = DEFAULT_LOAN_TERM_YEARS
) -> Dict[str, Any]:
    """Calculate NOI, Cap Rate, Cash-on-Cash return for investment properties."""
    
    # Annual rental income
    annual_rent = monthly_rent * 12
    
    # Operating expenses
    insurance_annual = purchase_price * 0.006  # 0.6% of property value
    maintenance_annual = annual_rent * 0.08  # 8% of rent
    vacancy_annual = annual_rent * 0.05  # 5% vacancy
    management_annual = annual_rent * 0.08  # 8% property management
    taxes_annual = taxes_annual or purchase_price * 0.012  # 1.2% default
    hoa_annual = hoa_monthly * 12
    
    total_operating_expenses = (
        insurance_annual +
        maintenance_annual +
        vacancy_annual +
        management_annual +
        taxes_annual +
        hoa_annual
    )
    
    # Net Operating Income
    noi = annual_rent - total_operating_expenses
    monthly_noi = noi / 12
    
    # Cap Rate = NOI / Purchase Price
    cap_rate = (noi / purchase_price * 100) if purchase_price > 0 else 0
    
    # Cash-on-Cash calculation
    payment_info = calculate_monthly_payment(
        purchase_price,
        down_payment_pct,
        interest_rate,
        loan_term_years,
        taxes_annual,
        hoa_monthly,
        insurance_annual
    )
    
    annual_debt_service = payment_info['mortgage_payment'] * 12
    cash_invested = payment_info['down_payment']
    
    annual_cash_flow = noi - annual_debt_service
    cash_on_cash = (annual_cash_flow / cash_invested * 100) if cash_invested > 0 else 0
    
    return {
        'annual_rent': annual_rent,
        'operating_expenses': {
            'insurance': insurance_annual,
            'maintenance': maintenance_annual,
            'vacancy': vacancy_annual,
            'management': management_annual,
            'taxes': taxes_annual,
            'hoa': hoa_annual,
            'total': total_operating_expenses
        },
        'noi': noi,
        'monthly_noi': monthly_noi,
        'cap_rate': cap_rate,
        'cash_on_cash': cash_on_cash,
        'annual_cash_flow': annual_cash_flow,
        'cash_invested': cash_invested,
        'monthly_payment': payment_info['total_monthly']
    }


def calculate_suggested_list_price(
    facts: PropertyFacts,
    stats: MarketStats,
    comps: List[Dict]
) -> Dict[str, Any]:
    """Calculate suggested list price for sellers with seasonal adjustment."""
    
    # Get current month for seasonal adjustment
    current_month = datetime.now().month
    
    # Seasonal adjustments
    if current_month in [11, 12, 1, 2]:  # Nov-Feb: slower season
        seasonal_factor = 0.985  # -1.5%
    elif current_month in [3, 4, 5, 6]:  # Mar-Jun: peak season
        seasonal_factor = 1.015  # +1.5%
    else:
        seasonal_factor = 1.0
    
    # Calculate base price from comps
    if comps:
        recent_sold = [c for c in comps if c['status'] == 'sold' and c['days_ago'] <= 90]
        if recent_sold:
            avg_sold_price = sum(c['price'] for c in recent_sold) / len(recent_sold)
        else:
            avg_sold_price = sum(c['price'] for c in comps) / len(comps)
    else:
        avg_sold_price = stats.median_sold_price or facts.list_price or 500000
    
    # Apply seasonal adjustment
    suggested_price = avg_sold_price * seasonal_factor
    
    # Reasoning bullets
    reasons = []
    if seasonal_factor > 1:
        reasons.append("Peak selling season - market favors sellers")
    elif seasonal_factor < 1:
        reasons.append("Off-season pricing to attract serious buyers")
    
    if stats.supply_to_demand_ratio and stats.supply_to_demand_ratio < 3:
        reasons.append("Low inventory creates pricing power")
    elif stats.supply_to_demand_ratio and stats.supply_to_demand_ratio > 6:
        reasons.append("High inventory suggests competitive pricing needed")
    
    return {
        'suggested_price': suggested_price,
        'price_range_low': suggested_price * 0.97,
        'price_range_high': suggested_price * 1.03,
        'seasonal_factor': seasonal_factor,
        'reasons': reasons
    }


def analyze_condition(facts: PropertyFacts) -> str:
    """Estimate property condition from description and year built."""
    
    description = (facts.description or "").lower()
    
    # Keyword analysis
    positive_keywords = ['updated', 'renovated', 'remodeled', 'modern', 'new', 'pristine', 'immaculate']
    negative_keywords = ['original', 'needs tlc', 'fixer', 'potential', 'investor special', 'as-is']
    
    positive_count = sum(1 for kw in positive_keywords if kw in description)
    negative_count = sum(1 for kw in negative_keywords if kw in description)
    
    if positive_count > negative_count and positive_count > 0:
        return "Updated/Renovated"
    elif negative_count > 0:
        return "Original/Needs Work"
    elif facts.year_built and facts.year_built > 2010:
        return "Modern/Like New"
    elif facts.year_built and facts.year_built < 1980:
        return "Older/Character Home"
    else:
        return "Average Condition"
