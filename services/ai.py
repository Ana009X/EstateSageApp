import os
import json
from typing import Dict, Any
from openai import OpenAI


def ai_summarize(flow: str, payload: Dict[str, Any]) -> str:
    """
    Generate AI summary using OpenAI if API key is available.
    Falls back to heuristic-based summary otherwise.
    
    The newest OpenAI model is "gpt-5" which was released August 7, 2025.
    Do not change this unless explicitly requested by the user.
    """
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        return _heuristic_summary(flow, payload)
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Build context from payload
        context = _build_context(flow, payload)
        
        system_prompt = f"""You are a real estate expert providing insights for a {flow} evaluation. 
Provide a concise, actionable 4-6 sentence summary that helps the user make an informed decision.
Focus on key factors like pricing, market conditions, financial viability, and notable risks or opportunities.
Be professional but conversational. Respond in JSON format with a 'summary' field."""

        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context}
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if content:
            result = json.loads(content)
            return result.get('summary', _heuristic_summary(flow, payload))
        return _heuristic_summary(flow, payload)
        
    except Exception as e:
        # Fallback to heuristic summary on any error
        return _heuristic_summary(flow, payload)


def _build_context(flow: str, payload: Dict[str, Any]) -> str:
    """Build context string from payload for AI."""
    
    facts = payload.get('facts', {})
    stats = payload.get('stats', {})
    metrics = payload.get('metrics', {})
    
    context_parts = [f"Flow: {flow}"]
    
    if facts:
        context_parts.append(f"Property: {facts.get('address', 'Unknown')}")
        if facts.get('list_price'):
            context_parts.append(f"Price: ${facts['list_price']:,.0f}")
        if facts.get('beds') and facts.get('baths'):
            context_parts.append(f"{facts['beds']} bed, {facts['baths']} bath")
        if facts.get('sqft'):
            context_parts.append(f"{facts['sqft']} sqft")
    
    if stats:
        if stats.get('median_list_price'):
            context_parts.append(f"Area median: ${stats['median_list_price']:,.0f}")
        if stats.get('dom_median'):
            context_parts.append(f"Median DOM: {stats['dom_median']} days")
        if stats.get('price_trend_12m_pct'):
            context_parts.append(f"1yr trend: {stats['price_trend_12m_pct']:+.1f}%")
    
    if metrics:
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                context_parts.append(f"{key}: {value}")
            elif isinstance(value, str):
                context_parts.append(f"{key}: {value}")
    
    return " | ".join(context_parts)


def _heuristic_summary(flow: str, payload: Dict[str, Any]) -> str:
    """Generate rule-based summary when AI is not available."""
    
    facts = payload.get('facts', {})
    stats = payload.get('stats', {})
    price_position = payload.get('price_position', 'normal')
    demand_supply = payload.get('demand_supply', 'normal')
    
    summaries = {
        'rent': _rent_heuristic(facts, stats, price_position, demand_supply),
        'buy': _buy_heuristic(facts, stats, price_position, demand_supply),
        'sell': _sell_heuristic(facts, stats, price_position, demand_supply),
        'investment': _investment_heuristic(facts, stats, payload.get('metrics', {}))
    }
    
    return summaries.get(flow, "Property evaluation complete. Review the metrics below for detailed insights.")


def _rent_heuristic(facts, stats, price_pos, demand_supply):
    price_desc = {"low": "below market", "normal": "fairly priced", "high": "above market"}[price_pos]
    demand_desc = {"low": "soft", "normal": "balanced", "high": "strong"}[demand_supply]
    
    return f"This rental property appears {price_desc} compared to similar units in the area. " \
           f"The local rental market shows {demand_desc} demand. " \
           f"With median days on market at {stats.get('dom_median', 'N/A')} days, " \
           f"rental opportunities in this neighborhood are moving at a {'quick' if demand_supply == 'high' else 'moderate'} pace. " \
           f"Consider negotiating if pricing seems high relative to market conditions."


def _buy_heuristic(facts, stats, price_pos, demand_supply):
    price_desc = {"low": "underpriced", "normal": "market-rate", "high": "premium-priced"}[price_pos]
    
    trend = stats.get('price_trend_12m_pct', 0) or 0
    trend_desc = "appreciating" if trend > 3 else "stable" if trend > -2 else "softening"
    
    market_type = "competitive buyer's" if demand_supply == 'low' else 'balanced' if demand_supply == 'normal' else "seller's"
    action_word = 'decisively' if demand_supply == 'high' else 'thoughtfully'
    
    return f"This property is {price_desc} relative to comparable sales in the area. " \
           f"The market is currently {trend_desc} with a {trend:+.1f}% price change over the past year. " \
           f"Local inventory levels suggest a {market_type} market. " \
           f"Act {action_word} based on your timeline and budget constraints."


def _sell_heuristic(facts, stats, price_pos, demand_supply):
    market_desc = {"low": "buyer-friendly", "normal": "balanced", "high": "seller-friendly"}[demand_supply]
    
    return f"Current market conditions are {market_desc} with {stats.get('active_listings', 'N/A')} active listings " \
           f"and {stats.get('sold_last_90d', 'N/A')} sales in the past 90 days. " \
           f"Properties are averaging {stats.get('dom_median', 'N/A')} days on market. " \
           f"Price strategically to {'attract multiple offers' if demand_supply == 'high' else 'remain competitive' if demand_supply == 'normal' else 'generate buyer interest'}. " \
           f"Consider seasonal timing and current inventory levels when setting your list price."


def _investment_heuristic(facts, stats, metrics):
    cap_rate = metrics.get('cap_rate') or 0
    coc = metrics.get('cash_on_cash') or 0
    monthly_noi = metrics.get('monthly_noi') or 0
    price_trend_5y = stats.get('price_trend_5y_pct') or 0
    
    cap_quality = "strong" if cap_rate > 7 else "moderate" if cap_rate > 5 else "modest"
    
    return f"This investment opportunity shows a {cap_quality} {cap_rate:.1f}% cap rate " \
           f"with a {coc:.1f}% cash-on-cash return. " \
           f"Monthly NOI of ${monthly_noi:,.0f} suggests " \
           f"{'positive' if monthly_noi > 0 else 'challenging'} cash flow potential. " \
           f"Consider operating expense ratios and local vacancy trends when finalizing your analysis. " \
           f"Long-term appreciation in this market has been {price_trend_5y:.1f}% over 5 years."
