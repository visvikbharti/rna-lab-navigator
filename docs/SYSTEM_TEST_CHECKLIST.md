# RNA Lab Navigator - System Test Checklist
**Pre-Beta Testing Verification**

## 1. Authentication System ✓

### Frontend Tests
- [ ] Login page loads correctly
- [ ] Login with correct credentials works
- [ ] Login with incorrect credentials shows error
- [ ] Logout functionality works
- [ ] Token stored in localStorage as 'access_token'
- [ ] Refresh token mechanism works
- [ ] Protected routes redirect to login when not authenticated

### Backend Tests
- [ ] `/api/auth/login/` endpoint accepts POST requests
- [ ] Returns access and refresh tokens
- [ ] `/api/auth/logout/` invalidates tokens
- [ ] `/api/auth/refresh/` generates new access token
- [ ] Token expiry working (15 min access, 1 day refresh)

### Test Credentials
```
Username: admin
Password: GODisone@1
```

## 2. CORS Configuration ✓

### Required Tests
- [ ] Frontend can call backend API without CORS errors
- [ ] Preflight requests succeed
- [ ] Cookies/credentials included in requests
- [ ] All Vercel deployment URLs whitelisted

### Test Commands
```bash
# Test from frontend console
fetch('https://rnalab.pythonanywhere.com/api/auth/profile/', {
  credentials: 'include',
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('access_token')
  }
})
```

## 3. Document Upload & Processing ✓

### Upload Tests
- [ ] PDF upload works
- [ ] File size limits enforced (10MB)
- [ ] Progress indicator shows
- [ ] Success/error messages display
- [ ] Uploaded documents appear in library

### Processing Tests
- [ ] Text extraction successful
- [ ] Chunking creates appropriate segments
- [ ] Metadata extraction works
- [ ] Embeddings generated
- [ ] Documents searchable immediately

## 4. RAG Query System ✓

### Query Tests
- [ ] Natural language queries accepted
- [ ] Response time < 5 seconds
- [ ] Citations included in responses
- [ ] Confidence scores displayed
- [ ] Follow-up questions work

### Test Queries
1. "What is the protocol for RNA extraction?"
2. "Compare CRISPR and RNAi efficiency"
3. "What are the latest findings on non-coding RNA?"
4. "Show me Rhythm's thesis conclusions"
5. "What buffer is used in Protocol_2023?"

## 5. Performance Metrics ✓

### Response Times
- [ ] Login: < 2 seconds
- [ ] Document list load: < 1 second
- [ ] Query response: < 5 seconds
- [ ] Document upload: < 30 seconds
- [ ] Page navigation: < 1 second

### Concurrent Users
- [ ] Test with 5 simultaneous users
- [ ] No performance degradation
- [ ] All users get responses

## 6. Security Checks ✓

### Authentication Security
- [ ] Passwords hashed (not visible in DB)
- [ ] Brute force protection active (5 attempts)
- [ ] Session timeout works (30 min)
- [ ] No sensitive data in logs

### Data Security
- [ ] Documents encrypted at rest
- [ ] HTTPS enforced
- [ ] No API keys exposed in frontend
- [ ] User isolation working

## 7. Error Handling ✓

### Frontend Errors
- [ ] Network errors show user-friendly messages
- [ ] 404 pages handled gracefully
- [ ] Form validation messages clear
- [ ] Loading states for all async operations

### Backend Errors
- [ ] 500 errors logged but not exposed
- [ ] Rate limiting messages clear
- [ ] Database errors handled
- [ ] External API failures graceful

## 8. Browser Compatibility ✓

### Desktop Browsers
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

### Responsive Design
- [ ] Desktop (1920x1080)
- [ ] Laptop (1366x768)
- [ ] Tablet (768x1024)
- [ ] Mobile (375x667) - basic support

## 9. Critical User Flows ✓

### Flow 1: First Time User
1. [ ] Navigate to site
2. [ ] Click login
3. [ ] Enter credentials
4. [ ] View onboarding
5. [ ] Ask first question
6. [ ] Get helpful response

### Flow 2: Returning User
1. [ ] Login quickly
2. [ ] See conversation history
3. [ ] Continue previous query
4. [ ] Upload new document
5. [ ] Search uploaded doc

### Flow 3: Research Task
1. [ ] Ask complex question
2. [ ] Review citations
3. [ ] Click through to source
4. [ ] Ask follow-up
5. [ ] Save useful info

## 10. Data Verification ✓

### Existing Content
- [ ] All demo documents loaded
- [ ] Rhythm's thesis accessible
- [ ] Lab protocols searchable
- [ ] Papers have correct metadata

### New Content
- [ ] Can upload new PDF
- [ ] Appears in search results
- [ ] Citations work correctly
- [ ] No data corruption

## Test Environment URLs

**Frontend**: https://rna-lab-navigator-production-ctbr1wtbw.vercel.app  
**Backend API**: https://rnalab.pythonanywhere.com/api/  
**Admin Panel**: https://rnalab.pythonanywhere.com/admin/

## Issue Tracking

| Test | Status | Issue | Resolution |
|------|--------|-------|------------|
| CORS | ❌ | Blocking frontend | Update PythonAnywhere |
| Auth | ✓ | Working | - |
| Upload | ? | Not tested | Test after CORS fix |

## Sign-off

**Tested by**: _______________________  
**Date**: _______________________  
**Ready for Beta**: Yes / No  

**Notes**: 
_________________________________________________________________
_________________________________________________________________

---

*Use this checklist before releasing to beta testers*