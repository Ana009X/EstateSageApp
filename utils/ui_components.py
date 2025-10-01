import streamlit as st


def render_status_bar(value: str, labels: list | None = None, title: str = ""):
    """Render a horizontal status bar with low/normal/high segments."""
    
    if labels is None:
        labels = ["Low", "Normal", "High"]
    
    # Map value to position
    position_map = {
        'low': 0,
        'normal': 1,
        'high': 2,
        'underpriced': 0,
        'average': 1,
        'overpriced': 2
    }
    
    position = position_map.get(value.lower(), 1)
    
    # Colors for each segment
    colors = {
        0: "#10b981",  # Green
        1: "#f59e0b",  # Amber
        2: "#ef4444"   # Red
    }
    
    if title:
        st.markdown(f"**{title}**")
    
    # Create bar using columns
    cols = st.columns(3)
    
    for idx, label in enumerate(labels):
        with cols[idx]:
            if idx == position:
                st.markdown(
                    f'<div style="background-color: {colors[idx]}; color: white; padding: 8px; '
                    f'border-radius: 4px; text-align: center; font-weight: 600;">{label}</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div style="background-color: #e5e7eb; color: #6b7280; padding: 8px; '
                    f'border-radius: 4px; text-align: center;">{label}</div>',
                    unsafe_allow_html=True
                )


def render_flags(red_flags: list, green_flags: list):
    """Render red and green flag badges."""
    
    col1, col2 = st.columns(2)
    
    with col1:
        if red_flags:
            st.markdown("**⚠️ Red Flags**")
            for flag in red_flags[:4]:
                st.markdown(
                    f'<div style="background-color: #fee2e2; color: #991b1b; padding: 6px 12px; '
                    f'border-radius: 9999px; margin: 4px 0; display: inline-block; font-size: 0.875rem;">'
                    f'{flag}</div>',
                    unsafe_allow_html=True
                )
    
    with col2:
        if green_flags:
            st.markdown("**✅ Green Flags**")
            for flag in green_flags[:4]:
                st.markdown(
                    f'<div style="background-color: #d1fae5; color: #065f46; padding: 6px 12px; '
                    f'border-radius: 9999px; margin: 4px 0; display: inline-block; font-size: 0.875rem;">'
                    f'{flag}</div>',
                    unsafe_allow_html=True
                )


def render_metric_card(label: str, value: str, delta: str | None = None):
    """Render a metric card."""
    
    st.metric(label=label, value=value, delta=delta)


def render_property_status_and_pricing(facts):
    """Render prominent property status and pricing information."""
    
    st.markdown("### 🏷️ Property Status & Pricing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Status**")
        if facts.status:
            status_colors = {
                'active': '#10b981',
                'pending': '#3b82f6',
                'sold': '#6b7280',
                'off_market': '#f59e0b'
            }
            status_labels = {
                'active': '🟢 Active',
                'pending': '🔵 Pending',
                'sold': '⚫ Sold',
                'off_market': '🟠 Off Market'
            }
            status_label = status_labels.get(facts.status, facts.status.replace('_', ' ').title())
            color = status_colors.get(facts.status, '#6b7280')
            st.markdown(
                f'<div style="background-color: {color}; color: white; padding: 12px 20px; '
                f'border-radius: 8px; font-size: 1.1rem; font-weight: 600; text-align: center;">'
                f'{status_label}</div>',
                unsafe_allow_html=True
            )
            
            # Show data source and freshness
            if facts.data_source or facts.data_updated:
                source_info = []
                if facts.data_source:
                    source_label = 'RentCast' if facts.data_source == 'rentcast' else facts.data_source.title()
                    source_info.append(f"Source: {source_label}")
                if facts.data_updated:
                    source_info.append(f"Updated: {facts.data_updated}")
                st.caption(" | ".join(source_info))
        else:
            st.markdown(
                '<div style="background-color: #e5e7eb; color: #6b7280; padding: 12px 20px; '
                'border-radius: 8px; font-size: 1.1rem; text-align: center;">Status Unknown</div>',
                unsafe_allow_html=True
            )
    
    with col2:
        st.markdown("**Pricing Information**")
        price_box_items = []
        
        if facts.active_price:
            price_box_items.append(f"**Active Price:** ${facts.active_price:,.0f}")
        
        if facts.sold_price:
            price_box_items.append(f"**Sold Price:** ${facts.sold_price:,.0f}")
        
        if facts.last_listed_price and facts.last_listed_price != facts.active_price:
            price_box_items.append(f"**Last Listed:** ${facts.last_listed_price:,.0f}")
        
        if not price_box_items and facts.list_price:
            price_box_items.append(f"**List Price:** ${facts.list_price:,.0f}")
        
        if price_box_items:
            price_text = "<br>".join(price_box_items)
            st.markdown(
                f'<div style="background-color: #f3f4f6; padding: 12px 20px; border-radius: 8px;">'
                f'{price_text}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div style="background-color: #f3f4f6; color: #6b7280; padding: 12px 20px; '
                'border-radius: 8px;">Price information not available</div>',
                unsafe_allow_html=True
            )
    
    st.markdown("<br>", unsafe_allow_html=True)


def render_property_header(facts, photo_url: str | None = None):
    """Render property header with photo and key details."""
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if photo_url:
            st.image(photo_url, use_container_width=True)
        else:
            # Placeholder
            st.markdown(
                '<div style="background-color: #e5e7eb; height: 200px; display: flex; '
                'align-items: center; justify-content: center; border-radius: 8px;">'
                '<span style="color: #6b7280;">No Photo</span></div>',
                unsafe_allow_html=True
            )
    
    with col2:
        st.markdown(f"### {facts.address}")
        
        # Status badge
        if facts.status:
            status_colors = {
                'active': '#10b981',
                'sold': '#6b7280',
                'off_market': '#f59e0b'
            }
            status_label = facts.status.replace('_', ' ').title()
            color = status_colors.get(facts.status, '#6b7280')
            st.markdown(
                f'<span style="background-color: {color}; color: white; padding: 4px 12px; '
                f'border-radius: 12px; font-size: 0.875rem; font-weight: 600;">{status_label}</span>',
                unsafe_allow_html=True
            )
            st.markdown("<br>", unsafe_allow_html=True)
        
        details = []
        if facts.beds:
            details.append(f"{facts.beds} bed")
        if facts.baths:
            details.append(f"{facts.baths} bath")
        if facts.sqft:
            details.append(f"{facts.sqft:,} sqft")
        
        if details:
            st.markdown(" • ".join(details))
        
        # Price information
        price_info = []
        if facts.active_price:
            price_info.append(f"**Active Price:** ${facts.active_price:,.0f}")
        if facts.sold_price:
            price_info.append(f"**Sold Price:** ${facts.sold_price:,.0f}")
        if facts.last_listed_price and facts.last_listed_price != facts.active_price:
            price_info.append(f"**Last Listed:** ${facts.last_listed_price:,.0f}")
        if not price_info and facts.list_price:
            price_info.append(f"**Price:** ${facts.list_price:,.0f}")
        
        if price_info:
            st.markdown(" | ".join(price_info))
        
        if facts.days_on_market:
            st.caption(f"Days on Market: {facts.days_on_market}")
