# Advanced Analytics Module for AI Tech Portfolio Tracker
# Provides additional analytical capabilities for deep portfolio insights

import pandas as pd
import numpy as np
import yfinance as yf
from typing import Dict, List, Tuple
import warnings
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

warnings.filterwarnings('ignore')

class AdvancedPortfolioAnalytics:
    """
    Advanced analytics for AI tech portfolio including:
    - Sector rotation analysis
    - Correlation analysis
    - Risk-adjusted performance metrics
    - Monte Carlo simulations
    - AI trend scoring
    """
    
    def __init__(self, portfolio_tracker):
        self.tracker = portfolio_tracker
        self.benchmark_symbols = {
            'QQQ': 'NASDAQ-100 Tech ETF',
            'XLK': 'Technology Select Sector',
            'ROBO': 'Global Robotics & AI ETF',
            'ARKQ': 'Autonomous & Robotics ETF'
        }
        self.ai_trend_indicators = {
            'cloud_adoption': 0.85,
            'ai_patent_growth': 0.92,
            'venture_ai_funding': 0.78,
            'enterprise_ai_spend': 0.88,
            'semiconductor_demand': 0.95
        }
    
    def fetch_benchmark_data(self, period: str = "1y") -> Dict:
        """Fetch benchmark ETF data for comparison"""
        benchmark_data = {}
        
        for symbol, name in self.benchmark_symbols.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)
                benchmark_data[symbol] = {
                    'name': name,
                    'history': hist,
                    'current_price': hist['Close'].iloc[-1] if not hist.empty else 0
                }
                print(f"✓ Fetched benchmark data for {symbol}")
            except Exception as e:
                print(f"✗ Error fetching {symbol}: {str(e)}")
        
        return benchmark_data
    
    def calculate_portfolio_beta(self, benchmark_symbol: str = 'QQQ') -> Dict:
        """Calculate portfolio beta against benchmark"""
        if benchmark_symbol not in self.benchmark_symbols:
            print(f"Benchmark {benchmark_symbol} not available")
            return {}
        
        # Get benchmark data
        benchmark_data = self.fetch_benchmark_data()
        if benchmark_symbol not in benchmark_data:
            return {}
        
        benchmark_returns = benchmark_data[benchmark_symbol]['history']['Close'].pct_change().dropna()
        
        portfolio_betas = {}
        
        for symbol in self.tracker.portfolio.keys():
            if symbol in self.tracker.stock_data:
                stock_hist = self.tracker.stock_data[symbol]['history']
                if not stock_hist.empty:
                    stock_returns = stock_hist['Close'].pct_change().dropna()
                    
                    # Align dates
                    common_dates = stock_returns.index.intersection(benchmark_returns.index)
                    if len(common_dates) > 30:  # Need sufficient data points
                        aligned_stock = stock_returns.loc[common_dates]
                        aligned_bench = benchmark_returns.loc[common_dates]
                        
                        # Calculate beta using linear regression
                        slope, intercept, r_value, p_value, std_err = stats.linregress(
                            aligned_bench, aligned_stock
                        )
                        
                        portfolio_betas[symbol] = {
                            'beta': slope,
                            'alpha': intercept * 252,  # Annualized alpha
                            'r_squared': r_value ** 2,
                            'correlation': r_value
                        }
        
        return portfolio_betas
    
    def analyze_sector_momentum(self) -> Dict:
        """Analyze momentum across different AI sectors"""
        sector_performance = {}
        
        # Group stocks by category
        categories = {}
        for symbol, details in self.tracker.portfolio.items():
            category = details['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(symbol)
        
        # Calculate momentum for each category
        for category, symbols in categories.items():
            category_returns = []
            category_volumes = []
            
            for symbol in symbols:
                if symbol in self.tracker.stock_data:
                    hist = self.tracker.stock_data[symbol]['history']
                    if not hist.empty and len(hist) >= 20:
                        # 20-day momentum
                        returns_20d = (hist['Close'].iloc[-1] / hist['Close'].iloc[-20] - 1) * 100
                        volume_trend = hist['Volume'].tail(5).mean() / hist['Volume'].tail(20).mean()
                        
                        category_returns.append(returns_20d)
                        category_volumes.append(volume_trend)
            
            if category_returns:
                sector_performance[category] = {
                    'avg_momentum_20d': np.mean(category_returns),
                    'momentum_std': np.std(category_returns),
                    'avg_volume_trend': np.mean(category_volumes),
                    'stocks_count': len(category_returns),
                    'momentum_score': np.mean(category_returns) / (np.std(category_returns) + 0.1)  # Risk-adjusted
                }
        
        return sector_performance
    
    def calculate_correlation_matrix(self) -> pd.DataFrame:
        """Calculate correlation matrix of portfolio stocks"""
        returns_data = {}
        
        # Collect returns for all stocks
        for symbol in self.tracker.portfolio.keys():
            if symbol in self.tracker.stock_data:
                hist = self.tracker.stock_data[symbol]['history']
                if not hist.empty:
                    returns = hist['Close'].pct_change().dropna()
                    returns_data[symbol] = returns
        
        if not returns_data:
            return pd.DataFrame()
        
        # Create DataFrame with aligned dates
        returns_df = pd.DataFrame(returns_data)
        returns_df = returns_df.dropna()
        
        # Calculate correlation matrix
        correlation_matrix = returns_df.corr()
        
        return correlation_matrix
    
    def identify_portfolio_clusters(self) -> Dict:
        """Use K-means clustering to identify stock clusters based on performance metrics"""
        
        # Prepare features for clustering
        features_data = []
        stock_symbols = []
        
        for symbol in self.tracker.portfolio.keys():
            if symbol in self.tracker.stock_data:
                hist = self.tracker.stock_data[symbol]['history']
                if not hist.empty and len(hist) >= 60:
                    returns = hist['Close'].pct_change().dropna()
                    
                    # Calculate features
                    volatility = returns.std() * np.sqrt(252)
                    sharpe_ratio = returns.mean() / (returns.std() + 1e-8) * np.sqrt(252)
                    max_drawdown = self._calculate_max_drawdown(hist['Close'])
                    momentum_3m = (hist['Close'].iloc[-1] / hist['Close'].iloc[-65] - 1) if len(hist) >= 65 else 0
                    volume_trend = hist['Volume'].tail(20).mean() / hist['Volume'].head(20).mean() if len(hist) >= 40 else 1
                    
                    features_data.append([
                        volatility, sharpe_ratio, max_drawdown, momentum_3m, volume_trend
                    ])
                    stock_symbols.append(symbol)
        
        if len(features_data) < 3:
            return {}
        
        # Standardize features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features_data)
        
        # K-means clustering
        n_clusters = min(4, len(features_data))  # Max 4 clusters
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(features_scaled)
        
        # Organize results
        clusters = {}
        for i, symbol in enumerate(stock_symbols):
            cluster_id = cluster_labels[i]
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append({
                'symbol': symbol,
                'volatility': features_data[i][0],
                'sharpe_ratio': features_data[i][1],
                'max_drawdown': features_data[i][2],
                'momentum_3m': features_data[i][3],
                'volume_trend': features_data[i][4]
            })
        
        return clusters
    
    def _calculate_max_drawdown(self, price_series) -> float:
        """Calculate maximum drawdown for a price series"""
        cumulative = (1 + price_series.pct_change()).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
    
    def monte_carlo_simulation(self, days: int = 252, simulations: int = 1000) -> Dict:
        """Run Monte Carlo simulation for portfolio performance"""
        
        # Calculate portfolio weights
        total_value = 0
        portfolio_weights = {}
        
        for symbol, holding in self.tracker.portfolio.items():
            if symbol in self.tracker.stock_data:
                current_price = self.tracker.stock_data[symbol]['current_price']
                market_value = current_price * holding['shares']
                total_value += market_value
        
        for symbol, holding in self.tracker.portfolio.items():
            if symbol in self.tracker.stock_data:
                current_price = self.tracker.stock_data[symbol]['current_price']
                market_value = current_price * holding['shares']
                portfolio_weights[symbol] = market_value / total_value if total_value > 0 else 0
        
        # Calculate historical returns and correlations
        returns_data = {}
        for symbol in portfolio_weights.keys():
            hist = self.tracker.stock_data[symbol]['history']
            if not hist.empty:
                returns = hist['Close'].pct_change().dropna()
                returns_data[symbol] = returns
        
        if not returns_data:
            return {}
        
        returns_df = pd.DataFrame(returns_data).dropna()
        mean_returns = returns_df.mean()
        cov_matrix = returns_df.cov()
        
        # Run simulations
        portfolio_results = []
        
        for _ in range(simulations):
            # Generate random returns using multivariate normal distribution
            random_returns = np.random.multivariate_normal(
                mean_returns.values, cov_matrix.values, days
            )
            
            # Calculate portfolio returns
            portfolio_returns = []
            for day_returns in random_returns:
                day_portfolio_return = sum(
                    portfolio_weights[symbol] * day_returns[i] 
                    for i, symbol in enumerate(returns_df.columns)
                )
                portfolio_returns.append(day_portfolio_return)
            
            # Calculate cumulative return
            cumulative_return = np.prod(1 + np.array(portfolio_returns)) - 1
            portfolio_results.append(cumulative_return)
        
        # Calculate statistics
        portfolio_results = np.array(portfolio_results)
        
        return {
            'mean_return': np.mean(portfolio_results),
            'std_return': np.std(portfolio_results),
            'percentile_5': np.percentile(portfolio_results, 5),
            'percentile_95': np.percentile(portfolio_results, 95),
            'probability_positive': (portfolio_results > 0).mean(),
            'probability_loss_10pct': (portfolio_results < -0.1).mean(),
            'all_results': portfolio_results.tolist()
        }
    
    def ai_trend_scoring(self) -> Dict:
        """Score stocks based on AI trend alignment"""
        ai_scores = {}
        
        for symbol, holding in self.tracker.portfolio.items():
            if symbol in self.tracker.stock_data:
                base_score = 5.0  # Base score
                
                # Category multipliers
                category_multipliers = {
                    'Infrastructure': 1.2,
                    'Software_Platforms': 1.1,
                    'Applications': 1.0,
                    'Emerging_AI': 1.3
                }
                
                category = holding['category']
                category_multiplier = category_multipliers.get(category, 1.0)
                
                # Regional multipliers (based on AI investment trends)
                regional_multipliers = {
                    'US': 1.1,
                    'Asia': 1.2,
                    'Europe': 1.0
                }
                
                region = holding['region']
                regional_multiplier = regional_multipliers.get(region, 1.0)
                
                # Performance factor
                hist = self.tracker.stock_data[symbol]['history']
                if not hist.empty and len(hist) >= 30:
                    recent_performance = (hist['Close'].iloc[-1] / hist['Close'].iloc[-30] - 1)
                    performance_factor = 1 + (recent_performance * 0.5)  # 50% weight to recent performance
                else:
                    performance_factor = 1.0
                
                # Calculate final AI trend score
                final_score = (base_score * category_multiplier * 
                              regional_multiplier * performance_factor)
                
                # Apply AI trend indicators
                trend_bonus = sum(self.ai_trend_indicators.values()) / len(self.ai_trend_indicators)
                final_score *= trend_bonus
                
                ai_scores[symbol] = {
                    'ai_trend_score': min(final_score, 10.0),  # Cap at 10
                    'category_factor': category_multiplier,
                    'regional_factor': regional_multiplier,
                    'performance_factor': performance_factor,
                    'trend_alignment': trend_bonus
                }
        
        return ai_scores
    
    def generate_advanced_insights(self) -> List[str]:
        """Generate advanced analytical insights"""
        insights = []
        
        # Run analyses
        beta_analysis = self.calculate_portfolio_beta()
        sector_momentum = self.analyze_sector_momentum()
        correlation_matrix = self.calculate_correlation_matrix()
        clusters = self.identify_portfolio_clusters()
        monte_carlo = self.monte_carlo_simulation()
        ai_trends = self.ai_trend_scoring()
        
        # Beta insights
        if beta_analysis:
            avg_beta = np.mean([data['beta'] for data in beta_analysis.values()])
            if avg_beta > 1.2:
                insights.append(f"⚡ High-beta portfolio (β={avg_beta:.2f}) - expect amplified market moves")
            elif avg_beta < 0.8:
                insights.append(f"🛡️ Defensive portfolio (β={avg_beta:.2f}) - lower market sensitivity")
        
        # Sector momentum insights
        if sector_momentum:
            best_momentum = max(sector_momentum.items(), key=lambda x: x[1]['momentum_score'])
            insights.append(f"🚀 Strongest sector momentum: {best_momentum[0]} ({best_momentum[1]['avg_momentum_20d']:+.1f}%)")
        
        # Correlation insights
        if not correlation_matrix.empty:
            avg_correlation = correlation_matrix.values[np.triu_indices_from(correlation_matrix.values, k=1)].mean()
            if avg_correlation > 0.7:
                insights.append(f"⚠️ High portfolio correlation ({avg_correlation:.2f}) - limited diversification")
            elif avg_correlation < 0.3:
                insights.append(f"✅ Well-diversified portfolio (correlation: {avg_correlation:.2f})")
        
        # Monte Carlo insights
        if monte_carlo:
            prob_positive = monte_carlo['probability_positive']
            var_5 = monte_carlo['percentile_5']
            insights.append(f"🎯 1-year outlook: {prob_positive:.0%} chance of gains, 5% VaR: {var_5:+.1%}")
        
        # AI trend insights
        if ai_trends:
            top_ai_stock = max(ai_trends.items(), key=lambda x: x[1]['ai_trend_score'])
            insights.append(f"🤖 Highest AI trend alignment: {top_ai_stock[0]} (score: {top_ai_stock[1]['ai_trend_score']:.1f}/10)")
        
        # Clustering insights
        if clusters:
            cluster_sizes = [len(cluster) for cluster in clusters.values()]
            insights.append(f"📊 Portfolio clusters identified: {len(clusters)} groups (sizes: {cluster_sizes})")
        
        return insights
    
    def create_advanced_visualizations(self):
        """Create advanced analytical visualizations"""
        fig = plt.figure(figsize=(20, 24))
        
        # 1. Correlation Heatmap
        plt.subplot(4, 3, 1)
        correlation_matrix = self.calculate_correlation_matrix()
        if not correlation_matrix.empty:
            sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, 
                       square=True, fmt='.2f', cbar_kws={"shrink": .8})
            plt.title('Portfolio Correlation Matrix')
        
        # 2. Beta Analysis
        plt.subplot(4, 3, 2)
        beta_analysis = self.calculate_portfolio_beta()
        if beta_analysis:
            symbols = list(beta_analysis.keys())
            betas = [beta_analysis[s]['beta'] for s in symbols]
            colors = ['red' if b > 1 else 'green' for b in betas]
            
            plt.barh(symbols, betas, color=colors, alpha=0.7)
            plt.axvline(x=1, color='black', linestyle='--', alpha=0.5)
            plt.xlabel('Beta (vs QQQ)')
            plt.title('Stock Beta Analysis')
        
        # 3. Sector Momentum
        plt.subplot(4, 3, 3)
        sector_momentum = self.analyze_sector_momentum()
        if sector_momentum:
            sectors = list(sector_momentum.keys())
            momentum_scores = [sector_momentum[s]['momentum_score'] for s in sectors]
            
            plt.bar(sectors, momentum_scores, alpha=0.7)
            plt.xticks(rotation=45)
            plt.ylabel('Risk-Adjusted Momentum')
            plt.title('Sector Momentum Analysis')
        
        # 4. Monte Carlo Results
        plt.subplot(4, 3, 4)
        monte_carlo = self.monte_carlo_simulation(simulations=500)
        if monte_carlo and 'all_results' in monte_carlo:
            plt.hist(monte_carlo['all_results'], bins=50, alpha=0.7, edgecolor='black')
            plt.axvline(x=monte_carlo['mean_return'], color='red', linestyle='--', 
                       label=f"Mean: {monte_carlo['mean_return']:+.1%}")
            plt.axvline(x=monte_carlo['percentile_5'], color='orange', linestyle='--',
                       label=f"5% VaR: {monte_carlo['percentile_5']:+.1%}")
            plt.xlabel('1-Year Return')
            plt.ylabel('Frequency')
            plt.title('Monte Carlo Simulation (500 runs)')
            plt.legend()
        
        # 5. AI Trend Scores
        plt.subplot(4, 3, 5)
        ai_trends = self.ai_trend_scoring()
        if ai_trends:
            symbols = list(ai_trends.keys())
            scores = [ai_trends[s]['ai_trend_score'] for s in symbols]
            
            plt.barh(symbols, scores, alpha=0.7, color='blue')
            plt.xlabel('AI Trend Score (0-10)')
            plt.title('AI Trend Alignment Scores')
        
        # 6. Risk-Return Scatter (Advanced)
        plt.subplot(4, 3, 6)
        risk_return_data = []
        for symbol in self.tracker.portfolio.keys():
            if symbol in self.tracker.stock_data:
                hist = self.tracker.stock_data[symbol]['history']
                if not hist.empty and len(hist) >= 60:
                    returns = hist['Close'].pct_change().dropna()
                    ann_return = returns.mean() * 252 * 100
                    ann_vol = returns.std() * np.sqrt(252) * 100
                    risk_return_data.append((symbol, ann_vol, ann_return))
        
        if risk_return_data:
            symbols, vols, rets = zip(*risk_return_data)
            plt.scatter(vols, rets, alpha=0.7, s=100)
            for i, symbol in enumerate(symbols):
                plt.annotate(symbol, (vols[i], rets[i]), fontsize=8)
            plt.xlabel('Annualized Volatility (%)')
            plt.ylabel('Annualized Return (%)')
            plt.title('Risk-Return Profile')
        
        # 7. Portfolio Clusters Visualization
        plt.subplot(4, 3, 7)
        clusters = self.identify_portfolio_clusters()
        if clusters:
            colors = ['red', 'blue', 'green', 'orange', 'purple']
            for i, (cluster_id, stocks) in enumerate(clusters.items()):
                vols = [s['volatility'] for s in stocks]
                sharpes = [s['sharpe_ratio'] for s in stocks]
                symbols = [s['symbol'] for s in stocks]
                
                plt.scatter(vols, sharpes, c=colors[i % len(colors)], 
                           label=f'Cluster {cluster_id}', alpha=0.7, s=100)
                for j, symbol in enumerate(symbols):
                    plt.annotate(symbol, (vols[j], sharpes[j]), fontsize=8)
            
            plt.xlabel('Volatility')
            plt.ylabel('Sharpe Ratio')
            plt.title('Portfolio Clustering Analysis')
            plt.legend()
        
        # 8. Volume Trend Analysis
        plt.subplot(4, 3, 8)
        volume_trends = {}
        for symbol in self.tracker.portfolio.keys():
            if symbol in self.tracker.stock_data:
                hist = self.tracker.stock_data[symbol]['history']
                if not hist.empty and len(hist) >= 40:
                    recent_vol = hist['Volume'].tail(10).mean()
                    historical_vol = hist['Volume'].head(30).mean()
                    volume_trends[symbol] = (recent_vol / historical_vol - 1) * 100
        
        if volume_trends:
            symbols = list(volume_trends.keys())
            trends = list(volume_trends.values())
            colors = ['green' if t > 0 else 'red' for t in trends]
            
            plt.barh(symbols, trends, color=colors, alpha=0.7)
            plt.xlabel('Volume Trend (%)')
            plt.title('Recent Volume vs Historical Average')
            plt.axvline(x=0, color='black', linestyle='-', alpha=0.3)
        
        # 9. AI Trend Components
        plt.subplot(4, 3, 9)
        trend_components = list(self.ai_trend_indicators.keys())
        trend_values = list(self.ai_trend_indicators.values())
        
        plt.bar(trend_components, trend_values, alpha=0.7)
        plt.xticks(rotation=45)
        plt.ylabel('Trend Strength (0-1)')
        plt.title('AI Market Trend Indicators')
        plt.ylim(0, 1)
        
        # 10. Performance Attribution
        plt.subplot(4, 3, 10)
        if hasattr(self.tracker, 'calculate_portfolio_metrics'):
            metrics = self.tracker.calculate_portfolio_metrics()
            if 'portfolio_df' in metrics:
                df = metrics['portfolio_df']
                category_contrib = df.groupby('Category').apply(
                    lambda x: (x['Weight'] * x['Gain_Loss_Pct']).sum()
                )
                
                colors = ['green' if c > 0 else 'red' for c in category_contrib.values]
                plt.bar(category_contrib.index, category_contrib.values, 
                       color=colors, alpha=0.7)
                plt.xticks(rotation=45)
                plt.ylabel('Contribution to Return (%)')
                plt.title('Performance Attribution by Category')
        
        # 11. Drawdown Analysis
        plt.subplot(4, 3, 11)
        portfolio_prices = []
        dates = []
        
        # Calculate portfolio price series (simplified)
        if self.tracker.stock_data:
            sample_symbol = list(self.tracker.stock_data.keys())[0]
            sample_hist = self.tracker.stock_data[sample_symbol]['history']
            if not sample_hist.empty:
                dates = sample_hist.index
                
                # Simplified portfolio construction for visualization
                portfolio_values = []
                for date in dates:
                    daily_value = 0
                    for symbol, holding in self.tracker.portfolio.items():
                        if symbol in self.tracker.stock_data:
                            hist = self.tracker.stock_data[symbol]['history']
                            if date in hist.index:
                                price = hist.loc[date, 'Close']
                                daily_value += price * holding['shares'] * 0.01  # Scaled down
                    portfolio_values.append(daily_value)
                
                if portfolio_values:
                    portfolio_series = pd.Series(portfolio_values, index=dates)
                    running_max = portfolio_series.expanding().max()
                    drawdown = (portfolio_series - running_max) / running_max * 100
                    
                    plt.fill_between(dates, drawdown, 0, alpha=0.3, color='red')
                    plt.plot(dates, drawdown, color='red', linewidth=1)
                    plt.ylabel('Drawdown (%)')
                    plt.title('Portfolio Drawdown Analysis')
                    plt.xticks(rotation=45)
        
        # 12. Efficiency Frontier (simplified)
        plt.subplot(4, 3, 12)
        # This would require more complex optimization - showing conceptual version
        if hasattr(self.tracker, 'stock_data') and len(self.tracker.stock_data) >= 3:
            np.random.seed(42)
            n_portfolios = 100
            returns = np.random.normal(0.08, 0.15, n_portfolios)
            risks = np.random.normal(0.20, 0.05, n_portfolios)
            
            plt.scatter(risks, returns, alpha=0.6, c=returns/risks, cmap='viridis')
            plt.xlabel('Risk (Volatility)')
            plt.ylabel('Expected Return')
            plt.title('Efficient Frontier (Conceptual)')
            plt.colorbar(label='Sharpe Ratio')
        
        plt.tight_layout()
        plt.savefig('advanced_portfolio_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def export_advanced_report(self) -> str:
        """Export comprehensive advanced analytics report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Run all analyses
        beta_analysis = self.calculate_portfolio_beta()
        sector_momentum = self.analyze_sector_momentum()
        correlation_matrix = self.calculate_correlation_matrix()
        clusters = self.identify_portfolio_clusters()
        monte_carlo = self.monte_carlo_simulation()
        ai_trends = self.ai_trend_scoring()
        insights = self.generate_advanced_insights()
        
        # Compile comprehensive report
        advanced_report = {
            'report_metadata': {
                'timestamp': timestamp,
                'analysis_type': 'Advanced AI Tech Portfolio Analytics',
                'portfolio_size': len(self.tracker.portfolio),
                'data_period': '1 year'
            },
            'beta_analysis': beta_analysis,
            'sector_momentum': sector_momentum,
            'correlation_analysis': {
                'correlation_matrix': correlation_matrix.to_dict() if not correlation_matrix.empty else {},
                'average_correlation': correlation_matrix.values[np.triu_indices_from(correlation_matrix.values, k=1)].mean() if not correlation_matrix.empty else 0
            },
            'portfolio_clusters': clusters,
            'monte_carlo_simulation': monte_carlo,
            'ai_trend_scoring': ai_trends,
            'ai_market_indicators': self.ai_trend_indicators,
            'advanced_insights': insights,
            'risk_metrics': {
                'portfolio_beta_avg': np.mean([data['beta'] for data in beta_analysis.values()]) if beta_analysis else 0,
                'correlation_risk': 'High' if (not correlation_matrix.empty and correlation_matrix.values[np.triu_indices_from(correlation_matrix.values, k=1)].mean() > 0.7) else 'Moderate',
                'downside_risk_5pct': monte_carlo.get('percentile_5', 0) if monte_carlo else 0
            }
        }
        
        # Save comprehensive report
        filename = f'advanced_ai_portfolio_analytics_{timestamp}.json'
        with open(filename, 'w') as f:
            json.dump(advanced_report, f, indent=4, default=str)
        
        print(f"Advanced analytics report saved: {filename}")
        return filename

def run_advanced_analysis(portfolio_tracker):
    """Convenience function to run complete advanced analysis"""
    print("\n🔬 ADVANCED AI PORTFOLIO ANALYTICS")
    print("=" * 60)
    
    # Initialize advanced analytics
    advanced = AdvancedPortfolioAnalytics(portfolio_tracker)
    
    # Generate insights
    insights = advanced.generate_advanced_insights()
    
    print("\n🧠 ADVANCED INSIGHTS")
    print("-" * 30)
    for insight in insights:
        print(f"  {insight}")
    
    # Create visualizations
    print("\n📊 Generating advanced visualizations...")
    advanced.create_advanced_visualizations()
    
    # Export report
    report_file = advanced.export_advanced_report()
    
    print(f"\n✅ Advanced analysis complete!")
    print(f"📁 Report saved: {report_file}")
    print(f"📈 Visualizations saved: advanced_portfolio_analysis.png")
    
    return advanced

# Example usage integration
if __name__ == "__main__":
    # This would be used with the main portfolio tracker
    print("Advanced Analytics Module for AI Tech Portfolio Tracker")
    print("Import this module and use with your portfolio tracker instance:")
    print("\nfrom advanced_analytics import run_advanced_analysis")
    print("run_advanced_analysis(your_portfolio_tracker)")
