
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import json
import os
import warnings
import time
from matplotlib import cm  # Import cm here, at the global level

warnings.filterwarnings('ignore')

# Remove this line - it's causing the error
# colors = cm.viridis(np.linspace(0, 0.8, len(top_ai)))  


class AITechPortfolioTracker:
    def __init__(self, config_file="ai_portfolio_config.json"):
        self.config_file = config_file
        self.portfolio = {}
        self.stock_data = {}
        self.load_config()
        self.last_updated = datetime.now()

    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.portfolio = config.get('portfolio', {})
                # Update config last_updated timestamp
                config['last_updated'] = datetime.now().isoformat()
                # Save the updated config
                self.save_config(config)
        except FileNotFoundError:
            print(f"Config file {self.config_file} not found. Using empty portfolio.")
    
    def save_config(self, config=None):
        """Save the configuration back to the JSON file"""
        if config is None:
            config = {
                'portfolio': self.portfolio,
                'last_updated': datetime.now().isoformat()
            }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
            
    def fetch_stock_data(self, period="1mo"):
        print(f"Fetching stock data as of {datetime.now().strftime('%Y-%m-%d')}...")
        
        # Add a slight delay between API calls to avoid rate limiting
        delay = 0.5  # seconds
        
        for symbol in self.portfolio.keys():
            try:
                ticker = yf.Ticker(symbol)
                # Use end date as yesterday to ensure we have complete data
                yesterday = datetime.now() - timedelta(days=1)
                end_date = yesterday.strftime('%Y-%m-%d')
                
                # Fetch data with explicit start and end dates
                hist = ticker.history(period=period, end=end_date)
                
                # Fetch detailed info
                info = ticker.info
                
                if not hist.empty:
                    self.stock_data[symbol] = {
                        'history': hist,
                        'info': info,
                        'current_price': hist['Close'].iloc[-1],
                        'last_updated': yesterday.strftime('%Y-%m-%d')
                    }
                    print(f"✓ {symbol} - ${hist['Close'].iloc[-1]:.2f} as of {yesterday.strftime('%Y-%m-%d')}")
                else:
                    print(f"⚠ {symbol} - No data returned")
                    self.stock_data[symbol] = {'history': pd.DataFrame(), 'info': {}, 'current_price': 0}
            except Exception as e:
                print(f"✗ {symbol} failed: {e}")
                self.stock_data[symbol] = {'history': pd.DataFrame(), 'info': {}, 'current_price': 0}
            
            # Add delay to avoid rate limiting
            time.sleep(delay)
            
        return self.stock_data

    def calculate_portfolio_metrics(self):
        """Calculate key portfolio metrics using real market data"""
        metrics = {}
        total_value, total_cost = 0, 0
        rows = []
        
        for symbol, holding in self.portfolio.items():
            if symbol not in self.stock_data or self.stock_data[symbol]['current_price'] == 0:
                continue
                
            current_price = self.stock_data[symbol]['current_price']
            shares = holding['shares']
            market_value = current_price * shares
            
            # Get more realistic cost basis - use a month-ago price or approximate
            hist = self.stock_data[symbol]['history']
            if not hist.empty and len(hist) > 20:
                # Use price from ~30 days ago as mock cost basis
                cost_basis = hist['Close'].iloc[-20]
            else:
                # Fallback - assume 10% gain
                cost_basis = current_price * 0.9
                
            cost_value = cost_basis * shares
            gain_loss = market_value - cost_value
            gain_loss_pct = (gain_loss / cost_value * 100) if cost_value > 0 else 0
            
            # Calculate additional metrics
            if not hist.empty:
                week_ago_idx = -5 if len(hist) >= 5 else 0
                week_ago_price = hist['Close'].iloc[week_ago_idx]
                week_change_pct = ((current_price - week_ago_price) / week_ago_price * 100) if week_ago_price > 0 else 0
                
                # Get 52-week high/low if available
                if len(hist) >= 252:
                    high_52wk = hist['High'].tail(252).max()
                    low_52wk = hist['Low'].tail(252).min()
                    pct_off_high = ((high_52wk - current_price) / high_52wk * 100) if high_52wk > 0 else 0
                else:
                    high_52wk = hist['High'].max()
                    low_52wk = hist['Low'].min()
                    pct_off_high = ((high_52wk - current_price) / high_52wk * 100) if high_52wk > 0 else 0
            else:
                week_change_pct = 0
                high_52wk, low_52wk = 0, 0
                pct_off_high = 0
            
            # Add company name if available
            company_name = self.stock_data[symbol]['info'].get('shortName', symbol)
            
            total_value += market_value
            total_cost += cost_value
            
            rows.append({
                "Symbol": symbol,
                "Company": company_name,
                "Shares": shares,
                "Current_Price": current_price,
                "Market_Value": market_value,
                "Cost_Basis": cost_basis,
                "Gain_Loss_Pct": gain_loss_pct,
                "Week_Change_Pct": week_change_pct,
                "Pct_Off_52wk_High": pct_off_high,
                "52wk_High": high_52wk,
                "52wk_Low": low_52wk,
                "Category": holding.get('category', 'Uncategorized'),
                "Region": holding.get('region', 'Unknown'),
                "Weight": 0  # Will calculate after we have total
            })
        
        # Create DataFrame and calculate weights
        df = pd.DataFrame(rows)
        if not df.empty:
            df["Weight"] = (df["Market_Value"] / total_value * 100) if total_value > 0 else 0
            
            # Sort by market value (descending)
            df = df.sort_values("Market_Value", ascending=False)
        
        metrics['portfolio_df'] = df
        metrics['total_value'] = total_value
        metrics['total_cost'] = total_cost
        metrics['total_gain_loss'] = total_value - total_cost
        metrics['total_gain_loss_pct'] = (total_value - total_cost) / total_cost * 100 if total_cost > 0 else 0
        
        # Add category analysis
        if not df.empty:
            category_analysis = df.groupby('Category').agg({
                'Market_Value': 'sum',
                'Gain_Loss_Pct': 'mean',
                'Symbol': 'count'
            }).rename(columns={'Symbol': 'Count'})
            
            category_analysis['Weight'] = category_analysis['Market_Value'] / total_value * 100
            metrics['category_analysis'] = category_analysis
            
            # Add region analysis
            region_analysis = df.groupby('Region').agg({
                'Market_Value': 'sum',
                'Gain_Loss_Pct': 'mean',
                'Symbol': 'count'
            }).rename(columns={'Symbol': 'Count'})
            
            region_analysis['Weight'] = region_analysis['Market_Value'] / total_value * 100
            metrics['region_analysis'] = region_analysis
        
        return metrics

    def analyze_ai_growth(self):
        """Analyze AI-specific growth metrics"""
        analysis = {}
        for symbol, data in self.stock_data.items():
            hist = data['history']
            if hist.empty:
                continue
                
            current_price = hist['Close'].iloc[-1]
            
            # Calculate growth over different periods
            price_1m_ago = hist['Close'].iloc[-20] if len(hist) >= 20 else hist['Close'].iloc[0]
            price_3m_ago = hist['Close'].iloc[-60] if len(hist) >= 60 else hist['Close'].iloc[0]
            price_6m_ago = hist['Close'].iloc[-130] if len(hist) >= 130 else hist['Close'].iloc[0]
            
            growth_1m = ((current_price - price_1m_ago) / price_1m_ago * 100) if price_1m_ago > 0 else 0
            growth_3m = ((current_price - price_3m_ago) / price_3m_ago * 100) if price_3m_ago > 0 else 0
            growth_6m = ((current_price - price_6m_ago) / price_6m_ago * 100) if price_6m_ago > 0 else 0
            
            # Calculate volatility and trading volume metrics
            returns = hist['Close'].pct_change().dropna()
            volume_trend = hist['Volume'].tail(5).mean() / hist['Volume'].tail(20).mean() if len(hist) >= 20 else 1
            
            # Assign AI relevance scores based on categorization and real company data
            category = self.portfolio[symbol].get('category', '')
            
            # More nuanced AI scoring
            ai_base_scores = {
                'Infrastructure': 8.5,
                'Software_Platforms': 8.0,
                'Applications': 7.0,
                'Emerging_AI': 9.0
            }
            
            # Get base score from category
            ai_relevance_score = ai_base_scores.get(category, 7.0)
            
            # Adjust based on specific companies with high AI focus
            if symbol in ["NVDA", "TSM"]:  # Infrastructure leaders
                ai_relevance_score = 9.5
            elif symbol in ["MSFT", "GOOGL"]:  # AI platform leaders
                ai_relevance_score = 9.0
            elif symbol in ["PLTR", "SNOW"]:  # Emerging AI data leaders
                ai_relevance_score = 8.8
            
            # Also account for recent growth as a factor in AI relevance
            growth_factor = (growth_3m / 20) if abs(growth_3m) < 40 else (np.sign(growth_3m) * 2)
            ai_relevance_score = min(10, ai_relevance_score + growth_factor)
            
            # Store the analysis - ensure numeric values
            analysis[symbol] = {
                "ai_relevance_score": float(ai_relevance_score),  # Ensure float type
                "growth_1m": float(growth_1m),
                "growth_3m": float(growth_3m),
                "growth_6m": float(growth_6m),
                "volatility": float(returns.std() * np.sqrt(252) * 100),
                "volume_trend": float(volume_trend),
                "category": category
            }
            
        return analysis

    def generate_portfolio_insights(self, metrics, growth_analysis):
        """Generate key insights about the portfolio"""
        insights = []
        
        if not metrics or not growth_analysis:
            return ["Insufficient data for insights"]
            
        df = metrics.get('portfolio_df', pd.DataFrame())
        if df.empty:
            return ["No portfolio data available"]
            
        # Overall portfolio performance
        total_value = metrics.get('total_value', 0)
        total_gain_pct = metrics.get('total_gain_loss_pct', 0)
        
        insights.append(f"Portfolio value: ${total_value:,.2f}, Performance: {total_gain_pct:+.2f}%")
        
        # Top performers
        if len(df) > 0:
            top_performers = df.nlargest(3, 'Gain_Loss_Pct')
            insights.append("Top performers: " + ", ".join([
                f"{row['Symbol']} ({row['Gain_Loss_Pct']:+.2f}%)" 
                for _, row in top_performers.iterrows()
            ]))
            
            # Laggards
            laggards = df.nsmallest(3, 'Gain_Loss_Pct')
            insights.append("Underperformers: " + ", ".join([
                f"{row['Symbol']} ({row['Gain_Loss_Pct']:+.2f}%)" 
                for _, row in laggards.iterrows()
            ]))
        
        # Category analysis
        if 'category_analysis' in metrics:
            top_category = metrics['category_analysis'].nlargest(1, 'Gain_Loss_Pct')
            if not top_category.empty:
                cat_name = top_category.index[0]
                cat_gain = top_category['Gain_Loss_Pct'].iloc[0]
                cat_weight = top_category['Weight'].iloc[0]
                insights.append(f"Best category: {cat_name} ({cat_gain:+.2f}%), {cat_weight:.1f}% of portfolio")
        
        # AI specific insights
        if growth_analysis:
            try:
                # Convert to DataFrame and ensure numeric types
                ai_df = pd.DataFrame.from_dict(growth_analysis, orient='index')
                ai_df.reset_index(inplace=True)
                ai_df.rename(columns={'index': 'symbol'}, inplace=True)
                
                # Ensure numeric data types
                for col in ['ai_relevance_score', 'growth_3m']:
                    ai_df[col] = pd.to_numeric(ai_df[col], errors='coerce')
                
                # Filter for high AI relevance and positive growth
                high_potential = ai_df[
                    (ai_df['ai_relevance_score'] > 8.5) & 
                    (ai_df['growth_3m'] > 0)
                ]
                
                if not high_potential.empty:
                    # Get top 2 by AI relevance
                    top_potential = high_potential.sort_values('ai_relevance_score', ascending=False).head(2)
                    
                    insights.append("AI high potential: " + ", ".join([
                        f"{row['symbol']} (AI score: {row['ai_relevance_score']:.1f}, 3m: {row['growth_3m']:+.2f}%)" 
                        for _, row in top_potential.iterrows()
                    ]))
            except Exception as e:
                insights.append(f"AI analysis error: {str(e)}")
        
        return insights

    def export_html(self, metrics, growth_analysis):
        """Generate HTML dashboard with current portfolio data"""
        os.makedirs("docs/charts", exist_ok=True)
        
        # Convert growth analysis to DataFrame for easier handling
        try:
            df_growth = pd.DataFrame.from_dict(growth_analysis, orient='index')
            df_growth.reset_index(inplace=True)
            df_growth.rename(columns={'index': 'symbol'}, inplace=True)
            
            # Ensure numeric types
            for col in ['ai_relevance_score', 'growth_1m', 'growth_3m', 'growth_6m', 'volatility', 'volume_trend']:
                if col in df_growth.columns:
                    df_growth[col] = pd.to_numeric(df_growth[col], errors='coerce')
        
            # 1. Create portfolio allocation chart by category
            if 'category_analysis' in metrics:
                category_data = metrics['category_analysis']
                plt.figure(figsize=(10, 6))
                plt.pie(
                    category_data['Market_Value'], 
                    labels=category_data.index, 
                    autopct='%1.1f%%',
                    startangle=90,
                    shadow=False
                )
                plt.axis('equal')
                plt.title('AI Portfolio Allocation by Category')
                plt.tight_layout()
                plt.savefig("docs/charts/category_allocation.png")
                plt.close()
            
            # 2. Top AI ranking by relevance score
            top_ai = df_growth.nlargest(8, "ai_relevance_score")
            
            plt.figure(figsize=(12, 6))
            colors = plt.cm.viridis(np.linspace(0, 0.8, len(top_ai)))
            bars = plt.barh(top_ai['symbol'], top_ai["ai_relevance_score"], color=colors)
            
            # Add growth data as text
            for i, (_, row) in enumerate(top_ai.iterrows()):
                plt.text(
                    row["ai_relevance_score"] + 0.1, 
                    i, 
                    f"{row['growth_3m']:+.1f}% (3m)",
                    va='center'
                )
            
            plt.xlabel("AI Relevance Score")
            plt.title("Top AI Companies by Relevance Score")
            plt.xlim(0, 10.5)  # Scale 0-10 with room for text
            plt.gca().invert_yaxis()  # Highest at top
            plt.grid(axis='x', linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig("docs/charts/ai_portfolio_analysis.png")
            plt.close()
            
            # 3. Performance comparison chart
            portfolio_df = metrics['portfolio_df']
            if not portfolio_df.empty and len(portfolio_df) > 0:
                # Sort by gain/loss percentage
                sorted_df = portfolio_df.sort_values('Gain_Loss_Pct', ascending=False)
                
                plt.figure(figsize=(12, 8))
                colors = ['green' if x >= 0 else 'red' for x in sorted_df['Gain_Loss_Pct']]
                
                bars = plt.bar(sorted_df['Symbol'], sorted_df['Gain_Loss_Pct'], color=colors)
                
                # Add value labels on top of bars
                for bar in bars:
                    height = bar.get_height()
                    plt.text(
                        bar.get_x() + bar.get_width()/2.,
                        height + (0.5 if height >= 0 else -1.5),
                        f"{height:+.1f}%",
                        ha='center',
                        va='bottom' if height >= 0 else 'top',
                        fontsize=9
                    )
                
                plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
                plt.axhline(y=metrics['total_gain_loss_pct'], color='blue', linestyle='--', alpha=0.7,
                           label=f"Portfolio Avg: {metrics['total_gain_loss_pct']:+.1f}%")
                
                plt.ylabel('Gain/Loss %')
                plt.title('AI Portfolio Holdings Performance')
                plt.xticks(rotation=45)
                plt.grid(axis='y', linestyle='--', alpha=0.7)
                plt.legend()
                plt.tight_layout()
                plt.savefig("docs/charts/performance_comparison.png")
                plt.close()
        except Exception as e:
            print(f"Error generating charts: {str(e)}")
        
        # Generate insights
        insights = self.generate_portfolio_insights(metrics, growth_analysis)
        insights_html = "<ul>" + "".join([f"<li>{insight}</li>" for insight in insights]) + "</ul>"
        
        # Format the dataframe for display
        display_df = metrics['portfolio_df'].copy() if 'portfolio_df' in metrics else pd.DataFrame()
        if not display_df.empty:
            try:
                # Format as currency where appropriate
                for col in ['Current_Price', 'Market_Value', 'Cost_Basis', '52wk_High', '52wk_Low']:
                    if col in display_df.columns:
                        display_df[col] = display_df[col].map('${:,.2f}'.format)
                
                # Format percentages
                for col in ['Gain_Loss_Pct', 'Week_Change_Pct', 'Pct_Off_52wk_High', 'Weight']:
                    if col in display_df.columns:
                        display_df[col] = display_df[col].map('{:+.2f}%'.format)
                
                # Select columns to display
                display_cols = ['Symbol', 'Company', 'Shares', 'Current_Price', 'Market_Value', 
                               'Gain_Loss_Pct', 'Week_Change_Pct', 'Category', 'Region']
                display_df = display_df[[col for col in display_cols if col in display_df.columns]]
            except Exception as e:
                print(f"Error formatting display data: {str(e)}")
        
        # Get last updated timestamp
        last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # HTML page with multiple sections and improved styling
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>AI Tech Portfolio Tracker</title>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; background: #f8f9fa; color: #333; }}
                h1, h2 {{ color: #2c3e50; }}
                .dashboard-header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .dashboard-section {{ background: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 12px 8px; text-align: left; }}
                th {{ background-color: #2c3e50; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                .chart-container {{ display: flex; flex-wrap: wrap; justify-content: space-between; }}
                .chart {{ flex: 0 0 48%; margin-bottom: 20px; background: white; padding: 10px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                .chart img {{ max-width: 100%; height: auto; }}
                .positive {{ color: green; }}
                .negative {{ color: red; }}
                .insights {{ background-color: #f0f7ff; padding: 15px; border-left: 5px solid #3498db; margin-bottom: 20px; }}
                .footer {{ text-align: center; margin-top: 30px; font-size: 0.9em; color: #7f8c8d; }}
                @media (max-width: 768px) {{
                    .chart {{ flex: 0 0 100%; }}
                }}
            </style>
        </head>
        <body>
            <div class="dashboard-header">
                <h1>AI Tech Portfolio Tracker</h1>
                <p>Real-time tracking and analysis of AI technology investments</p>
            </div>
            
            <div class="dashboard-section">
                <h2>Portfolio Summary</h2>
                <p>Last Updated: {last_updated}</p>
                <p>Total Portfolio Value: <strong>${metrics.get('total_value', 0):,.2f}</strong> | 
                   Overall Performance: <strong class="{'positive' if metrics.get('total_gain_loss_pct', 0) >= 0 else 'negative'}">
                   {metrics.get('total_gain_loss_pct', 0):+.2f}%</strong></p>
                
                <div class="insights">
                    <h3>Key Insights</h3>
                    {insights_html}
                </div>
            </div>
            
            <div class="dashboard-section">
                <h2>Portfolio Holdings</h2>
                {display_df.to_html(index=False, classes='table') if not display_df.empty else "<p>No portfolio data available</p>"}
            </div>
            
            <div class="dashboard-section">
                <h2>Portfolio Analysis</h2>
                
                <div class="chart-container">
                    <div class="chart">
                        <h3>AI Relevance Ranking</h3>
                        <img src="charts/ai_portfolio_analysis.png" alt="AI Portfolio Analysis">
                    </div>
                    
                    <div class="chart">
                        <h3>Performance Comparison</h3>
                        <img src="charts/performance_comparison.png" alt="Performance Comparison">
                    </div>
                    
                    <div class="chart">
                        <h3>Portfolio Allocation</h3>
                        <img src="charts/category_allocation.png" alt="Category Allocation">
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p><a href="https://zodiac6k.github.io/ESG/">← Back to ESG Dashboard</a></p>
                <p>Powered by AI Tech Portfolio Tracker | Data sourced from Yahoo Finance</p>
                <p>© {datetime.now().year} AI Portfolio Analytics</p>
            </div>
        </body>
        </html>
        """
        
        with open("docs/ai.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"AI dashboard generated: docs/ai.html with data as of {last_updated}")
        
        # Save a JSON report file with the data
        try:
            report_data = {
                "timestamp": last_updated,
                "total_value": metrics.get('total_value', 0),
                "total_gain_loss_pct": metrics.get('total_gain_loss_pct', 0),
                "holdings": metrics.get('portfolio_df', pd.DataFrame()).to_dict(orient='records') if not metrics.get('portfolio_df', pd.DataFrame()).empty else [],
                "insights": insights
            }
            
            report_filename = f"ai_portfolio_report_{datetime.now().strftime('%Y%m%d')}.json"
            with open(report_filename, "w") as f:
                json.dump(report_data, f, indent=2)
            
            print(f"Portfolio report saved: {report_filename}")
        except Exception as e:
            print(f"Error saving portfolio report: {str(e)}")

    def run_full_analysis(self):
        """Run complete portfolio analysis and return results"""
        self.fetch_stock_data(period="3mo")  # Get 3 months of data for better analysis
        metrics = self.calculate_portfolio_metrics()
        growth_analysis = self.analyze_ai_growth()
        self.export_html(metrics, growth_analysis)
        
        # Generate insights for return
        insights = self.generate_portfolio_insights(metrics, growth_analysis)
        
        return metrics, growth_analysis, insights

    def run_full(self):
        """Legacy method for backward compatibility"""
        metrics, growth_analysis, _ = self.run_full_analysis()
        print(f"Portfolio analysis complete. Total value: ${metrics.get('total_value', 0):,.2f}")


if __name__ == "__main__":
    # Skip interactive mode in CI
    if os.environ.get("GITHUB_ACTIONS") == "true":
        tracker = AITechPortfolioTracker()
        tracker.run_full()
    else:
        print("🚀 Starting AI Tech Portfolio Tracker...")
        tracker = AITechPortfolioTracker()
        metrics, growth, insights = tracker.run_full_analysis()
        
        print("\n📊 PORTFOLIO INSIGHTS:")
        for insight in insights:
            print(f"  • {insight}")