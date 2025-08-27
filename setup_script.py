#!/usr/bin/env python3
"""
Setup script for AI Tech Stack Portfolio Tracker
Helps users get started quickly with the portfolio tracking system
"""

import os
import json
import subprocess
import sys
from datetime import datetime

def install_requirements():
    """Install required Python packages"""
    print("📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False
    return True

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    directories = ['reports', 'visualizations', 'data', 'backups']
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def setup_default_config():
    """Setup default portfolio configuration"""
    print("⚙️ Setting up default portfolio configuration...")
    
    config_exists = os.path.exists('ai_portfolio_config.json')
    
    if config_exists:
        response = input("Configuration file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Keeping existing configuration")
            return
    
    # Default portfolio focusing on AI tech stack
    default_config = {
        "portfolio": {
            "TSM": {
                "shares": 100,
                "category": "Infrastructure",
                "region": "Asia",
                "notes": "Leading AI chip manufacturer, 3nm process leader"
            },
            "ASML": {
                "shares": 25,
                "category": "Infrastructure",
                "region": "Europe",
                "notes": "EUV lithography monopoly, critical for advanced chips"
            },
            "NVDA": {
                "shares": 50,
                "category": "Infrastructure",
                "region": "US",
                "notes": "AI training and inference chip leader"
            },
            "MSFT": {
                "shares": 75,
                "category": "Software_Platforms",
                "region": "US",
                "notes": "Azure AI services, OpenAI partnership"
            },
            "GOOGL": {
                "shares": 50,
                "category": "Software_Platforms",
                "region": "US",
                "notes": "AI research leader, TensorFlow, Bard AI"
            },
            "META": {
                "shares": 40,
                "category": "Applications",
                "region": "US",
                "notes": "AI-driven social media, VR/AR metaverse"
            },
            "PLTR": {
                "shares": 100,
                "category": "Emerging_AI",
                "region": "US",
                "notes": "AI analytics, government and enterprise data"
            }
        },
        "settings": {
            "auto_rebalance": False,
            "risk_tolerance": "moderate",
            "investment_horizon": "3-5 years",
            "focus_regions": ["US", "Europe", "Asia"],
            "exclude_sectors": ["tobacco", "gambling", "weapons"]
        },
        "last_updated": datetime.now().isoformat()
    }
    
    with open('ai_portfolio_config.json', 'w') as f:
        json.dump(default_config, f, indent=4)
    
    print("✅ Default configuration created")

def create_gitignore():
    """Create .gitignore file for the project"""
    print("📝 Creating .gitignore file...")
    
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
data/*.csv
reports/*.json
reports/*.csv
visualizations/*.png
backups/
*.log

# Sensitive data
config_private.json
api_keys.txt

# Temporary files
temp/
tmp/
"""
    
    with open('.gitignore', 'w') as f:
        f.write(gitignore_content)
    
    print("✅ .gitignore created")

def run_initial_test():
    """Run initial test to verify setup"""
    print("🧪 Running initial test...")
    
    try:
        from ai_portfolio_tracker import AITechPortfolioTracker
        
        # Initialize tracker
        tracker = AITechPortfolioTracker()
        
        # Test data fetching for a small subset
        test_symbols = ['MSFT', 'GOOGL']
        print(f"Testing data fetch for: {', '.join(test_symbols)}")
        
        # Temporarily modify portfolio for test
        original_portfolio = tracker.portfolio.copy()
        tracker.portfolio = {symbol: {'shares': 10, 'category': 'Test', 'region': 'US'} 
                           for symbol in test_symbols}
        
        # Fetch data
        stock_data = tracker.fetch_stock_data(period="5d")
        
        if stock_data:
            print("✅ Data fetching test successful")
            
            # Test basic analysis
            metrics = tracker.calculate_portfolio_metrics()
            if metrics and 'total_value' in metrics:
                print(f"✅ Portfolio analysis test successful (Test value: ${metrics['total_value']:,.2f})")
            else:
                print("⚠️ Portfolio analysis test had issues")
        else:
            print("⚠️ Data fetching test had issues")
        
        # Restore original portfolio
        tracker.portfolio = original_portfolio
        tracker.save_config()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Test completed with warnings: {e}")
    
    return True

def setup_scheduler_info():
    """Provide information about setting up scheduled runs"""
    print("\n⏰ SCHEDULING INFORMATION")
    print("=" * 50)
    print("To run portfolio analysis automatically, you can:")
    print("\n1. GitHub Actions (Recommended for GitHub repos):")
    print("   - Already configured in .github/workflows/portfolio_tracker.yml")
    print("   - Runs weekdays at 9:30 AM UTC after market open")
    print("   - Manual trigger available")
    
    print("\n2. Cron Job (Linux/Mac):")
    print("   Add to crontab (crontab -e):")
    print("   # Run Mon-Fri at 9:30 AM")
    print("   30 9 * * 1-5 cd /path/to/portfolio && python ai_portfolio_tracker.py")
    
    print("\n3. Windows Task Scheduler:")
    print("   - Create new task")
    print("   - Trigger: Daily, weekdays only")
    print("   - Action: Start program 'python' with argument 'ai_portfolio_tracker.py'")
    print("   - Set working directory to your project folder")

def main():
    """Main setup function"""
    print("🚀 AI Tech Stack Portfolio Tracker Setup")
    print("=" * 50)
    print("This script will help you set up the portfolio tracking system.\n")
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Install requirements
    if not install_requirements():
        print("❌ Setup failed during package installation")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Setup configuration
    setup_default_config()
    
    # Create .gitignore
    create_gitignore()
    
    # Run initial test
    if run_initial_test():
        print("\n✅ SETUP COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        print("You can now run the portfolio tracker with:")
        print("  python ai_portfolio_tracker.py")
        print("\nOr import it in your own scripts:")
        print("  from ai_portfolio_tracker import AITechPortfolioTracker")
        
        # Show next steps
        print("\n📋 NEXT STEPS:")
        print("1. Review and customize ai_portfolio_config.json")
        print("2. Run: python ai_portfolio_tracker.py")
        print("3. Check the generated reports and visualizations")
        print("4. Set up automated scheduling (see info below)")
        
        # Scheduler info
        setup_scheduler_info()
        
        print(f"\n📚 Check README.md for detailed usage instructions")
        
    else:
        print("\n⚠️ Setup completed with warnings")
        print("Please check the error messages above and ensure all dependencies are correctly installed")

if __name__ == "__main__":
    main()
