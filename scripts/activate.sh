#!/bin/bash
# Virtual Environment Activation Script
# Run this to activate the virtual environment

echo "🐍 Activating Web Crawler Virtual Environment..."
source venv/bin/activate
echo "✅ Virtual environment activated!"
echo "📦 Python: $(which python)"
echo "📦 Version: $(python --version)"
echo ""
echo "🚀 Now you can run:"
echo "   python -m web_crawler.cli --help"
echo "   python examples/basic_usage.py"
echo "   python tests/test_crawler.py"
echo ""
echo "�� To deactivate, run: deactivate"
