import streamlit as st


def render_status_bar(value: str, labels: list = None, title: str = ""):
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


def render_metric_card(label: str, value: str, delta: str = None):
    """Render a metric card."""
    
    st.metric(label=label, value=value, delta=delta)


def render_property_header(facts, photo_url: str = None):
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
        
        details = []
        if facts.beds:
            details.append(f"{facts.beds} bed")
        if facts.baths:
            details.append(f"{facts.baths} bath")
        if facts.sqft:
            details.append(f"{facts.sqft:,} sqft")
        if facts.list_price:
            details.append(f"${facts.list_price:,.0f}")
        
        if details:
            st.markdown(" • ".join(details))
        
        if facts.days_on_market:
            st.caption(f"Days on Market: {facts.days_on_market}")
