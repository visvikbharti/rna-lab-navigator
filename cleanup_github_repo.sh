#!/bin/bash
# Script to clean up old/experimental files from the repository
# Date: June 27, 2025

echo "🧹 Cleaning up old UI/UX and experimental files..."

# Old UI experiment files
rm -f frontend/src/SimpleSearch.jsx
rm -f frontend/src/TestApp.jsx
rm -f frontend/src/TestRoutes.jsx
rm -f frontend/src/main-debug.jsx
rm -f frontend/src/main-simple.jsx
rm -f frontend/src/main-with-router.jsx
rm -f frontend/src/components/SimpleSearchBox.jsx
rm -f frontend/src/pages/ColossalDemo.jsx
rm -f frontend/src/pages/ColossalShowcase.jsx
rm -f frontend/src/pages/HomeSimple.jsx

# Remove entire enhanced components directory (old UI experiments)
rm -rf frontend/src/components/enhanced/

# Old style files
rm -f frontend/src/styles/app-clean.css
rm -f frontend/src/styles/colossal-*.css
rm -f frontend/src/styles/particle-animations.css
rm -f frontend/src/styles/ripple-animation.css

# Disabled/unimplemented features
rm -f frontend/src/components/DisabledFeatures.js
rm -f frontend/src/components/MultiAgentAnalysis.jsx
rm -f frontend/src/components/KnowledgeGapHeatmap.jsx
rm -f frontend/src/components/ProtocolBuilder.jsx
rm -f frontend/src/components/ProtocolDesigner.jsx
rm -f frontend/src/components/HypothesisExplorer.jsx
rm -f frontend/src/components/ExperimentMapper.jsx
rm -f frontend/src/components/BatchProcessingManager.jsx
rm -f frontend/src/components/SecurityAuditDashboard.jsx
rm -f frontend/src/components/FeedbackAnalyticsDashboard.jsx
rm -f frontend/src/components/SearchQualityDashboard.jsx
rm -f frontend/src/components/ResearchConnectionGraph.jsx
rm -f frontend/src/components/TopicEvolutionTimeline.jsx
rm -f frontend/src/components/CrossPaperInsights.jsx
rm -f frontend/src/components/GapExplorer.jsx
rm -f frontend/src/components/KnowledgeGraphExplorer.jsx
rm -f frontend/src/components/PaperDashboard.jsx
rm -f frontend/src/components/ProtocolUploader.jsx
rm -f frontend/src/components/SavedSearches.jsx
rm -f frontend/src/components/SearchWithGaps.jsx
rm -f frontend/src/components/EnhancedSearchInterface.jsx
rm -f frontend/src/components/AdvancedSearchBox.jsx
rm -f frontend/src/components/AdvancedSearchFilters.jsx
rm -f frontend/src/components/OptimizedSearchBox.jsx
rm -f frontend/src/components/SearchFacets.jsx
rm -f frontend/src/components/SearchRankingSelector.jsx
rm -f frontend/src/components/ReasoningTraceDisplay.jsx
rm -f frontend/src/components/EnhancedChatBox.jsx
rm -f frontend/src/components/EnhancedFeedbackForm.jsx
rm -f frontend/src/components/FeedbackAnalyticsSummary.jsx
rm -f frontend/src/pages/KnowledgeGapDashboard.jsx

# Remove unimplemented backend modules
rm -rf backend/api/agents/
rm -rf backend/api/experiments/
rm -rf backend/api/hypothesis/
rm -rf backend/api/protocols/
rm -rf backend/api/papers/
rm -rf backend/api/knowledge_graph/

# Old/unused API files
rm -f frontend/src/api/experiments.js
rm -f frontend/src/api/hypothesis.js
rm -f frontend/src/api/gaps.js
rm -f frontend/src/api/knowledge-graph.js
rm -f frontend/src/api/search-quality.js
rm -f frontend/src/api/intelligence.js
rm -f frontend/src/api/enhanced-rag.js

# Archive directory (old documentation)
rm -rf docs/archive/

# Animation-related files (if not used)
rm -f frontend/src/contexts/AnimationContext.jsx
rm -f frontend/ANIMATION_AUDIT.md
rm -f frontend/ANIMATION_DEPENDENCIES.md

# Old test files for removed components
rm -f frontend/src/components/__tests__/SearchQualityDashboard.test.jsx
rm -f frontend/src/__tests__/EnhancedSearchInterface.test.jsx

# Demo files
rm -f frontend/demo.html

# Count removed files
echo "✅ Cleanup complete!"
echo "📊 Files removed: $(git status --porcelain | grep -c '^D')"