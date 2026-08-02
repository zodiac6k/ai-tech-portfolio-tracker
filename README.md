# ai-tech-portfolio-tracker
AI-focused technology stock portfolio tracker with growth analysis and automated reporting

## PNB FCNR Leverage Return Tracker

A companion project that tracks returns on the **PNB (Punjab National Bank) FCNR
(Foreign Currency Non-Resident) leverage strategy**:

1. Place a USD FCNR fixed deposit (FD).
2. Borrow against it (leverage) so your own outlay is only the margin.
3. Earn the spread between the FD rate and the loan rate, net of your margin.

The tracker ships the illustrative scenarios (3/4/5-year tenors × sub-1 MN and
1 MN+ deposit tiers) and recomputes the derived metrics:

- `difference` = FD maturity − loan + interest
- `net_return` = difference − investment amount
- `annualised_yield` = net_return / investment / tenor (simple annualisation)

### Files
- `pnb_fcnr_config.json` — scenario inputs and illustrative maturity values
- `pnb_fcnr_tracker.py` — calculator, JSON report + HTML dashboard generator
- `pnb_fcnr_app.py` — Streamlit dashboard

### Usage
```bash
# Generate JSON report + docs/pnb_fcnr.html and print a summary
python pnb_fcnr_tracker.py

# Interactive dashboard
streamlit run pnb_fcnr_app.py
```

> Disclaimer: Illustrative calculation based on semi-annual compounding.
> Figures are indicative and do not constitute financial advice.
