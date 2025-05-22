import React, { useState, useEffect } from 'react';
import { 
  getSecurityDashboardSummary, 
  getSecurityHealthCheck,
  getSecurityEvents,
  getBlockedIPs,
  blockIP,
  unblockIP,
  getSecurityIncidents,
  updateIncidentStatus,
  getWAFAlerts,
  markWAFAlertAsFalsePositive
} from '../api/security';

/**
 * Security Audit Dashboard Component
 * Provides comprehensive security monitoring and administration interface
 */
const SecurityAuditDashboard = () => {
  // State for dashboard data
  const [summaryData, setSummaryData] = useState(null);
  const [healthCheck, setHealthCheck] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // State for specific sections
  const [securityEvents, setSecurityEvents] = useState([]);
  const [blockedIPs, setBlockedIPs] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [wafAlerts, setWafAlerts] = useState([]);
  
  // State for IP blocking form
  const [ipBlockForm, setIpBlockForm] = useState({
    ipAddress: '',
    reason: 'manual',
    isPermanent: false,
    durationHours: 24,
    description: ''
  });
  
  // Load initial dashboard data
  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Load dashboard summary
        const summary = await getSecurityDashboardSummary();
        setSummaryData(summary);
        
        // Load health check
        const health = await getSecurityHealthCheck();
        setHealthCheck(health);
        
        setLoading(false);
      } catch (err) {
        setError('Failed to load security dashboard data');
        setLoading(false);
        console.error('Error loading security dashboard:', err);
      }
    };
    
    loadDashboardData();
  }, []);
  
  // Load data for specific tabs when they're activated
  useEffect(() => {
    const loadTabData = async () => {
      try {
        setLoading(true);
        
        if (activeTab === 'events') {
          const events = await getSecurityEvents();
          setSecurityEvents(events.results || []);
        } else if (activeTab === 'blocked-ips') {
          const ips = await getBlockedIPs();
          setBlockedIPs(ips.results || []);
        } else if (activeTab === 'incidents') {
          const securityIncidents = await getSecurityIncidents();
          setIncidents(securityIncidents.results || []);
        } else if (activeTab === 'waf') {
          const alerts = await getWAFAlerts();
          setWafAlerts(alerts.results || []);
        }
        
        setLoading(false);
      } catch (err) {
        setError(`Failed to load data for ${activeTab} tab`);
        setLoading(false);
        console.error(`Error loading ${activeTab} data:`, err);
      }
    };
    
    if (activeTab !== 'overview' && activeTab !== 'health') {
      loadTabData();
    }
  }, [activeTab]);
  
  // Handle IP block form submission
  const handleBlockIP = async (e) => {
    e.preventDefault();
    
    try {
      setLoading(true);
      await blockIP(ipBlockForm);
      
      // Refresh the blocked IPs list
      const ips = await getBlockedIPs();
      setBlockedIPs(ips.results || []);
      
      // Reset form
      setIpBlockForm({
        ipAddress: '',
        reason: 'manual',
        isPermanent: false,
        durationHours: 24,
        description: ''
      });
      
      setLoading(false);
    } catch (err) {
      setError('Failed to block IP address');
      setLoading(false);
      console.error('Error blocking IP:', err);
    }
  };
  
  // Handle IP unblock
  const handleUnblockIP = async (id) => {
    try {
      setLoading(true);
      await unblockIP(id);
      
      // Refresh the blocked IPs list
      const ips = await getBlockedIPs();
      setBlockedIPs(ips.results || []);
      
      setLoading(false);
    } catch (err) {
      setError('Failed to unblock IP address');
      setLoading(false);
      console.error('Error unblocking IP:', err);
    }
  };
  
  // Handle marking WAF alert as false positive
  const handleMarkFalsePositive = async (id, notes = '') => {
    try {
      setLoading(true);
      await markWAFAlertAsFalsePositive(id, notes);
      
      // Refresh the WAF alerts list
      const alerts = await getWAFAlerts();
      setWafAlerts(alerts.results || []);
      
      setLoading(false);
    } catch (err) {
      setError('Failed to mark WAF alert as false positive');
      setLoading(false);
      console.error('Error marking WAF alert as false positive:', err);
    }
  };
  
  // Handle updating incident status
  const handleUpdateIncidentStatus = async (id, newStatus, additionalData = {}) => {
    try {
      setLoading(true);
      
      const data = {
        status: newStatus,
        ...additionalData
      };
      
      await updateIncidentStatus(id, data);
      
      // Refresh the incidents list
      const securityIncidents = await getSecurityIncidents();
      setIncidents(securityIncidents.results || []);
      
      setLoading(false);
    } catch (err) {
      setError('Failed to update incident status');
      setLoading(false);
      console.error('Error updating incident status:', err);
    }
  };
  
  // Handle form input changes
  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setIpBlockForm({
      ...ipBlockForm,
      [name]: type === 'checkbox' ? checked : value
    });
  };
  
  // Render the appropriate tab content
  const renderTabContent = () => {
    if (loading) {
      return <div className="flex justify-center p-8">Loading...</div>;
    }
    
    if (error) {
      return <div className="text-red-500 p-4">{error}</div>;
    }
    
    switch (activeTab) {
      case 'overview':
        return renderOverviewTab();
      case 'health':
        return renderHealthCheckTab();
      case 'events':
        return renderSecurityEventsTab();
      case 'blocked-ips':
        return renderBlockedIPsTab();
      case 'incidents':
        return renderIncidentsTab();
      case 'waf':
        return renderWAFAlertsTab();
      default:
        return renderOverviewTab();
    }
  };
  
  // Render overview tab with summary metrics
  const renderOverviewTab = () => {
    if (!summaryData) {
      return <div>No summary data available</div>;
    }
    
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
        {/* Security metrics cards */}
        <div className="bg-white shadow rounded-lg p-4">
          <h3 className="text-lg font-semibold mb-2">Security Incidents</h3>
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-gray-100 p-3 rounded">
              <div className="text-2xl font-bold">{summaryData.metrics.total_incidents}</div>
              <div className="text-sm text-gray-600">Total</div>
            </div>
            <div className="bg-red-100 p-3 rounded">
              <div className="text-2xl font-bold">{summaryData.metrics.open_incidents}</div>
              <div className="text-sm text-gray-600">Open</div>
            </div>
            <div className="bg-orange-100 p-3 rounded">
              <div className="text-2xl font-bold">{summaryData.metrics.critical_incidents}</div>
              <div className="text-sm text-gray-600">Critical</div>
            </div>
          </div>
        </div>
        
        <div className="bg-white shadow rounded-lg p-4">
          <h3 className="text-lg font-semibold mb-2">Last 24 Hours</h3>
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-blue-100 p-3 rounded">
              <div className="text-2xl font-bold">{summaryData.metrics.security_events_24h}</div>
              <div className="text-sm text-gray-600">Security Events</div>
            </div>
            <div className="bg-yellow-100 p-3 rounded">
              <div className="text-2xl font-bold">{summaryData.metrics.waf_alerts_24h}</div>
              <div className="text-sm text-gray-600">WAF Alerts</div>
            </div>
            <div className="bg-red-100 p-3 rounded">
              <div className="text-2xl font-bold">{summaryData.metrics.failed_logins_24h}</div>
              <div className="text-sm text-gray-600">Failed Logins</div>
            </div>
            <div className="bg-purple-100 p-3 rounded">
              <div className="text-2xl font-bold">{summaryData.metrics.suspicious_activities_24h}</div>
              <div className="text-sm text-gray-600">Suspicious Activities</div>
            </div>
          </div>
        </div>
        
        <div className="bg-white shadow rounded-lg p-4">
          <h3 className="text-lg font-semibold mb-2">Active Protection</h3>
          <div className="grid grid-cols-1 gap-2">
            <div className="bg-blue-100 p-3 rounded">
              <div className="text-2xl font-bold">{summaryData.metrics.blocked_ips}</div>
              <div className="text-sm text-gray-600">Blocked IPs</div>
            </div>
          </div>
        </div>
        
        {/* Top attack vectors */}
        <div className="bg-white shadow rounded-lg p-4 md:col-span-2">
          <h3 className="text-lg font-semibold mb-2">Top Attack Vectors (Last 7 Days)</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Attack Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Count
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {summaryData.top_attack_vectors.map((vector, index) => (
                  <tr key={index}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {vector.attack_type}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{vector.count}</div>
                    </td>
                  </tr>
                ))}
                {summaryData.top_attack_vectors.length === 0 && (
                  <tr>
                    <td colSpan="2" className="px-6 py-4 text-center text-sm text-gray-500">
                      No attack vectors detected in the last 7 days
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
        
        {/* Recent security incidents */}
        <div className="bg-white shadow rounded-lg p-4 md:col-span-3">
          <h3 className="text-lg font-semibold mb-2">Recent Security Incidents</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Severity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Detected
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Description
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {summaryData.recent_incidents.map((incident) => (
                  <tr key={incident.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {incident.incident_type}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                        ${incident.severity === 'critical' ? 'bg-red-100 text-red-800' : 
                          incident.severity === 'high' ? 'bg-orange-100 text-orange-800' : 
                          incident.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' : 
                          'bg-green-100 text-green-800'}`}>
                        {incident.severity}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                        ${incident.status === 'detected' || incident.status === 'investigating' ? 'bg-red-100 text-red-800' : 
                          incident.status === 'contained' ? 'bg-yellow-100 text-yellow-800' : 
                          'bg-green-100 text-green-800'}`}>
                        {incident.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {new Date(incident.detected_at).toLocaleDateString()}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900 truncate max-w-xs">
                        {incident.description}
                      </div>
                    </td>
                  </tr>
                ))}
                {summaryData.recent_incidents.length === 0 && (
                  <tr>
                    <td colSpan="5" className="px-6 py-4 text-center text-sm text-gray-500">
                      No recent security incidents
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };
  
  // Render health check tab
  const renderHealthCheckTab = () => {
    if (!healthCheck) {
      return <div>No health check data available</div>;
    }
    
    const getStatusClass = (status) => {
      switch (status) {
        case 'critical':
          return 'text-red-600 bg-red-100';
        case 'at_risk':
          return 'text-orange-600 bg-orange-100';
        case 'warning':
          return 'text-yellow-600 bg-yellow-100';
        case 'healthy':
          return 'text-green-600 bg-green-100';
        default:
          return 'text-gray-600 bg-gray-100';
      }
    };
    
    const getSeverityClass = (severity) => {
      switch (severity) {
        case 'critical':
          return 'text-red-600 bg-red-100';
        case 'high':
          return 'text-orange-600 bg-orange-100';
        case 'medium':
          return 'text-yellow-600 bg-yellow-100';
        case 'low':
          return 'text-green-600 bg-green-100';
        default:
          return 'text-gray-600 bg-gray-100';
      }
    };
    
    return (
      <div className="p-4">
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-semibold">Security Health Status</h3>
            <span className={`px-4 py-1 rounded-full font-semibold ${getStatusClass(healthCheck.status)}`}>
              {healthCheck.status.replace('_', ' ').toUpperCase()}
            </span>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-100 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold">{healthCheck.checks_performed}</div>
              <div className="text-sm text-gray-600">Checks Performed</div>
            </div>
            <div className="bg-red-100 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-red-700">{healthCheck.critical_issues}</div>
              <div className="text-sm text-gray-600">Critical Issues</div>
            </div>
            <div className="bg-orange-100 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-orange-700">{healthCheck.high_issues}</div>
              <div className="text-sm text-gray-600">High Issues</div>
            </div>
            <div className="bg-yellow-100 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-yellow-700">{healthCheck.medium_issues}</div>
              <div className="text-sm text-gray-600">Medium Issues</div>
            </div>
          </div>
          
          <div className="mb-4">
            <h4 className="text-lg font-semibold mb-2">Findings</h4>
            {healthCheck.findings.length === 0 ? (
              <div className="bg-green-100 text-green-700 p-4 rounded">
                No security issues found. All systems are operating normally.
              </div>
            ) : (
              <div className="space-y-3">
                {healthCheck.findings.map((finding, index) => (
                  <div key={index} className={`p-4 rounded ${getSeverityClass(finding.severity)}`}>
                    <div className="flex justify-between">
                      <span className="font-semibold">{finding.message}</span>
                      <span className="text-sm uppercase">{finding.severity}</span>
                    </div>
                    <p className="text-sm mt-1">{finding.recommendation}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <div className="text-sm text-gray-500 mt-4">
            Last checked: {new Date(healthCheck.last_checked).toLocaleString()}
          </div>
        </div>
      </div>
    );
  };
  
  // Render security events tab
  const renderSecurityEventsTab = () => {
    return (
      <div className="p-4">
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-xl font-semibold mb-4">Security Events Log</h3>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Event Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Severity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    IP Address
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {securityEvents.map((event) => (
                  <tr key={event.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {event.event_type}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                        ${event.severity === 'critical' ? 'bg-red-100 text-red-800' : 
                          event.severity === 'error' ? 'bg-orange-100 text-orange-800' : 
                          event.severity === 'warning' ? 'bg-yellow-100 text-yellow-800' : 
                          'bg-green-100 text-green-800'}`}>
                        {event.severity}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {new Date(event.timestamp).toLocaleString()}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {event.ip_address || 'N/A'}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900 truncate max-w-xs">
                        {event.description}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                        ${event.is_resolved ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                        {event.is_resolved ? 'Resolved' : 'Unresolved'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      {!event.is_resolved && (
                        <button 
                          className="text-indigo-600 hover:text-indigo-900"
                          onClick={() => {
                            const notes = prompt('Enter resolution notes:');
                            if (notes !== null) {
                              // Call API to resolve event
                              // This would need implementation
                            }
                          }}
                        >
                          Resolve
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
                {securityEvents.length === 0 && (
                  <tr>
                    <td colSpan="7" className="px-6 py-4 text-center text-sm text-gray-500">
                      No security events found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };
  
  // Render blocked IPs tab
  const renderBlockedIPsTab = () => {
    return (
      <div className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 bg-white shadow rounded-lg p-6">
            <h3 className="text-xl font-semibold mb-4">Blocked IP Addresses</h3>
            
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      IP Address
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Reason
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Blocked At
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Duration
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {blockedIPs.map((ip) => (
                    <tr key={ip.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {ip.ip_address}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {ip.reason}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {new Date(ip.blocked_at).toLocaleString()}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {ip.is_permanent ? 'Permanent' : ip.blocked_until ? 
                            `Until ${new Date(ip.blocked_until).toLocaleString()}` : 
                            'Unknown'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                          ${ip.status === 'permanent' ? 'bg-red-100 text-red-800' : 
                            ip.status === 'active' ? 'bg-yellow-100 text-yellow-800' : 
                            'bg-green-100 text-green-800'}`}>
                          {ip.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button 
                          className="text-indigo-600 hover:text-indigo-900"
                          onClick={() => handleUnblockIP(ip.id)}
                        >
                          Unblock
                        </button>
                      </td>
                    </tr>
                  ))}
                  {blockedIPs.length === 0 && (
                    <tr>
                      <td colSpan="6" className="px-6 py-4 text-center text-sm text-gray-500">
                        No blocked IP addresses found
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
          
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-xl font-semibold mb-4">Block IP Address</h3>
            
            <form onSubmit={handleBlockIP}>
              <div className="mb-4">
                <label htmlFor="ipAddress" className="block text-sm font-medium text-gray-700">
                  IP Address*
                </label>
                <input
                  type="text"
                  id="ipAddress"
                  name="ipAddress"
                  required
                  value={ipBlockForm.ipAddress}
                  onChange={handleInputChange}
                  className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                  placeholder="e.g. 192.168.1.1"
                />
              </div>
              
              <div className="mb-4">
                <label htmlFor="reason" className="block text-sm font-medium text-gray-700">
                  Reason for Blocking
                </label>
                <select
                  id="reason"
                  name="reason"
                  value={ipBlockForm.reason}
                  onChange={handleInputChange}
                  className="mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                >
                  <option value="manual">Manual Block</option>
                  <option value="suspicious">Suspicious Activity</option>
                  <option value="attack">Attack Detected</option>
                  <option value="brute_force">Brute Force Attempt</option>
                  <option value="rate_limit">Rate Limit Exceeded</option>
                </select>
              </div>
              
              <div className="mb-4">
                <div className="flex items-center">
                  <input
                    id="isPermanent"
                    name="isPermanent"
                    type="checkbox"
                    checked={ipBlockForm.isPermanent}
                    onChange={handleInputChange}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <label htmlFor="isPermanent" className="ml-2 block text-sm text-gray-900">
                    Permanent Block
                  </label>
                </div>
              </div>
              
              {!ipBlockForm.isPermanent && (
                <div className="mb-4">
                  <label htmlFor="durationHours" className="block text-sm font-medium text-gray-700">
                    Block Duration (hours)
                  </label>
                  <input
                    type="number"
                    id="durationHours"
                    name="durationHours"
                    min="1"
                    value={ipBlockForm.durationHours}
                    onChange={handleInputChange}
                    className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                  />
                </div>
              )}
              
              <div className="mb-4">
                <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                  Description
                </label>
                <textarea
                  id="description"
                  name="description"
                  rows="3"
                  value={ipBlockForm.description}
                  onChange={handleInputChange}
                  className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                  placeholder="Optional notes about this block"
                />
              </div>
              
              <div>
                <button
                  type="submit"
                  className="w-full inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Block IP Address
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    );
  };
  
  // Render security incidents tab
  const renderIncidentsTab = () => {
    return (
      <div className="p-4">
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-xl font-semibold mb-4">Security Incidents</h3>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Severity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Detected At
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Reported By
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {incidents.map((incident) => (
                  <tr key={incident.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {incident.incident_type}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                        ${incident.severity === 'critical' ? 'bg-red-100 text-red-800' : 
                          incident.severity === 'high' ? 'bg-orange-100 text-orange-800' : 
                          incident.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' : 
                          'bg-green-100 text-green-800'}`}>
                        {incident.severity}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                        ${incident.status === 'detected' || incident.status === 'investigating' ? 'bg-red-100 text-red-800' : 
                          incident.status === 'contained' ? 'bg-yellow-100 text-yellow-800' : 
                          'bg-green-100 text-green-800'}`}>
                        {incident.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {new Date(incident.detected_at).toLocaleString()}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {incident.reported_by ? 
                          `${incident.reported_by.first_name} ${incident.reported_by.last_name}` : 
                          'System'}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900 truncate max-w-xs">
                        {incident.description}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      {incident.status !== 'resolved' && incident.status !== 'closed' && (
                        <div className="space-x-2">
                          {incident.status === 'detected' && (
                            <button 
                              className="text-yellow-600 hover:text-yellow-900"
                              onClick={() => handleUpdateIncidentStatus(incident.id, 'investigating')}
                            >
                              Investigate
                            </button>
                          )}
                          {incident.status === 'investigating' && (
                            <button 
                              className="text-blue-600 hover:text-blue-900"
                              onClick={() => handleUpdateIncidentStatus(incident.id, 'contained')}
                            >
                              Mark Contained
                            </button>
                          )}
                          {incident.status === 'contained' && (
                            <button 
                              className="text-green-600 hover:text-green-900"
                              onClick={() => {
                                const notes = prompt('Enter resolution details:');
                                if (notes) {
                                  handleUpdateIncidentStatus(incident.id, 'resolved', {
                                    response_actions: notes
                                  });
                                }
                              }}
                            >
                              Resolve
                            </button>
                          )}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
                {incidents.length === 0 && (
                  <tr>
                    <td colSpan="7" className="px-6 py-4 text-center text-sm text-gray-500">
                      No security incidents found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };
  
  // Render WAF alerts tab
  const renderWAFAlertsTab = () => {
    return (
      <div className="p-4">
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-xl font-semibold mb-4">Web Application Firewall Alerts</h3>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Attack Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Severity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    IP Address
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Request Path
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Action Taken
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    False Positive
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {wafAlerts.map((alert) => (
                  <tr key={alert.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {alert.attack_type}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                        ${alert.severity === 'critical' ? 'bg-red-100 text-red-800' : 
                          alert.severity === 'high' ? 'bg-orange-100 text-orange-800' : 
                          alert.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' : 
                          'bg-green-100 text-green-800'}`}>
                        {alert.severity}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {new Date(alert.timestamp).toLocaleString()}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {alert.ip_address || 'N/A'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {alert.request_method} {alert.request_path}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                        ${alert.action_taken === 'block' ? 'bg-red-100 text-red-800' : 
                          alert.action_taken === 'challenge' ? 'bg-yellow-100 text-yellow-800' : 
                          'bg-blue-100 text-blue-800'}`}>
                        {alert.action_taken}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                        ${alert.is_false_positive ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                        {alert.is_false_positive ? 'Yes' : 'No'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="space-x-2">
                        {!alert.is_false_positive && (
                          <button 
                            className="text-indigo-600 hover:text-indigo-900"
                            onClick={() => {
                              const notes = prompt('Enter notes for false positive:');
                              if (notes !== null) {
                                handleMarkFalsePositive(alert.id, notes);
                              }
                            }}
                          >
                            Mark as False Positive
                          </button>
                        )}
                        {alert.ip_address && (
                          <button 
                            className="text-red-600 hover:text-red-900"
                            onClick={() => {
                              setIpBlockForm({
                                ...ipBlockForm,
                                ipAddress: alert.ip_address,
                                reason: 'attack'
                              });
                              setActiveTab('blocked-ips');
                            }}
                          >
                            Block IP
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {wafAlerts.length === 0 && (
                  <tr>
                    <td colSpan="8" className="px-6 py-4 text-center text-sm text-gray-500">
                      No WAF alerts found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };
  
  return (
    <div className="bg-gray-100 min-h-screen">
      <div className="py-6 px-4 sm:px-6 lg:px-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Security Audit Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500">
            Monitor and manage security events, incidents, and configuration
          </p>
        </div>
        
        {/* Tab Navigation */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            <button
              className={`${
                activeTab === 'overview'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
              onClick={() => setActiveTab('overview')}
            >
              Overview
            </button>
            <button
              className={`${
                activeTab === 'health'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
              onClick={() => setActiveTab('health')}
            >
              Health Check
            </button>
            <button
              className={`${
                activeTab === 'events'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
              onClick={() => setActiveTab('events')}
            >
              Security Events
            </button>
            <button
              className={`${
                activeTab === 'blocked-ips'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
              onClick={() => setActiveTab('blocked-ips')}
            >
              Blocked IPs
            </button>
            <button
              className={`${
                activeTab === 'incidents'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
              onClick={() => setActiveTab('incidents')}
            >
              Incidents
            </button>
            <button
              className={`${
                activeTab === 'waf'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
              onClick={() => setActiveTab('waf')}
            >
              WAF Alerts
            </button>
          </nav>
        </div>
        
        {/* Tab Content */}
        {renderTabContent()}
      </div>
    </div>
  );
};

export default SecurityAuditDashboard;