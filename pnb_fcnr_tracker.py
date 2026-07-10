"""
PNB FCNR Leverage Return Tracker
================================

Tracks and analyses returns on the PNB (Punjab National Bank) FCNR
(Foreign Currency Non-Resident) leverage strategy:

    1. The customer places an FCNR fixed deposit (FD) in USD.
    2. The bank extends a loan against that deposit (leverage), so the
       customer's own outlay is only the margin / investment amount.
    3. The FD earns interest at a higher rate than the loan costs; the
       spread, net of the customer's margin, is the return on investment.

The tracker loads a set of illustrative scenarios (tenor x deposit tier),
recomputes the derived metrics from the stored maturity values, and emits a
JSON report plus a self-contained HTML dashboard.

Derived metrics
---------------
    difference        = fd_maturity - loan_maturity
    net_return        = difference - investment_amount
    annualised_yield  = net_return / investment_amount / tenor_years   (simple)

The `project_maturity` helper reproduces the maturity of a principal under
semi-annual compounding for users who want to model their own inputs.
"""

import json
import os
from datetime import datetime


class PNBFCNRTracker:
    def __init__(self, config_file="pnb_fcnr_config.json"):
        self.config_file = config_file
        self.config = {}
        self.scenarios = []
        self.load_config()
        self.last_updated = datetime.now()

    def load_config(self):
        try:
            with open(self.config_file, "r") as f:
                self.config = json.load(f)
                self.scenarios = self.config.get("scenarios", [])
        except FileNotFoundError:
            print(f"Config file {self.config_file} not found. Using empty scenario set.")
            self.config, self.scenarios = {}, []

    @staticmethod
    def project_maturity(principal, annual_rate_pct, years, periods_per_year=2):
        """Maturity value under periodic compounding (default: semi-annual).

        Note: the shipped illustrative figures use a slightly higher internal
        card rate than the displayed rate, so this projection approximates —
        rather than exactly reproduces — the stored maturity values.
        """
        rate = annual_rate_pct / 100.0 / periods_per_year
        return principal * (1 + rate) ** (periods_per_year * years)

    def analyse_scenario(self, scenario):
        """Return a scenario enriched with derived leverage metrics."""
        fd_maturity = scenario["fd_maturity"]
        loan_maturity = scenario["loan_maturity"]
        investment = scenario["investment_amount"]
        years = scenario["tenor_years"]

        difference = fd_maturity - loan_maturity
        net_return = difference - investment
        annualised_yield = (net_return / investment / years * 100) if investment and years else 0.0
        leverage_ratio = (scenario["fd_amount"] / investment) if investment else 0.0

        result = dict(scenario)
        result.update({
            "difference": round(difference, 2),
            "net_return": round(net_return, 2),
            "annualised_yield": round(annualised_yield, 2),
            "leverage_ratio": round(leverage_ratio, 2),
        })
        return result

    def analyse_all(self):
        return [self.analyse_scenario(s) for s in self.scenarios]

    def best_scenario(self, results=None):
        results = results or self.analyse_all()
        if not results:
            return None
        return max(results, key=lambda r: r["annualised_yield"])

    def generate_insights(self, results=None):
        results = results or self.analyse_all()
        insights = []
        if not results:
            return ["No scenarios available for analysis."]

        best = self.best_scenario(results)
        worst = min(results, key=lambda r: r["annualised_yield"])
        insights.append(
            f"Best annualised yield: {best['annualised_yield']:.2f}% "
            f"({best['tenor_years']}Y, {best['tier']})."
        )
        insights.append(
            f"Lowest annualised yield: {worst['annualised_yield']:.2f}% "
            f"({worst['tenor_years']}Y, {worst['tier']})."
        )
        avg_yield = sum(r["annualised_yield"] for r in results) / len(results)
        insights.append(f"Average annualised yield across {len(results)} scenarios: {avg_yield:.2f}%.")
        total_net = sum(r["net_return"] for r in results)
        insights.append(f"Aggregate illustrative net return: ${total_net:,.0f}.")
        insights.append(
            "Higher deposit tiers (>= USD 1 MN) consistently out-yield the sub-1 MN tier "
            "at the same tenor, driven by a wider FD-vs-loan rate spread."
        )
        return insights

    def save_report(self, results=None):
        results = results or self.analyse_all()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report = {
            "product": self.config.get("product", "PNB FCNR Leverage Return Calculation"),
            "currency": self.config.get("currency", "USD"),
            "timestamp": timestamp,
            "scenarios": results,
            "summary": {
                "scenario_count": len(results),
                "average_annualised_yield": round(
                    sum(r["annualised_yield"] for r in results) / len(results), 2
                ) if results else 0.0,
                "best_scenario": self.best_scenario(results)["id"] if results else None,
                "total_net_return": round(sum(r["net_return"] for r in results), 2),
            },
            "insights": self.generate_insights(results),
        }
        filename = f"pnb_fcnr_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(filename, "w") as f:
            json.dump(report, f, indent=2)
        print(f"PNB FCNR report saved: {filename}")
        return filename, report

    def export_html(self, results=None):
        results = results or self.analyse_all()
        os.makedirs("docs", exist_ok=True)
        last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        insights = self.generate_insights(results)
        insights_html = "".join(f"<li>{i}</li>" for i in insights)

        rows = ""
        for r in sorted(results, key=lambda x: (-x["tenor_years"], x["tier"])):
            rows += f"""
            <tr>
                <td>{r['tenor_years']}Y</td>
                <td>{r['tier']}</td>
                <td>${r['customer_margin']:,.0f}</td>
                <td>${r['fd_amount']:,.0f}</td>
                <td>{r['fd_rate']:.2f}%</td>
                <td>${r['fd_maturity']:,.0f}</td>
                <td>${r['loan_amount']:,.0f}</td>
                <td>{r['loan_rate']:.2f}%</td>
                <td>${r['loan_maturity']:,.0f}</td>
                <td>${r['difference']:,.0f}</td>
                <td>${r['net_return']:,.0f}</td>
                <td class="yield">{r['annualised_yield']:.2f}%</td>
            </tr>"""

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PNB FCNR Leverage Return Tracker</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background: #faf6ef; color: #333; }}
        .header {{ background: linear-gradient(90deg, #6b0f1a 0%, #8b1a2b 60%, #d4a017 100%); color: #fff; padding: 28px 24px; }}
        .header h1 {{ margin: 0; font-size: 1.9rem; letter-spacing: 0.5px; }}
        .header p {{ margin: 6px 0 0; opacity: 0.9; }}
        .wrap {{ padding: 24px; }}
        .insights {{ background: #fff8ec; border-left: 5px solid #d4a017; padding: 16px 20px; border-radius: 6px; margin-bottom: 24px; }}
        .insights h2 {{ margin-top: 0; color: #6b0f1a; }}
        table {{ border-collapse: collapse; width: 100%; background: #fff; box-shadow: 0 2px 6px rgba(0,0,0,0.08); border-radius: 6px; overflow: hidden; }}
        th, td {{ padding: 10px 12px; text-align: right; border-bottom: 1px solid #eee; font-size: 0.9rem; white-space: nowrap; }}
        th {{ background: #6b0f1a; color: #fff; text-align: right; }}
        td:nth-child(2), th:nth-child(2) {{ text-align: left; }}
        .yield {{ font-weight: bold; color: #6b0f1a; }}
        .table-scroll {{ overflow-x: auto; }}
        .footer {{ text-align: center; color: #8a7f6a; font-size: 0.85rem; margin-top: 24px; }}
        .disclaimer {{ font-size: 0.8rem; color: #8a7f6a; margin-top: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>PNB FCNR Leverage Return Tracker</h1>
        <p>Foreign Currency Non-Resident deposit leverage strategy &middot; USD &middot; semi-annual compounding</p>
    </div>
    <div class="wrap">
        <div class="insights">
            <h2>Key Insights</h2>
            <ul>{insights_html}</ul>
        </div>
        <div class="table-scroll">
        <table>
            <thead>
                <tr>
                    <th>Tenor</th><th>Tier</th><th>Margin</th>
                    <th>FD Amt</th><th>FD Rate</th><th>FD Maturity</th>
                    <th>Loan Amt</th><th>Loan Rate</th><th>Loan+Int</th>
                    <th>Difference</th><th>Net Return</th><th>Annualised Yield</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        </div>
        <p class="disclaimer">Disclaimer: Illustrative calculation based on semi-annual compounding.
        Figures are indicative and do not constitute financial advice.</p>
        <div class="footer">
            <p>PNB FCNR Leverage Return Tracker &middot; Last updated: {last_updated}</p>
        </div>
    </div>
</body>
</html>"""

        with open("docs/pnb_fcnr.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"PNB FCNR dashboard generated: docs/pnb_fcnr.html")

    def run_full(self):
        results = self.analyse_all()
        self.save_report(results)
        self.export_html(results)
        return results


if __name__ == "__main__":
    print("🏦 Starting PNB FCNR Leverage Return Tracker...")
    tracker = PNBFCNRTracker()
    results = tracker.run_full()

    print("\n📊 PNB FCNR SCENARIOS:")
    for r in sorted(results, key=lambda x: (-x["tenor_years"], x["tier"])):
        print(
            f"  • {r['tenor_years']}Y {r['tier']:<16} "
            f"net ${r['net_return']:>9,.0f}  yield {r['annualised_yield']:>6.2f}%  "
            f"(leverage {r['leverage_ratio']:.1f}x)"
        )

    print("\n💡 INSIGHTS:")
    for insight in tracker.generate_insights(results):
        print(f"  • {insight}")
