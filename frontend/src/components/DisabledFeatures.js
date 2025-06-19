// Temporarily disabled features to prevent 404 errors
export const DISABLED_FEATURES = {
  // Search suggestions - not implemented yet
  SEARCH_SUGGESTIONS: true,
  SEARCH_AUTOCOMPLETE: true,
  SEARCH_FACETS: true,
  
  // Analytics features - endpoints missing
  FEEDBACK_ANALYSIS: true,
  FEEDBACK_THEMES: true,
  SEARCH_QUALITY_METRICS: true,
  
  // Security features - requires auth
  SECURITY_DASHBOARD: true,
  SECURITY_EVENTS: true
};

// Helper function to check if feature is enabled
export const isFeatureEnabled = (feature) => {
  return !DISABLED_FEATURES[feature];
};