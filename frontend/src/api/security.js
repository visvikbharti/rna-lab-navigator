/**
 * Security API service.
 * Provides functions for accessing security audit and monitoring data.
 */

import { API_BASE_URL } from './config';

/**
 * Get security dashboard summary data
 * @returns {Promise} Dashboard summary data
 */
export const getSecurityDashboardSummary = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/security/dashboard/summary/`, {
      credentials: 'include',
    });
    
    if (!response.ok) {
      throw new Error(`Error ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch security dashboard summary:', error);
    throw error;
  }
};

/**
 * Get security health check
 * @returns {Promise} Security health check data
 */
export const getSecurityHealthCheck = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/security/health-check/`, {
      credentials: 'include',
    });
    
    if (!response.ok) {
      throw new Error(`Error ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch security health check:', error);
    throw error;
  }
};

/**
 * Get security events with optional filters
 * @param {Object} filters - Optional filters (eventType, severity, isResolved, etc.)
 * @returns {Promise} Security events
 */
export const getSecurityEvents = async (filters = {}) => {
  try {
    // Build query parameters
    const queryParams = new URLSearchParams();
    
    if (filters.eventType) queryParams.append('event_type', filters.eventType);
    if (filters.severity) queryParams.append('severity', filters.severity);
    if (filters.isResolved !== undefined) queryParams.append('is_resolved', filters.isResolved);
    if (filters.startDate) queryParams.append('start_date', filters.startDate);
    if (filters.endDate) queryParams.append('end_date', filters.endDate);
    if (filters.limit) queryParams.append('limit', filters.limit);
    
    const url = `${API_BASE_URL}/security/events/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    
    const response = await fetch(url, {
      credentials: 'include',
    });
    
    if (!response.ok) {
      throw new Error(`Error ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch security events:', error);
    throw error;
  }
};

/**
 * Get security event trends
 * @param {number} days - Number of days to include in trends data
 * @returns {Promise} Security event trends
 */
export const getSecurityEventTrends = async (days = 30) => {
  try {
    const response = await fetch(`${API_BASE_URL}/security/events/trends/?days=${days}`, {
      credentials: 'include',
    });
    
    if (!response.ok) {
      throw new Error(`Error ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch security event trends:', error);
    throw error;
  }
};

/**
 * Get list of blocked IPs
 * @returns {Promise} Blocked IPs
 */
export const getBlockedIPs = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/security/blocked-ips/`, {
      credentials: 'include',
    });
    
    if (!response.ok) {
      throw new Error(`Error ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch blocked IPs:', error);
    throw error;
  }
};

/**
 * Block an IP address
 * @param {Object} data - Block data (ipAddress, reason, isPermanent, etc.)
 * @returns {Promise} Block result
 */
export const blockIP = async (data) => {
  try {
    const response = await fetch(`${API_BASE_URL}/security/blocked-ips/block/`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ip_address: data.ipAddress,
        reason: data.reason || 'manual',
        is_permanent: data.isPermanent || false,
        duration_hours: data.durationHours || 24,
        description: data.description || '',
      }),
    });
    
    if (!response.ok) {
      throw new Error(`Error ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to block IP:', error);
    throw error;
  }
};

/**
 * Unblock an IP address
 * @param {string} id - Blocked IP record ID
 * @returns {Promise} Unblock result
 */
export const unblockIP = async (id) => {
  try {
    const response = await fetch(`${API_BASE_URL}/security/blocked-ips/${id}/unblock/`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`Error ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to unblock IP:', error);
    throw error;
  }
};

/**
 * Get security incidents
 * @returns {Promise} Security incidents
 */
export const getSecurityIncidents = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/security/incidents/`, {
      credentials: 'include',
    });
    
    if (!response.ok) {
      throw new Error(`Error ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch security incidents:', error);
    throw error;
  }
};

/**
 * Update security incident status
 * @param {string} id - Incident ID
 * @param {Object} data - Update data (status, responseActions, etc.)
 * @returns {Promise} Update result
 */
export const updateIncidentStatus = async (id, data) => {
  try {
    const response = await fetch(`${API_BASE_URL}/security/incidents/${id}/update_status/`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`Error ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to update incident status:', error);
    throw error;
  }
};

/**
 * Get WAF alerts
 * @param {Object} filters - Optional filters
 * @returns {Promise} WAF alerts
 */
export const getWAFAlerts = async (filters = {}) => {
  try {
    // Build query parameters
    const queryParams = new URLSearchParams();
    
    if (filters.attackType) queryParams.append('attack_type', filters.attackType);
    if (filters.severity) queryParams.append('severity', filters.severity);
    if (filters.actionTaken) queryParams.append('action_taken', filters.actionTaken);
    if (filters.falsePositive !== undefined) queryParams.append('false_positive', filters.falsePositive);
    if (filters.ipAddress) queryParams.append('ip_address', filters.ipAddress);
    if (filters.startDate) queryParams.append('start_date', filters.startDate);
    if (filters.endDate) queryParams.append('end_date', filters.endDate);
    
    const url = `${API_BASE_URL}/security/waf-alerts/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    
    const response = await fetch(url, {
      credentials: 'include',
    });
    
    if (!response.ok) {
      throw new Error(`Error ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch WAF alerts:', error);
    throw error;
  }
};

/**
 * Mark WAF alert as false positive
 * @param {string} id - Alert ID
 * @param {string} notes - Notes about why this is a false positive
 * @returns {Promise} Update result
 */
export const markWAFAlertAsFalsePositive = async (id, notes = '') => {
  try {
    const response = await fetch(`${API_BASE_URL}/security/waf-alerts/${id}/mark_false_positive/`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ notes }),
    });
    
    if (!response.ok) {
      throw new Error(`Error ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to mark WAF alert as false positive:', error);
    throw error;
  }
};