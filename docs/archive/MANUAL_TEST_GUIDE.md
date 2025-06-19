# RNA Lab Navigator - Manual Testing Guide

Since you have Node v16, here's a manual testing checklist to verify everything works:

## 🎯 Core Features to Test (Using REAL Data)

### 1. Main Search (REAL DATA)
1. Go to http://localhost:5173/
2. Search for: "CRISPR-Cas9 protocol"
3. **Expected**: 
   - Answer cites real papers (Kumar, Phutela, etc.)
   - Shows confidence score
   - Response time <5s with o4-mini model

### 2. Different Query Types
Test these to see model routing in action:

**Simple Query** (uses gpt-4.1-mini):
- "What is RNA?"
- Should be fast (<2s)

**Research Query** (uses o4-mini):
- "Design protocol for RNA extraction from brain tissue"
- More detailed, thoughtful response

**Complex Query** (uses gpt-4.1):
- "Compare CRISPR-Cas9, Cas12, and base editing approaches"
- Comprehensive analysis

### 3. Navigation Test
Click through all pages:
- ✅ Home
- ✅ Analytics Dashboard
- ✅ Search Quality  
- ✅ Upload Protocol
- ✅ Security Audit
- ✅ Component Demo
- ✅ Experiment Mapper

### 4. Features Using Mock Data (UI Only)
These show mock data but don't affect search:
- Search suggestions dropdown
- Trending/popular queries
- Analytics charts
- Security dashboard (requires auth)

## 🔍 How to Verify REAL vs Mock Data

### REAL Data Indicators:
1. **Citations** - References actual papers in your database
2. **Confidence scores** - Vary based on document relevance
3. **Processing time** - Shows actual API response time
4. **Query history** - Persists across sessions

### Mock Data Indicators:
1. **Static values** - Same suggestions every time
2. **No 404 errors** - Clean console
3. **Instant loading** - No API delay

## 📸 What to Check Visually

1. **Navigation Visibility**
   - Text should be clearly visible
   - White text on enhanced UI
   - Dark text on classic UI

2. **Search Results**
   - Citations formatted correctly
   - Sources listed with titles/authors
   - Confidence score displayed

3. **Performance**
   - No console errors
   - Smooth transitions
   - Fast response times

## 🧪 Quick API Test
Run this in terminal to verify backend:
```bash
# Test real query
curl -X POST http://localhost:8000/api/query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "RNA polymerase"}' | json_pp

# Check cache
curl http://localhost:8000/api/cache/ | json_pp
```

## ✅ Success Criteria
- [x] Search returns real citations from your documents
- [x] o4-mini model provides thoughtful answers
- [x] Navigation works across all pages
- [x] No 404/401 errors in console
- [x] Response times <5s for most queries

Remember: **All search queries use REAL data!** Mock data is only for unimplemented UI features.