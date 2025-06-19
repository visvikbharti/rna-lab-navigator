# Frontend Troubleshooting Guide

## Issue: Frontend Shows Minimal UI Instead of Beautiful UI

### Problem Description
After modifications, the frontend was loading a minimal UI instead of the beautiful UI with animations, particle effects, glass morphism, gradient text, and purple/blue theme that was working previously.

### Root Cause
The `main.jsx` file was importing and rendering `MinimalApp` instead of the full-featured `App.jsx` component.

### Solution
Update `/frontend/src/main.jsx` to import the correct component:

```javascript
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';  // NOT MinimalApp
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

## Common Import Errors and Fixes

### 1. HeroIcons v1 to v2 Migration
When upgrading from @heroicons/react v1 to v2, icon names have changed:

| Old Import (v1) | New Import (v2) |
|-----------------|-----------------|
| `TrendingUpIcon` | `ArrowTrendingUpIcon` |
| `SearchIcon` | `MagnifyingGlassIcon` |
| `XIcon` | `XMarkIcon` |
| `FilterIcon` | `FunnelIcon` |
| `RefreshIcon` | `ArrowPathIcon` |
| `ZoomInIcon` | `MagnifyingGlassPlusIcon` |
| `ZoomOutIcon` | `MagnifyingGlassMinusIcon` |

### 2. Default vs Named Exports
Custom components use default exports, not named exports:

```javascript
// ❌ Wrong
import { Card } from './components/enhanced/Card';
import { Button } from './components/enhanced/Button';

// ✅ Correct
import Card from './components/enhanced/Card';
import Button from './components/enhanced/Button';
```

### 3. API Function Names
Ensure API imports match the actual exported function names:

```javascript
// ❌ Wrong
import { analyzeGaps } from '../api/gaps';

// ✅ Correct
import { detectKnowledgeGaps } from '../api/gaps';
```

## Localhost Connection Issue (macOS)

### Problem
On macOS, Vite dev server may start successfully but localhost:5173 refuses connections.

### Symptoms
- Vite shows "ready in X ms" but localhost doesn't work
- Browser shows "This site can't be reached" or "localhost refused to connect"
- Network IP (e.g., 192.168.40.71:5173) works fine

### Workaround
Use the network IP address shown in Vite output:
```
  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.40.71:5173/  ← Use this one!
```

## How to Start/Restart the Frontend

### Prerequisites
- Node.js v18.20.8 or higher
- npm 10.8.2 or higher
- Backend services running (if needed for API calls)

### Steps to Start Frontend

1. **Navigate to frontend directory:**
   ```bash
   cd /Users/vishalbharti/Downloads/rna-lab-navigator/frontend
   ```

2. **Install dependencies (if needed):**
   ```bash
   npm install
   ```

3. **Clear Vite cache (if having issues):**
   ```bash
   rm -rf node_modules/.vite
   ```

4. **Start the development server:**
   ```bash
   npm run dev
   ```

5. **Access the application:**
   - Try: http://localhost:5173
   - If localhost doesn't work, use the Network URL shown in terminal
   - Example: http://192.168.40.71:5173

### Quick Restart Commands
```bash
# One-liner to restart frontend
cd /Users/vishalbharti/Downloads/rna-lab-navigator/frontend && npm run dev
```

### If Frontend Won't Start

1. **Check if port 5173 is in use:**
   ```bash
   lsof -i :5173
   ```

2. **Kill any processes using the port:**
   ```bash
   kill -9 <PID>
   ```

3. **Try a different port:**
   ```bash
   npm run dev -- --port 5174
   ```

4. **Reinstall Vite if needed:**
   ```bash
   npm uninstall vite
   npm install vite@latest
   ```

## Verification Checklist

After starting the frontend, verify these features are working:

- [ ] Purple/blue gradient theme visible
- [ ] Particle animations in background
- [ ] Floating orbs animation
- [ ] Glass morphism effects on cards
- [ ] Gradient text effects
- [ ] Search functionality
- [ ] Navigation between sections
- [ ] Smooth scroll animations

## Environment Details

- **Node Version:** v18.20.8
- **npm Version:** 10.8.2
- **Vite Version:** 6.3.5
- **React Version:** 18.x
- **Key Dependencies:**
  - @heroicons/react v2
  - framer-motion
  - react-router-dom
  - tailwindcss

## Additional Notes

1. The beautiful UI includes components from `/frontend/src/components/enhanced/` directory
2. Main styling is in `/frontend/src/styles/colossal-*.css` files
3. If animations aren't working, check that framer-motion is properly installed
4. The app should automatically reload when you make changes (HMR - Hot Module Replacement)

## Contact

If you continue to experience issues after following this guide, check:
- Browser console for JavaScript errors
- Terminal for compilation errors
- Network tab for failed API requests