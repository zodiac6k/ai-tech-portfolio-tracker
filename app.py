import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from ai_portfolio_tracker import AITechPortfolioTracker

# Page configuration
st.set_page_config(
    page_title="AI Tech Portfolio Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize tracker
tracker = AITechPortfolioTracker("ai_portfolio_config.json")

# Title
st.markdown('<div class="main-header">📊 AI Tech Portfolio Dashboard</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("Portfolio Settings")
    refresh_data = st.button("🔄 Refresh Data", use_container_width=True)
    
    if refresh_data:
        tracker.fetch_stock_data()
        st.success("Data refreshed successfully!")
    
    st.divider()
    st.write("### Last Updated")
    st.write(tracker.last_updated.strftime("%Y-%m-%d %H:%M:%S"))

# Main content
col1, col2, col3 = st.columns(3)

# Load portfolio data
if tracker.portfolio:
    total_holdings = len(tracker.portfolio)
    
    with col1:
        st.metric("Total Holdings", total_holdings)
    
    with col2:
        total_invested = sum(
            stock_data.get('shares', 0) * stock_data.get('entry_price', 0)
            for stock_data in tracker.portfolio.values()
        )
        st.metric("Total Invested", f"${total_invested:,.2f}")
    
    with col3:
        st.metric("Portfolio Status", "Active")

# Portfolio Table
st.subheader("📈 Portfolio Holdings")

if tracker.portfolio:
    # Create portfolio dataframe
    portfolio_data = []
    for ticker, data in tracker.portfolio.items():
        portfolio_data.append({
            "Ticker": ticker,
            "Company": data.get('company_name', 'N/A'),
            "Shares": data.get('shares', 0),
            "Entry Price": f"${data.get('entry_price', 0):.2f}",
            "Sector": data.get('sector', 'N/A'),
            "Added Date": data.get('date_added', 'N/A')
        })
    
    df = pd.DataFrame(portfolio_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("📭 No portfolio data available. Please configure your portfolio in the config file.")

# Load and display reports if available
st.divider()
st.subheader("📊 Latest Report")

report_files = [f for f in os.listdir(".") if f.startswith("ai_portfolio_report_") and f.endswith(".json")]
if report_files:
    # Get the latest report
    latest_report = sorted(report_files)[-1]
    
    with open(latest_report, 'r') as f:
        report_data = json.load(f)
    
    st.write(f"**Report Date:** {latest_report.replace('ai_portfolio_report_', '').replace('.json', '')}")
    
    # Display report metrics
    if "summary" in report_data:
        summary = report_data["summary"]
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Value", f"${summary.get('total_portfolio_value', 0):,.2f}")
        with col2:
            st.metric("Gain/Loss", f"${summary.get('total_gain_loss', 0):,.2f}")
        with col3:
            roi = summary.get('total_roi_percentage', 0)
            st.metric("ROI %", f"{roi:.2f}%", 
                     delta=f"{roi:.2f}%" if roi >= 0 else f"{roi:.2f}%")
    
    # Display top performers if available
    if "top_performers" in report_data:
        st.write("### Top Performers")
        st.json(report_data["top_performers"])
else:
    st.info("📊 No reports available yet. Run the tracker to generate reports.")

# Footer
st.divider()
st.markdown("""
    <div style="text-align: center; color: gray; font-size: 0.9rem;">
    AI Tech Portfolio Tracker v1.0 | Last updated: 2026-06-21
    </div>
""", unsafe_allow_html=True)
