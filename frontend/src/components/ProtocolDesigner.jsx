import React, { useState } from 'react';
import {
  BeakerIcon,
  ClockIcon,
  CurrencyDollarIcon,
  ExclamationTriangleIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import api from '../api/client';

const ProtocolDesigner = ({ initialHypothesis = '' }) => {
  const [hypothesis, setHypothesis] = useState(initialHypothesis);
  const [constraints, setConstraints] = useState({
    time: '1 week',
    budget: '$1000',
    equipment: 'Standard lab equipment'
  });
  const [protocol, setProtocol] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeSection, setActiveSection] = useState('overview');

  const generateProtocol = async () => {
    if (!hypothesis.trim()) {
      setError("Please enter a hypothesis");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/api/agents/design-protocol/', {
        hypothesis,
        constraints
      });

      setProtocol(response.data.protocol);
      setActiveSection('overview');
    } catch (err) {
      setError(err.response?.data?.error || "Protocol generation failed");
    } finally {
      setLoading(false);
    }
  };

  const exportProtocol = () => {
    if (!protocol) return;

    const content = `
# ${protocol.protocol_name}

## Overview
**Objective:** ${protocol.overview.objective}
**Approach:** ${protocol.overview.approach}
**Expected Outcomes:** ${protocol.overview.expected_outcomes}

## Materials
${Object.entries(protocol.materials).map(([category, items]) => 
  `### ${category}\n${items.map(item => `- ${item}`).join('\n')}`
).join('\n\n')}

## Methods
${protocol.methods.map((method, idx) => 
  `### Step ${idx + 1}: ${method.action}
Details: ${method.details}
Duration: ${method.duration}
${method.critical ? '⚠️ CRITICAL STEP' : ''}
${method.safety ? `Safety: ${method.safety}` : ''}`
).join('\n\n')}

## Timeline
Total Duration: ${protocol.timeline.total_duration}

## Estimated Cost
${protocol.estimated_cost.total_estimated}
    `;

    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${protocol.protocol_name.replace(/\s+/g, '_')}.md`;
    a.click();
  };

  const renderOverview = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Protocol Overview</h3>
        <div className="bg-gray-50 p-4 rounded-lg space-y-3">
          <div>
            <span className="font-medium text-gray-700">Objective:</span>
            <p className="text-gray-600 mt-1">{protocol.overview.objective}</p>
          </div>
          <div>
            <span className="font-medium text-gray-700">Approach:</span>
            <p className="text-gray-600 mt-1">{protocol.overview.approach}</p>
          </div>
          <div>
            <span className="font-medium text-gray-700">Expected Outcomes:</span>
            <p className="text-gray-600 mt-1">{protocol.overview.expected_outcomes}</p>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-blue-50 p-4 rounded-lg text-center">
          <ClockIcon className="h-8 w-8 text-blue-600 mx-auto mb-2" />
          <p className="text-sm text-gray-600">Duration</p>
          <p className="font-semibold text-gray-900">{protocol.timeline.total_duration}</p>
        </div>
        <div className="bg-green-50 p-4 rounded-lg text-center">
          <CurrencyDollarIcon className="h-8 w-8 text-green-600 mx-auto mb-2" />
          <p className="text-sm text-gray-600">Estimated Cost</p>
          <p className="font-semibold text-gray-900">{protocol.estimated_cost.total_estimated}</p>
        </div>
        <div className="bg-purple-50 p-4 rounded-lg text-center">
          <BeakerIcon className="h-8 w-8 text-purple-600 mx-auto mb-2" />
          <p className="text-sm text-gray-600">Total Steps</p>
          <p className="font-semibold text-gray-900">{protocol.methods.length}</p>
        </div>
      </div>
    </div>
  );

  const renderMethods = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900 mb-3">Step-by-Step Methods</h3>
      {protocol.methods.map((method, idx) => (
        <div 
          key={idx} 
          className={`p-4 rounded-lg border-2 ${
            method.critical ? 'border-red-300 bg-red-50' : 'border-gray-200 bg-white'
          }`}
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h4 className="font-medium text-gray-900">
                Step {method.step_number}: {method.action}
              </h4>
              {method.details && (
                <p className="text-gray-600 mt-2">{method.details}</p>
              )}
              <div className="flex items-center space-x-4 mt-3 text-sm">
                <span className="text-gray-500">
                  <ClockIcon className="h-4 w-4 inline mr-1" />
                  {method.duration}
                </span>
                {method.critical && (
                  <span className="text-red-600 font-medium">
                    <ExclamationTriangleIcon className="h-4 w-4 inline mr-1" />
                    Critical Step
                  </span>
                )}
              </div>
              {method.safety && (
                <div className="mt-2 p-2 bg-yellow-100 rounded text-sm text-yellow-800">
                  ⚠️ Safety: {method.safety}
                </div>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );

  const renderMaterials = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-3">Required Materials</h3>
      {Object.entries(protocol.materials).map(([category, items]) => (
        <div key={category} className="bg-gray-50 p-4 rounded-lg">
          <h4 className="font-medium text-gray-900 mb-2 capitalize">
            {category.replace(/_/g, ' ')}
          </h4>
          <ul className="space-y-1">
            {items.map((item, idx) => (
              <li key={idx} className="text-gray-600 flex items-start">
                <span className="text-gray-400 mr-2">•</span>
                {item}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );

  const renderControls = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900 mb-3">Experimental Controls</h3>
      {protocol.controls.map((control, idx) => (
        <div key={idx} className="bg-blue-50 p-4 rounded-lg">
          <h4 className="font-medium text-gray-900 capitalize">{control.type}</h4>
          <p className="text-gray-600 mt-1">{control.purpose}</p>
          <p className="text-sm text-gray-500 mt-2">Setup: {control.setup}</p>
        </div>
      ))}
    </div>
  );

  const renderSafety = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900 mb-3">Safety Considerations</h3>
      {protocol.safety_considerations.length > 0 ? (
        protocol.safety_considerations.map((safety, idx) => (
          <div key={idx} className="bg-yellow-50 p-4 rounded-lg">
            <h4 className="font-medium text-gray-900">{safety.type} Hazard</h4>
            <p className="text-gray-600 mt-1">{safety.concern}</p>
            <p className="text-sm text-gray-700 mt-2">
              <strong>Precautions:</strong> {safety.precautions}
            </p>
            <p className="text-sm text-gray-700">
              <strong>PPE Required:</strong> {safety.ppe}
            </p>
          </div>
        ))
      ) : (
        <p className="text-gray-600">No special safety considerations identified.</p>
      )}
    </div>
  );

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="bg-white rounded-xl shadow-lg p-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            AI Protocol Designer
          </h2>
          <p className="text-gray-600">
            Generate complete experimental protocols from your hypothesis
          </p>
        </div>

        {/* Input Section */}
        <div className="mb-8 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Your Hypothesis
            </label>
            <textarea
              value={hypothesis}
              onChange={(e) => setHypothesis(e.target.value)}
              placeholder="Enter your hypothesis... e.g., 'If we pre-treat cells with NAC before transfection, it will increase CRISPR efficiency'"
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={3}
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Time Constraint
              </label>
              <input
                type="text"
                value={constraints.time}
                onChange={(e) => setConstraints({...constraints, time: e.target.value})}
                className="w-full p-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Budget
              </label>
              <input
                type="text"
                value={constraints.budget}
                onChange={(e) => setConstraints({...constraints, budget: e.target.value})}
                className="w-full p-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Equipment
              </label>
              <input
                type="text"
                value={constraints.equipment}
                onChange={(e) => setConstraints({...constraints, equipment: e.target.value})}
                className="w-full p-2 border border-gray-300 rounded-lg"
              />
            </div>
          </div>

          <button
            onClick={generateProtocol}
            disabled={loading || !hypothesis.trim()}
            className="w-full py-3 px-6 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-medium rounded-lg hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {loading ? (
              <>
                <ArrowPathIcon className="h-5 w-5 mr-2 animate-spin" />
                Designing protocol...
              </>
            ) : (
              <>
                <BeakerIcon className="h-5 w-5 mr-2" />
                Generate Protocol
              </>
            )}
          </button>

          {error && (
            <p className="text-red-600 text-sm text-center">{error}</p>
          )}
        </div>

        {/* Results Section */}
        {protocol && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-gray-900">{protocol.protocol_name}</h3>
              <button
                onClick={exportProtocol}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center"
              >
                <DocumentTextIcon className="h-5 w-5 mr-2" />
                Export Protocol
              </button>
            </div>

            {/* Navigation Tabs */}
            <div className="border-b border-gray-200 mb-6">
              <nav className="-mb-px flex space-x-8">
                {['overview', 'methods', 'materials', 'controls', 'safety'].map(section => (
                  <button
                    key={section}
                    onClick={() => setActiveSection(section)}
                    className={`py-2 px-1 border-b-2 font-medium text-sm capitalize ${
                      activeSection === section
                        ? 'border-purple-500 text-purple-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    {section}
                  </button>
                ))}
              </nav>
            </div>

            {/* Content */}
            <div>
              {activeSection === 'overview' && renderOverview()}
              {activeSection === 'methods' && renderMethods()}
              {activeSection === 'materials' && renderMaterials()}
              {activeSection === 'controls' && renderControls()}
              {activeSection === 'safety' && renderSafety()}
            </div>

            {/* Validation Status */}
            {protocol.validation && (
              <div className={`mt-6 p-4 rounded-lg ${
                protocol.validation.is_valid ? 'bg-green-50' : 'bg-yellow-50'
              }`}>
                <div className="flex items-center">
                  <CheckCircleIcon className={`h-5 w-5 mr-2 ${
                    protocol.validation.is_valid ? 'text-green-600' : 'text-yellow-600'
                  }`} />
                  <span className="font-medium">
                    Protocol Feasibility: {protocol.validation.feasibility_score}%
                  </span>
                </div>
                {protocol.validation.warnings.length > 0 && (
                  <ul className="mt-2 space-y-1">
                    {protocol.validation.warnings.map((warning, idx) => (
                      <li key={idx} className="text-sm text-gray-600">• {warning}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ProtocolDesigner;