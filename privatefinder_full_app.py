import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
import json

st.set_page_config(
    page_title="PrivateFinder Cyprus – Sellable MVP",
    page_icon="🏠",
    layout="wide"
)

# -------------------- Sidebar --------------------
st.sidebar.title("🏠 PrivateFinder Cyprus")
st.sidebar.caption("Private-seller real estate only")

page = st.sidebar.radio("Menu", ["Search & Results", "Pricing & Landing", "Setup & Alerts", "How to Sell This"])

# -------------------- Helper: Apify run --------------------
def run_apify_scraper(token, category, city, min_price, max_price, max_results=100):
    """Run a Bazaraki scraper on Apify and return private listings only."""
    # Using logiover/bazaraki-scraper (adjust actor ID if needed)
    actor_id = "logiover~bazaraki-scraper"  # common one
    
    input_data = {
        "categoryPaths": [category],
        "maxListings": max_results,
        "scrapeDetails": False,
        "language": "en"
    }
    if city and city != "All Cyprus":
        input_data["cities"] = [city.lower()]
    if min_price:
        input_data["priceMin"] = int(min_price)
    if max_price:
        input_data["priceMax"] = int(max_price)

    # Start run
    start_url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={token}"
    try:
        r = requests.post(start_url, json=input_data, timeout=30)
        r.raise_for_status()
        run_id = r.json()["data"]["id"]
    except Exception as e:
        return None, f"Failed to start Apify run: {e}"

    # Poll for finish
    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={token}"
    for _ in range(30):  # ~2.5 min max
        time.sleep(5)
        status = requests.get(status_url).json()["data"]["status"]
        if status in ["SUCCEEDED", "FAILED", "ABORTED"]:
            break
    else:
        return None, "Timeout waiting for Apify"

    if status != "SUCCEEDED":
        return None, f"Run finished with status: {status}"

    # Get dataset
    dataset_url = f"https://api.apify.com/v2/actor-runs/{run_id}/dataset/items?token={token}"
    items = requests.get(dataset_url).json()

    # Filter private only
    private = [item for item in items if not item.get("sellerIsBusiness", True)]
    return private, None

# -------------------- Pages --------------------
if page == "Search & Results":
    st.title("🔍 Search Private Real Estate")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        category_choice = st.selectbox("Type", ["For Sale", "For Rent"])
        category = "real-estate-for-sale" if category_choice == "For Sale" else "real-estate-to-rent"
    with col2:
        city = st.selectbox("City", ["All Cyprus", "Nicosia", "Limassol", "Larnaca", "Paphos", "Famagusta"])
    with col3:
        max_results = st.slider("Max results", 20, 200, 50)

    min_price = st.number_input("Min Price (€)", 0, 1000000, 0)
    max_price = st.number_input("Max Price (€)", 0, 1000000, 0)

    apify_token = st.text_input("Apify API Token (get free at apify.com)", type="password", help="Required for live scraping")

    if st.button("Run Search (Private Sellers Only)", type="primary"):
        if not apify_token:
            st.error("Please enter your Apify API token.")
        else:
            with st.spinner("Scraping Bazaraki via Apify... (30–90 seconds)"):
                results, error = run_apify_scraper(apify_token, category, city, min_price, max_price, max_results)
            
            if error:
                st.error(error)
            elif not results:
                st.warning("No private listings found with these filters.")
            else:
                st.success(f"Found {len(results)} private listings")
                df = pd.DataFrame(results)
                # Clean columns for display
                display_cols = [c for c in ["title", "price", "location", "city", "sellerName", "detailUrl", "postedDate"] if c in df.columns]
                st.dataframe(df[display_cols] if display_cols else df, use_container_width=True)
                
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Download CSV", csv, "private_listings.csv", "text/csv")

elif page == "Pricing & Landing":
    st.title("PrivateFinder Cyprus")
    st.subheader("Stop wasting time on agency listings. Find real private sellers on Bazaraki.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Free", "€0", "Basic search + userscript")
    with col2:
        st.metric("Pro", "€29/mo", "Live scraping + CSV + alerts")
    with col3:
        st.metric("Agency", "€99/mo", "Multiple seats + priority")

    st.markdown("""
    ### What you get
    - Filter out all business & agency listings automatically
    - Search for sale and for rent across Cyprus
    - Export clean CSV of private sellers
    - Email alerts for new private listings (Pro+)
    - Clean, fast interface
    
    ### Perfect for
    - Property investors
    - Buyers who want direct deals
    - Anyone tired of dealing with agencies
    """)

elif page == "Setup & Alerts":
    st.title("⚙️ Setup & Email Alerts")
    
    st.markdown("### 1. Get your free Apify token")
    st.markdown("Go to [apify.com](https://apify.com) → Sign up → Integrations → API token")
    
    st.markdown("### 2. Install the userscript (optional extra)")
    st.download_button(
        "Download userscript",
        data=open("/workspace/artifacts/bazaraki-private-filter.user.js").read(),
        file_name="bazaraki-private-filter.user.js"
    )
    
    st.markdown("### 3. Email Alerts (Pro feature)")
    st.info("""
    **Simple way to add alerts:**
    - Use Apify’s built-in scheduling + webhook
    - Or integrate with Make.com / Zapier → email
    - Or add a free tier of Resend / SendGrid later
    
    For now the CSV export + manual re-run is the fastest path.
    """)

elif page == "How to Sell This":
    st.title("💰 How to Sell This App")
    st.markdown("""
    ### Quick path to revenue
    1. **Deploy** this Streamlit app to [share.streamlit.io](https://share.streamlit.io) (free).
    2. **Add Stripe** checkout (or Gumroad / Lemon Squeezy) for the Pro plan.
    3. **Target** Facebook groups, Cyprus property investor communities, and LinkedIn.
    4. **Offer** a free trial with limited results, then upsell CSV + alerts.
    
    ### Next technical steps I can add
    - User login (Streamlit Authenticator or Supabase)
    - Saved searches
    - Scheduled daily scrapes + email
    - Landing page with Stripe payment links
    
    Just tell me which one to build next.
    """)

st.sidebar.markdown("---")
st.sidebar.caption(f"MVP • {datetime.now().strftime('%Y-%m-%d')}")
