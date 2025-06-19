# Quick Fix for Demo

## The Issue:
The "Default Search" button you see is actually a dropdown for selecting search ranking profiles, not the search button itself. The actual search button is to the right of it.

## Two Options to Fix:

### Option 1: Use the Current Interface (Immediate)
1. Type your query in the text box
2. **Click the button on the RIGHT** (it might say "Search", "Enhanced Search", or "Multi-Hop Search")
3. **DO NOT click "Default Search"** - that's a dropdown menu for ranking options

### Option 2: Use Simple Search Interface (Better for Demo)
1. Go to: **http://localhost:5173/simple**
2. This has a clean, simple search interface with just one search button
3. No confusing dropdowns or options

## Recommended Demo Flow:

### Using Simple Search (http://localhost:5173/simple):
1. Navigate to the simple search page
2. Click on example queries or type your own
3. Click the blue "Search" button
4. Results appear below

### Example Queries to Demo:
```
What are the key findings from Rhythm Phutela's PhD thesis on RNA dynamics?
```
```
How do I extract RNA using TRIzol?
```
```
What are best practices for CRISPR guide RNA design?
```

## Why This Happened:
The UI has a "SearchRankingSelector" component that looks like a search button but is actually a dropdown menu. This is confusing UX that we've now bypassed with the simple search interface.

## For Your Presentation:
Use **http://localhost:5173/simple** - it's cleaner and less confusing!