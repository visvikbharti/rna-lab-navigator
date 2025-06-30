# Authentication Issue - June 29, 2025

## Problem
The authentication system is encountering a FOREIGN KEY constraint error when trying to create JWT tokens. This is related to the token blacklisting feature.

## Error Details
```
django.db.utils.IntegrityError: FOREIGN KEY constraint failed
```

The error occurs in `OutstandingToken.objects.create()` when JWT attempts to track tokens for blacklisting.

## Temporary Solution
To access the application without fixing authentication:

1. Modify `frontend/src/App.jsx` temporarily:
   - Replace `<PrivateRoute>` with `<>` for the routes you want to access
   - Remove authentication checks

2. Or create a development mode that bypasses authentication

## Permanent Fix Needed
1. Check if `rest_framework_simplejwt.token_blacklist` migrations are properly applied
2. Verify the User model foreign key relationships
3. Consider disabling token blacklisting temporarily by setting:
   ```python
   SIMPLE_JWT = {
       ...
       'BLACKLIST_AFTER_ROTATION': False,
       ...
   }
   ```

## Users Created
- Username: `testuser`, Password: `TestPassword123!`
- Username: `admin`, Password: `AdminPassword123!`

Both users are properly created with correct passwords, but JWT token generation is failing.