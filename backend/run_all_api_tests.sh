#!/bin/bash

# RNA Lab Navigator API Testing Suite Runner
# This script runs all API tests in sequence

echo "🚀 RNA Lab Navigator API Testing Suite"
echo "===================================="
echo ""

# Check if server is running
echo "🔍 Checking if backend server is running..."
if ! curl -s http://localhost:8000/api/health/ > /dev/null; then
    echo "❌ Backend server is not running!"
    echo "Please start the server with: cd backend && python manage.py runserver"
    exit 1
fi
echo "✅ Backend server is running"
echo ""

# Run comprehensive API tests
echo "📚 Running Comprehensive API Tests..."
echo "-------------------------------------"
python test_api_comprehensive.py
echo ""

# Run edge case tests
echo "🔨 Running Edge Case & Security Tests..."
echo "---------------------------------------"
python test_api_edge_cases.py
echo ""

# Run hallucination prevention tests
echo "🧠 Running Hallucination Prevention Tests..."
echo "-----------------------------------------"
python test_hallucination_prevention.py
echo ""

# Aggregate results
echo "📊 Aggregating Test Results..."
echo "==============================="

# Check if all result files exist
if [ -f "test_results.json" ] && [ -f "edge_case_results.json" ] && [ -f "hallucination_test_results.json" ]; then
    echo "✅ All test results generated successfully"
    
    # Simple summary (you could make this more sophisticated)
    echo ""
    echo "📋 Test Summary:"
    echo "  - Comprehensive API Tests: See test_results.json"
    echo "  - Edge Case Tests: See edge_case_results.json"
    echo "  - Hallucination Tests: See hallucination_test_results.json"
else
    echo "❌ Some test results are missing"
fi

echo ""
echo "✨ Testing complete!"