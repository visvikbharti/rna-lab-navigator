// Placeholder components for planned features
import React from 'react';

const PlaceholderComponent = ({ name, description }) => (
  <div className="flex flex-col items-center justify-center min-h-[400px] text-center p-8">
    <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center mb-6">
      <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    </div>
    <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">{name}</h2>
    <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl">{description}</p>
    <div className="mt-8 px-6 py-3 bg-yellow-100 dark:bg-yellow-900/20 rounded-lg">
      <p className="text-sm text-yellow-800 dark:text-yellow-200">
        🚧 This feature is under development and will be available soon!
      </p>
    </div>
  </div>
);

export const HypothesisExplorer = () => (
  <PlaceholderComponent 
    name="Hypothesis Explorer" 
    description="AI-powered tool to generate and validate research hypotheses based on existing literature and data patterns."
  />
);

export const ProtocolBuilder = () => (
  <PlaceholderComponent 
    name="Protocol Builder" 
    description="Generate complete experimental protocols tailored to your specific research needs with AI assistance."
  />
);

export const GapExplorer = () => (
  <PlaceholderComponent 
    name="Knowledge Gap Explorer" 
    description="Discover unexplored research areas and potential breakthrough opportunities in RNA biology."
  />
);

export const CrossPaperInsights = () => (
  <PlaceholderComponent 
    name="Cross-Paper Insights" 
    description="Uncover hidden connections and patterns across multiple research papers with advanced AI analysis."
  />
);

export const KnowledgeGraphExplorer = () => (
  <PlaceholderComponent 
    name="Knowledge Graph Explorer" 
    description="Visualize complex research relationships and navigate through interconnected scientific concepts."
  />
);

export const ExperimentMapper = () => (
  <PlaceholderComponent 
    name="Experiment Mapper" 
    description="Map and analyze experimental workflows, dependencies, and outcomes across your research."
  />
);

export const MultiAgentAnalysis = () => (
  <PlaceholderComponent 
    name="Multi-Agent Analysis" 
    description="Deploy multiple AI agents to analyze research from different perspectives and generate comprehensive insights."
  />
);

export const ProtocolDesigner = () => (
  <PlaceholderComponent 
    name="AI Protocol Designer" 
    description="Design and optimize experimental protocols with AI-powered suggestions and validation."
  />
);

export const FeedbackAnalyticsDashboard = () => (
  <PlaceholderComponent 
    name="Feedback Analytics Dashboard" 
    description="Track and analyze user feedback to continuously improve the research assistant experience."
  />
);

export const SecurityAuditDashboard = () => (
  <PlaceholderComponent 
    name="Security Audit Dashboard" 
    description="Monitor system security, access patterns, and ensure research data protection."
  />
);

export const SearchQualityDashboard = () => (
  <PlaceholderComponent 
    name="Search Quality Dashboard" 
    description="Analyze and optimize search performance, accuracy, and relevance metrics."
  />
);