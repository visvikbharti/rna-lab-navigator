#!/bin/bash

# Script to reload sample data for the RNA Lab Navigator
# This bypasses the ML-dependent ingestion pipeline

echo "Reloading sample data for RNA Lab Navigator..."
cd "$(dirname "$0")/../backend/scripts"
python load_sample_data.py

# Verify the data was loaded
echo ""
echo "Verifying loaded data:"
python verify_data.py

echo ""
echo "Sample data reloaded successfully!"
echo "You can now use the application with the demo data."