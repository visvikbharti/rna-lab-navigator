#!/bin/bash
set -e

echo "RNA Lab Navigator - Cleanup Script"
echo "=================================="
echo ""

# Working directory
WORKDIR="/Users/vishalbharti/Downloads/rna-lab-navigator"
cd "$WORKDIR"

echo "1. Removing Python cache files (__pycache__)"
find . -name "__pycache__" -type d -exec rm -rf {} +

echo "2. Removing simplified views"
simplified_files=(
  "backend/api/views_simplified.py"
  "backend/api/search/views_simplified.py"
  "backend/api/search/urls_simplified.py"
  "backend/api/quality/views_simplified.py"
  "backend/api/quality/urls_simplified.py"
  "backend/api/feedback/views_simplified.py"
  "backend/api/feedback/urls_simplified.py"
)

for file in "${simplified_files[@]}"; do
  if [ -f "$file" ]; then
    rm "$file"
    echo "  - Removed $file"
  fi
done

echo "3. Removing redundant environment directories"
if [ -d "myenv" ]; then
  rm -rf "myenv"
  echo "  - Removed myenv directory"
fi

echo "4. Removing development files"
dev_files=(
  ".DS_Store"
  "frontend/demo.html" 
  "backend/db.sqlite3"
)

for file in "${dev_files[@]}"; do
  if [ -f "$file" ]; then
    rm "$file"
    echo "  - Removed $file"
  fi
done

echo "5. Removing frontend build artifacts"
if [ -d "frontend/node_modules" ]; then
  rm -rf "frontend/node_modules"
  echo "  - Removed frontend/node_modules"
fi

echo "6. Updating API URLs to use standard instead of simplified views"
# Update urls.py to use regular views instead of simplified ones
if [ -f "backend/api/urls.py" ]; then
  # Create backup
  cp "backend/api/urls.py" "backend/api/urls.py.bak"
  
  # Replace simplified imports with standard ones
  sed -i '' 's/from .views_simplified import/from .views import/g' "backend/api/urls.py"
  echo "  - Updated backend/api/urls.py imports"
  
  # Replace quality/urls_simplified.py
  sed -i '' 's/quality\/", include("api\.quality\.urls_simplified/quality\/", include("api\.quality\.urls/g' "backend/api/urls.py"
  
  # Replace search/urls_simplified.py
  sed -i '' 's/search\/", include("api\.search\.urls_simplified/search\/", include("api\.search\.urls/g' "backend/api/urls.py"
  
  echo "  - Updated URL includes to standard versions"
fi

echo "7. Checking for unused directories"
if [ -d "backend/api/offline" ]; then
  echo "  - NOTICE: Found 'backend/api/offline' - Consider refactoring this module"
fi

echo "Done! Unnecessary files removed."
echo ""
echo "Next steps:"
echo "1. Update .env files with production values"
echo "2. Configure mTLS certificates for Weaviate"
echo "3. Set up CI/CD pipelines"
echo "4. Deploy to production"