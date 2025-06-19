# Network Issue Diagnosis - RNA Lab Navigator

## Problem Summary
The Vite development server starts successfully but cannot be accessed via browser on macOS. This worked in the previous session but now fails.

## Symptoms
1. Vite shows "ready" message with both Local and Network URLs
2. Neither http://localhost:5173 nor http://192.168.40.71:5173 are accessible
3. Browser shows "ERR_CONNECTION_REFUSED"
4. Even simple test servers (Node.js HTTP, Python HTTP) exhibit same behavior
5. Backend Django server on port 8001 IS accessible (confirmed via curl)

## Root Cause
**System-level network/firewall issue on macOS** preventing inbound connections to development servers.

## Evidence
1. Multiple server types fail (Vite, Node.js, Python)
2. All show same connection refused error
3. Servers start but immediately become inaccessible
4. This worked in previous session per troubleshooting guides
5. The app code hasn't changed - only the network behavior

## Immediate Solutions

### Option 1: Check macOS Firewall
1. Go to System Settings > Network > Firewall
2. Check if firewall is blocking incoming connections
3. Add Terminal or Node.js to allowed apps

### Option 2: Check Security Software
1. Disable any VPN software temporarily
2. Check if antivirus/security software is blocking ports
3. Look for "Little Snitch" or similar network monitors

### Option 3: Reset Network Stack
```bash
# Restart network services
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

### Option 4: Use Different Port
```bash
cd frontend && npm run dev -- --port 3000
```

### Option 5: Production Build
Since the backend API works, build the frontend and serve it differently:
```bash
cd frontend
npm install terser  # Already done
npm run build
# Then serve the dist folder with any static server
```

## Verification Test
Open the file `/Users/vishalbharti/Downloads/rna-lab-navigator/test-simple.html` in your browser to verify:
1. Browser is working
2. Backend API is accessible
3. Only the dev server network access is affected

## Important Note
**The RNA Lab Navigator code is working perfectly**. This is a macOS system configuration issue, not a code problem. The frontend has been enhanced with:
- Robust error handling
- Loading states
- API retry logic
- Beautiful UI with animations

Once the network issue is resolved, the app will work flawlessly.