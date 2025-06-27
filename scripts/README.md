# RNA Lab Navigator - Scripts

Utility scripts for deployment, maintenance, and data management.

## 📁 Script Categories

```
scripts/
├── Deployment Scripts
├── Data Management
├── Environment Setup
└── Maintenance Utilities
```

## 🚀 Deployment Scripts

### `deploy-railway.sh`
Deploys the backend to Railway platform.
```bash
./scripts/deploy-railway.sh
```

### `deploy-vercel.sh`
Deploys the frontend to Vercel.
```bash
./scripts/deploy-vercel.sh
```

### `deploy_production.sh`
Full production deployment (backend + frontend).
```bash
./scripts/deploy_production.sh
```

## 📊 Data Management

### `ingest_sample_docs.py`
Ingests sample documents for demo purposes.
```bash
python scripts/ingest_sample_docs.py
```

### `reload_sample_data.sh`
Clears existing data and reloads sample documents.
```bash
./scripts/reload_sample_data.sh
```

**Warning**: This will delete existing vectors!

## 🔧 Environment Setup

### `generate_env_values.py`
Generates secure random values for environment variables.
```bash
python scripts/generate_env_values.py
```

### `setup_demo.sh`
Sets up a complete demo environment with sample data.
```bash
./scripts/setup_demo.sh
```

### `setup_staging.sh`
Configures staging environment.
```bash
./scripts/setup_staging.sh
```

## 🧹 Maintenance

### `cleanup.sh`
Cleans up temporary files and caches.
```bash
./scripts/cleanup.sh
```

## 📝 Script Guidelines

### Adding New Scripts

1. **Naming**: Use lowercase with underscores
2. **Shebang**: Include appropriate shebang (`#!/bin/bash` or `#!/usr/bin/env python`)
3. **Documentation**: Add header comments explaining purpose
4. **Error Handling**: Include proper error checks
5. **Idempotency**: Scripts should be safe to run multiple times

### Script Template

```bash
#!/bin/bash
# Script: script_name.sh
# Purpose: Brief description
# Usage: ./scripts/script_name.sh [options]
# Author: Your Name
# Date: YYYY-MM-DD

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Main logic
main() {
    echo "Starting script..."
    # Your code here
}

# Run main function
main "$@"
```

### Python Script Template

```python
#!/usr/bin/env python3
"""
Script: script_name.py
Purpose: Brief description
Usage: python scripts/script_name.py [options]
Author: Your Name
Date: YYYY-MM-DD
"""

import os
import sys
import argparse

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Script description')
    # Add arguments
    args = parser.parse_args()
    
    # Your code here

if __name__ == "__main__":
    main()
```

## 🔐 Security Notes

- Never commit scripts with hardcoded credentials
- Use environment variables for sensitive data
- Validate all inputs
- Log actions for audit trails

## 🧪 Testing Scripts

Before committing:
1. Test in development environment
2. Verify idempotency
3. Check error handling
4. Document any side effects

## 📞 Support

For script issues or new script requests, contact the DevOps team.