#!/bin/bash
# F1 Dashboard Setup Script

echo "🏎️ Setting up F1 Dashboard..."

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3 and try again."
    exit 1
fi

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment. Please check your Python installation."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies. Please check your internet connection and try again."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📄 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit the .env file with your Salesforce API credentials."
fi

echo "✅ Setup complete! To start the dashboard, run:"
echo "   source venv/bin/activate"
echo "   python run_dashboard.py --driver \"Your Name\" --track \"Track Name\""
echo ""
echo "🎮 Make sure UDP telemetry is enabled in F1 24 game settings."