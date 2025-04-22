# upsell_demo_boss_friendly.py

import streamlit as st
import pandas as pd
import re
from collections import Counter
import random

# --- Core Logic Functions (Mostly unchanged, focus is on presentation) ---

@st.cache_data
def load_data(json_path):
    """Loads review JSON data"""
    try:
        df = pd.read_json(json_path)
        # Basic cleaning
        df['positiveText'] = df['positiveText'].fillna('')
        df['negativeText'] = df['negativeText'].fillna('')
        if 'username' not in df.columns: df['username'] = 'Unknown'
        else: df['username'] = df['username'].fillna('Unknown').str.strip()
        if 'countryName' not in df.columns: df['countryName'] = 'Unknown'
        if 'numNights' not in df.columns: df['numNights'] = 1
        else: df['numNights'] = pd.to_numeric(df['numNights'], errors='coerce').fillna(1)
        if 'lang' not in df.columns: df['lang'] = 'en'
        df['lang'] = df['lang'].replace('xu', 'en')
        return df
    except Exception as e:
        st.error(f"Error loading {json_path}: {e}")
        return None

@st.cache_data
def analyze_reviews_for_insights(_df):
    """Analyzes reviews for key insights"""
    if _df is None: return None
    insights = {}
    aspect_keywords = { # Simplified for clarity
        'Location': ["location", "station", "convenient", "access", "near", "位置", "车站", "方便", "交通"],
        'Service': ["staff", "service", "friendly", "helpful", "attentive", "concierge", "员工", "服务", "友好", "帮助", "周到"],
        'Breakfast': ["breakfast", "food", "restaurant", "delicious", "lounge", "buffet", "早餐", "食物", "餐厅", "美味"],
        'Room Comfort': ["room", "spacious", "clean", "view", "bed", "bathroom", "quiet", "comfortable", "房间", "宽敞", "干净", "景观", "床", "舒适"],
        'Value': ["price", "expensive", "value", "charge", "rate", "价格", "贵", "性价比"]
    }
    aspect_sentiment_scores = {aspect: {'Positive mentions': 0, 'Negative mentions': 0} for aspect in aspect_keywords}
    all_keywords_found = []
    common_negative_phrases = ['nothing', 'none', 'no', '-', '', '無い', '特にありません']

    for index, row in _df.iterrows():
        positive_text = str(row.get('positiveText', '')).lower()
        negative_text = str(row.get('negativeText', '')).lower()
        for aspect, keywords in aspect_keywords.items():
            for keyword in keywords:
                if keyword in positive_text:
                    aspect_sentiment_scores[aspect]['Positive mentions'] += 1
                    all_keywords_found.append(keyword)
                if keyword in negative_text and negative_text not in common_negative_phrases:
                    aspect_sentiment_scores[aspect]['Negative mentions'] += 1
                    # Only add negative keywords if you want them in the cloud/list
                    # all_keywords_found.append(keyword)

    insights['aspect_sentiment_df'] = pd.DataFrame(aspect_sentiment_scores)
    insights['top_keywords'] = Counter(all_keywords_found).most_common(10)
    try:
        insights['avg_nights_by_country'] = _df.groupby('countryName')['numNights'].mean().round(1).sort_values(ascending=False).head(5)
    except:
        insights['avg_nights_by_country'] = pd.Series(dtype='float64')
    return insights

@st.cache_data
def define_personas_and_proxies():
    """Defines personas and their key indicators"""
    personas_proxies = {
        "Food & Service Aficionado": {
            "description": "Highly values breakfast quality and staff service.",
            "key_indicators_text": "- High booking frequency\n- Often books breakfast\n- High member tier (Gold+)",
            "proxy_indicators": {"min_historical_bookings": 3, "current_booking_includes_breakfast": True, "is_member_tier": ["Gold", "Platinum"]},
            "targeted_upsells": ["UP002", "UP005", "UP003"], # Lounge, Premium Breakfast, Dinner Pkg
            "icon": "🍽️"
        },
        "View Chaser & Comfort Seeker": {
            "description": "Seeks room views, space, and comfort.",
            "key_indicators_text": "- Longer average stays\n- Historically books higher room types (View, Suite)\n- Traveling as a couple/family",
            "proxy_indicators": {"avg_historical_nights": 4, "historical_room_types": ["Deluxe", "Suite", "View"], "pax_count": 2},
            "targeted_upsells": ["UP001", "UP006"], # View Upgrade, Suite Upgrade
            "icon": "🏞️"
        },
        "Efficient Business Traveler": {
            "description": "Focuses on efficiency, location convenience, and business support.",
            "key_indicators_text": "- Corporate email\n- Midweek stays\n- Single occupancy",
            "proxy_indicators": {"email_domain_type": "corporate", "is_midweek_stay": True, "pax_count": 1},
             "targeted_upsells": ["UP002", "UP004"], # Lounge, Late Checkout
             "icon": "💼"
        }
    }
    return personas_proxies

@st.cache_data
def simulate_future_guests():
    """Simulates future guest data"""
    guests = [
        {"guest_id": "GUEST001", "name": "Mr. Smith (Business)", "email_domain_type": "corporate", "historical_bookings": 5, "avg_historical_nights": 2, "is_member_tier": "Silver", "current_booking_nights": 3, "is_midweek_stay": True, "pax_count": 1},
        {"guest_id": "GUEST002", "name": "Ms. Jones (Leisure)", "email_domain_type": "personal", "historical_bookings": 1, "avg_historical_nights": 5, "historical_room_types": ["Deluxe"], "is_member_tier": "Basic", "current_booking_nights": 4, "is_midweek_stay": False, "pax_count": 2},
        {"guest_id": "GUEST003", "name": "Dr. Chen (Frequent Flyer)", "email_domain_type": "educational", "historical_bookings": 10, "avg_historical_nights": 3, "is_member_tier": "Platinum", "current_booking_nights": 2, "is_midweek_stay": True, "pax_count": 1, "current_booking_includes_breakfast": True}
    ]
    return guests

def query_available_upsells(guest_id):
    """Simulates dynamically available upsells"""
    full_upsell_list = [
        {"id": "UP001", "name": "Upgrade to City View Room", "price_increase": 5000, "description": "Enjoy stunning city views."},
        {"id": "UP002", "name": "Executive Lounge Access", "price_increase": 15000, "description": "Includes breakfast, snacks, and evening cocktails."},
        {"id": "UP003", "name": "Special Dinner Package", "price_increase": 10000, "description": "A curated dining experience for two."},
        {"id": "UP004", "name": "Late Checkout (3 PM)", "price_increase": 3000, "description": "Relax longer on your departure day."},
        {"id": "UP005", "name": "Premium Breakfast Upgrade", "price_increase": 2000, "description": "Access to exclusive breakfast items."},
        {"id": "UP006", "name": "Upgrade to Junior Suite", "price_increase": 25000, "description": "More space and upgraded amenities."}
    ]
    num_to_remove = random.randint(0, 2)
    if num_to_remove >= len(full_upsell_list): num_to_remove = len(full_upsell_list) - 1
    available = random.sample(full_upsell_list, len(full_upsell_list) - num_to_remove)
    return available

def match_guest_to_persona(guest_data, personas_info):
    """Matches guest to the best persona and explains why"""
    best_match_persona = "Unknown"
    highest_score = 0
    match_reasons = {} # Store reasons for the best match

    for persona_name, persona_details in personas_info.items():
        current_score = 0
        reasons = []
        indicators = persona_details['proxy_indicators']

        # Simplified check for demonstration
        if 'min_historical_bookings' in indicators and guest_data.get('historical_bookings', 0) >= indicators['min_historical_bookings']:
            current_score += 1; reasons.append(f"Frequent Booker ({guest_data.get('historical_bookings', 0)} bookings)")
        if 'current_booking_includes_breakfast' in indicators and guest_data.get('current_booking_includes_breakfast') == indicators['current_booking_includes_breakfast']:
             current_score += 1; reasons.append("Booked Breakfast")
        if 'is_member_tier' in indicators and guest_data.get('is_member_tier') in indicators['is_member_tier']:
            current_score += 1; reasons.append(f"{guest_data.get('is_member_tier')} Tier Member")
        if 'avg_historical_nights' in indicators and guest_data.get('avg_historical_nights', 0) >= indicators['avg_historical_nights']:
            current_score += 1; reasons.append(f"Long Stays Avg ({guest_data.get('avg_historical_nights', 0)} nights)")
        if 'historical_room_types' in indicators and any(room in guest_data.get('historical_room_types', []) for room in indicators['historical_room_types']):
            current_score += 1; reasons.append("Prefers Higher Room Types")
        # Add other indicator checks similarly...
        if 'pax_count' in indicators and guest_data.get('pax_count') == indicators['pax_count']:
             current_score += 1; reasons.append(f"{indicators['pax_count']} Guest(s)")
        if 'email_domain_type' in indicators and guest_data.get('email_domain_type') == indicators['email_domain_type']:
             current_score += 1; reasons.append("Corporate Email")
        if 'is_midweek_stay' in indicators and guest_data.get('is_midweek_stay') == indicators['is_midweek_stay']:
             current_score += 1; reasons.append("Midweek Stay")

        if current_score > highest_score:
            highest_score = current_score
            best_match_persona = persona_name
            match_reasons = reasons # Store reasons for the highest score found so far

    if highest_score == 0: # If no indicators matched any persona
         best_match_persona = "General Guest"
         match_reasons = ["No specific indicators matched strongly."]


    return best_match_persona, match_reasons

def recommend_upsells_based_on_match(persona_name, available_upsells, personas_info):
    """Recommends available upsells targeted for the persona"""
    recommendations = []
    if persona_name == "Unknown" or persona_name == "General Guest" or persona_name not in personas_info:
        # Default Rules: Recommend globally high-performing upsells when no user history exists
        # Instead of just offering the cheapest option, prioritize known high-performing options
        if available_upsells:
            # Define globally high-performing upsell IDs in priority order
            global_high_performers = ["UP005", "UP002", "UP004", "UP001"]  # Breakfast, Lounge, Late Checkout, View Room
            available_map = {opt['id']: opt for opt in available_upsells}
            
            # First try to find breakfast upgrade (highest global performer)
            if "UP005" in available_map:  # Premium Breakfast
                recommendations.append({
                    "option": available_map["UP005"],
                    "reason": "Breakfast upgrades are our most popular option across all guest types."
                })
            
            # Then add other high performers if available
            for upsell_id in global_high_performers:
                if upsell_id != "UP005" and upsell_id in available_map and len(recommendations) < 2:
                    recommendations.append({
                        "option": available_map[upsell_id],
                        "reason": "This is a globally popular choice that most guests enjoy."
                    })
            
            # If somehow we still have no recommendations, fall back to cheapest option
            if not recommendations:
                cheapest = min(available_upsells, key=lambda x: x['price_increase'])
                recommendations.append({
                    "option": cheapest,
                    "reason": "An affordable enhancement to your stay."
                })
        return recommendations

    targeted_upsell_ids = personas_info[persona_name].get("targeted_upsells", [])
    available_map = {opt['id']: opt for opt in available_upsells} # Map for quick lookup

    for target_id in targeted_upsell_ids:
        if target_id in available_map:
            option = available_map[target_id]
            recommendations.append({
                "option": option,
                "reason": f"Matches the '{persona_name}' preference for {personas_info[persona_name]['description'].split('.')[0].lower()}." # Simplified reason
            })
    return recommendations


# --- Streamlit App UI ---

st.set_page_config(layout="wide", page_title="Hotel Upsell Demo")
st.title("🏨 Personalized Hotel Upsell Recommendation Demo")
st.caption("Using Past Review Insights from The Strings by InterContinental, Tokyo (IHG) (via Booking.com) to Target Future Guest Offers")

# --- Load Data ---
data_file = 'data.json'
review_data_df = load_data(data_file)

if review_data_df is not None:
    personas_database = define_personas_and_proxies()
    simulated_guests_list = simulate_future_guests()
    simulated_guests_dict = {guest['guest_id']: guest for guest in simulated_guests_list}

    # --- Section 1: Learning from Past Guests ---
    st.header("1. Why Analyze Guest Reviews?")
    st.markdown("Past reviews tell us what different guest types value most. We identify patterns to understand preferences.")

    insights = analyze_reviews_for_insights(review_data_df)

    if insights:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("👍👎 What Guests Talk About (Sentiment)")
            st.bar_chart(insights['aspect_sentiment_df'].T) # Transpose for better aspect view
            st.caption("Shows positive vs. negative mentions for key hotel aspects.")

        with col2:
            st.subheader("💬 Top Keywords Mentioned")
            keywords_df = pd.DataFrame(insights['top_keywords'], columns=['Keyword', 'Count'])
            st.dataframe(keywords_df, height=250) # Limit height
            st.caption("Highlights the most frequently discussed topics.")

            # st.subheader("🌍 Guests Staying Longest (Avg. Nights)")
            # st.dataframe(insights['avg_nights_by_country'])
            # st.caption("Helps understand travel patterns of different nationalities.")
    else:
        st.warning("Could not generate insights from review data.")

    st.divider()

    # --- Section 2: Defining Guest Personas ---
    st.header("2. Who Are Our Key Guest Types (Personas)?")
    st.markdown("Based on review insights, we create profiles for common guest types and how to identify them.")

    cols = st.columns(len(personas_database))
    for i, (name, data) in enumerate(personas_database.items()):
        with cols[i]:
            st.subheader(f"{data['icon']} {name}")
            st.markdown(f"**Description:** {data['description']}")
            st.markdown("**How we identify them (Examples):**")
            st.caption(data['key_indicators_text']) # Use pre-formatted text

    st.divider()

    # --- Section 3: The Live Recommendation Demo ---
    st.header("3. Live Demo: Recommending to a Future Guest")
    st.markdown("Select a simulated future guest. We'll use their limited data to match them to a persona and recommend relevant, *currently available* upsells.")

    # Guest Selection
    guest_names = [guest['name'] for guest in simulated_guests_list]
    selected_guest_name = st.selectbox("Select Simulated Guest:", guest_names, key="guest_select")

    if selected_guest_name:
        # Find the selected guest's data
        selected_guest_data = next((guest for guest in simulated_guests_list if guest['name'] == selected_guest_name), None)

        if selected_guest_data:
            guest_id = selected_guest_data['guest_id']
            st.info(f"Simulating arrival for **{selected_guest_name}**...")

            col_guest, col_match, col_rec = st.columns(3)

            with col_guest:
                st.subheader("📋 Guest Info (Simulated)")
                # Display key simulated data points clearly
                st.markdown(f"- **Tier:** {selected_guest_data.get('is_member_tier', 'N/A')}")
                st.markdown(f"- **Bookings:** {selected_guest_data.get('historical_bookings', 0)} historical")
                st.markdown(f"- **Email:** {selected_guest_data.get('email_domain_type', 'N/A')} type")
                st.markdown(f"- **Stay:** {selected_guest_data.get('current_booking_nights', 'N/A')} nights, {'Midweek' if selected_guest_data.get('is_midweek_stay') else 'Weekend'}")
                st.markdown(f"- **Breakfast Booked?** {'Yes' if selected_guest_data.get('current_booking_includes_breakfast') else 'No'}")

                # Show currently available upsells (dynamic)
                available_upsells = query_available_upsells(guest_id)
                st.subheader("🛒 Available Upsells Now")
                if available_upsells:
                    for upsell in available_upsells:
                         st.caption(f"- {upsell['name']} (+{upsell['price_increase']} JPY)")
                else:
                    st.caption("None available in this simulation.")


            with col_match:
                st.subheader("👤 Persona Match")
                matched_persona, match_reasons = match_guest_to_persona(selected_guest_data, personas_database)
                icon = personas_database.get(matched_persona, {}).get('icon', '❓')
                st.success(f"**Best Match: {icon} {matched_persona}**")
                st.markdown("**Reasoning (Key Matching Data):**")
                if match_reasons:
                     for reason in match_reasons:
                         st.caption(f"- {reason}")
                else:
                    st.caption("- Matches general profile.")


            with col_rec:
                st.subheader("✨ Recommended Offers")
                final_recommendations = recommend_upsells_based_on_match(matched_persona, available_upsells, personas_database)

                if final_recommendations:
                    for rec in final_recommendations:
                        st.markdown(f"**✅ {rec['option']['name']}** (+{rec['option']['price_increase']} JPY)")
                        st.caption(f"*{rec['reason']}*")
                        # st.caption(f"*{rec['option']['description']}*") # Optional: add description
                else:
                    st.warning("No specific targeted upsells are available and match this guest's profile right now.")

else:
    st.error("Cannot start the demo. Please ensure 'data.json' is present and valid.")
