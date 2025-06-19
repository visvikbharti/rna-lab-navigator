// Mock data for endpoints that aren't implemented yet
// This prevents 404 errors and keeps the UI functional

export const mockSearchQualitySummary = {
  overall_metrics: {
    total_searches: 1542,
    avg_confidence_score: 0.82,
    avg_response_time: 2.3,
    successful_searches: 1389,
    failed_searches: 153
  },
  trending_metrics: {
    searches_today: 47,
    searches_this_week: 312,
    searches_this_month: 1542,
    growth_rate: "+15%"
  }
};

export const mockQualityByDocType = {
  metrics: [
    { doc_type: "protocol", avg_confidence: 0.85, total_searches: 523, avg_time: 2.1 },
    { doc_type: "paper", avg_confidence: 0.83, total_searches: 687, avg_time: 2.4 },
    { doc_type: "thesis", avg_confidence: 0.78, total_searches: 332, avg_time: 2.5 }
  ]
};

export const mockFeedbackAnalysis = {
  total_feedback: 287,
  positive_feedback: 241,
  negative_feedback: 46,
  average_rating: 4.2,
  categories: [
    { category: "Accuracy", count: 89, sentiment: "positive" },
    { category: "Relevance", count: 76, sentiment: "positive" },
    { category: "Speed", count: 54, sentiment: "positive" },
    { category: "Missing Info", count: 32, sentiment: "negative" },
    { category: "Wrong Answer", count: 14, sentiment: "negative" }
  ]
};

export const mockFeedbackThemes = {
  themes: [
    { theme: "RNA protocols very helpful", count: 45, sentiment: "positive" },
    { theme: "Need more recent papers", count: 23, sentiment: "negative" },
    { theme: "o4-mini model improvement noticed", count: 18, sentiment: "positive" },
    { theme: "Search is much faster now", count: 31, sentiment: "positive" }
  ]
};

export const mockSecuritySummary = {
  status: "healthy",
  blocked_ips: 3,
  rate_limit_hits: 12,
  suspicious_requests: 0,
  last_scan: new Date().toISOString(),
  threat_level: "low"
};

export const mockPerformanceData = (days = 30) => {
  const data = [];
  const now = new Date();
  
  for (let i = days; i > 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    
    data.push({
      date: date.toISOString().split('T')[0],
      avg_confidence: 0.75 + Math.random() * 0.15,
      total_searches: Math.floor(30 + Math.random() * 50),
      avg_response_time: 1.8 + Math.random() * 1.2
    });
  }
  
  return { data, interval: "day" };
};