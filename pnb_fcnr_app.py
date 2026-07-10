import json
import os
from datetime import datetime

import pandas as pd
import streamlit as st

from pnb_fcnr_tracker import PNBFCNRTracker

st.set_page_config(
    page_title="PNB FCNR Leverage Return Tracker",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.4rem;
        font-weight: bold;
        background: linear-gradient(90deg, #6b0f1a, #d4a017);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

tracker = PNBFCNRTracker("pnb_fcnr_config.json")
results = tracker.analyse_all()

st.markdown('<div class="main-header">🏦 PNB FCNR Leverage Return Tracker</div>', unsafe_allow_html=True)
st.caption("Foreign Currency Non-Resident deposit leverage strategy · USD · semi-annual compounding")

with st.sidebar:
    st.header("About")
    st.write(
        "Tracks returns on the PNB FCNR leverage strategy: place a USD FCNR "
        "fixed deposit, borrow against it, and earn the spread net of your margin."
    )
    st.divider()
    if st.button("💾 Regenerate report & dashboard", use_container_width=True):
        tracker.run_full()
        st.success("Report and HTML dashboard regenerated.")

if results:
    best = tracker.best_scenario(results)
    avg_yield = sum(r["annualised_yield"] for r in results) / len(results)
    total_net = sum(r["net_return"] for r in results)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Scenarios", len(results))
    col2.metric("Best Annualised Yield", f"{best['annualised_yield']:.2f}%")
    col3.metric("Average Yield", f"{avg_yield:.2f}%")
    col4.metric("Total Net Return", f"${total_net:,.0f}")

    st.subheader("📈 Scenario Comparison")
    df = pd.DataFrame([
        {
            "Tenor": f"{r['tenor_years']}Y",
            "Tier": r["tier"],
            "Margin (USD)": r["customer_margin"],
            "FD Amount": r["fd_amount"],
            "FD Rate": f"{r['fd_rate']:.2f}%",
            "FD Maturity": r["fd_maturity"],
            "Loan Amount": r["loan_amount"],
            "Loan Rate": f"{r['loan_rate']:.2f}%",
            "Loan + Interest": r["loan_maturity"],
            "Difference": r["difference"],
            "Net Return": r["net_return"],
            "Annualised Yield": f"{r['annualised_yield']:.2f}%",
        }
        for r in sorted(results, key=lambda x: (-x["tenor_years"], x["tier"]))
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("📊 Annualised Yield by Scenario")
    chart_df = pd.DataFrame({
        "Scenario": [f"{r['tenor_years']}Y {r['tier'].replace('FCNR ', '')}" for r in results],
        "Annualised Yield %": [r["annualised_yield"] for r in results],
    }).set_index("Scenario")
    st.bar_chart(chart_df)

    st.subheader("💡 Key Insights")
    for insight in tracker.generate_insights(results):
        st.write(f"- {insight}")
else:
    st.info("No scenarios configured. Please populate pnb_fcnr_config.json.")

st.divider()
st.caption(
    "Disclaimer: Illustrative calculation based on semi-annual compounding. "
    "Figures are indicative and do not constitute financial advice."
)
