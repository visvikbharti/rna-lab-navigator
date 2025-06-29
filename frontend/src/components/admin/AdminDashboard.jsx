import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  UsersIcon,
  ShieldCheckIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  LockClosedIcon,
  CalendarIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import axios from 'axios';
import toast from 'react-hot-toast';

const AdminDashboard = () => {
  const [statistics, setStatistics] = useState(null);
  const [recentActivity, setRecentActivity] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch statistics
      const statsResponse = await axios.get('/api/auth/users/statistics/');
      setStatistics(statsResponse.data);

      // Fetch recent audit logs
      const auditResponse = await axios.get('/api/auth/audit-logs/summary/');
      setRecentActivity(auditResponse.data.activity_summary || []);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ title, value, icon: Icon, color, subtext }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 dark:text-gray-400">{title}</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
            {value}
          </p>
          {subtext && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {subtext}
            </p>
          )}
        </div>
        <div className={`w-12 h-12 rounded-lg ${color} flex items-center justify-center`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </motion.div>
  );

  const ActivityItem = ({ action, count }) => {
    const getActionDetails = (action) => {
      const actionMap = {
        'LOGIN_SUCCESS': { label: 'Successful Logins', icon: CheckCircleIcon, color: 'text-green-600' },
        'LOGIN_FAILED': { label: 'Failed Logins', icon: ExclamationTriangleIcon, color: 'text-red-600' },
        'USER_CREATED': { label: 'Users Created', icon: UsersIcon, color: 'text-blue-600' },
        'USER_UPDATED': { label: 'Users Updated', icon: UsersIcon, color: 'text-yellow-600' },
        'PASSWORD_CHANGED': { label: 'Password Changes', icon: LockClosedIcon, color: 'text-purple-600' },
        'ACCOUNT_LOCKED': { label: 'Accounts Locked', icon: LockClosedIcon, color: 'text-red-600' },
        'ACCOUNT_UNLOCKED': { label: 'Accounts Unlocked', icon: LockClosedIcon, color: 'text-green-600' },
      };
      return actionMap[action] || { label: action, icon: ClockIcon, color: 'text-gray-600' };
    };

    const details = getActionDetails(action);
    const Icon = details.icon;

    return (
      <div className="flex items-center justify-between py-3 border-b border-gray-200 dark:border-gray-700 last:border-0">
        <div className="flex items-center gap-3">
          <Icon className={`w-5 h-5 ${details.color}`} />
          <span className="text-sm text-gray-700 dark:text-gray-300">{details.label}</span>
        </div>
        <span className="text-sm font-medium text-gray-900 dark:text-white">{count}</span>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Admin Dashboard</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Overview of system usage and security metrics
        </p>
      </div>

      {/* Statistics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Users"
          value={statistics?.total_users || 0}
          icon={UsersIcon}
          color="bg-blue-600"
          subtext={`${statistics?.new_users_this_week || 0} new this week`}
        />
        <StatCard
          title="Active Users"
          value={statistics?.active_users || 0}
          icon={CheckCircleIcon}
          color="bg-green-600"
          subtext={`${statistics?.recent_logins || 0} logins today`}
        />
        <StatCard
          title="Locked Accounts"
          value={statistics?.locked_users || 0}
          icon={LockClosedIcon}
          color="bg-red-600"
          subtext="Requires attention"
        />
        <StatCard
          title="Failed Logins (24h)"
          value={statistics?.failed_attempts_24h || 0}
          icon={ExclamationTriangleIcon}
          color="bg-yellow-600"
          subtext="Security monitoring"
        />
      </div>

      {/* Users by Role */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Users by Role
          </h3>
          <div className="space-y-3">
            {statistics?.users_by_role?.map((role) => (
              <div key={role.role} className="flex items-center justify-between">
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  {role.role}
                </span>
                <div className="flex items-center gap-2">
                  <div className="w-32 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{
                        width: `${(role.count / statistics.total_users) * 100}%`
                      }}
                    />
                  </div>
                  <span className="text-sm font-medium text-gray-900 dark:text-white w-8 text-right">
                    {role.count}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Recent Activity */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Activity Summary (Last 7 Days)
          </h3>
          <div className="space-y-1">
            {recentActivity.length > 0 ? (
              recentActivity.map((activity) => (
                <ActivityItem
                  key={activity.action}
                  action={activity.action}
                  count={activity.count}
                />
              ))
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                No recent activity
              </p>
            )}
          </div>
        </motion.div>
      </div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-6 border border-blue-200 dark:border-blue-800"
      >
        <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-4">
          Quick Actions
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => window.location.href = '/admin/users'}
            className="flex items-center gap-3 p-4 bg-white dark:bg-gray-800 rounded-lg hover:shadow-md transition-shadow"
          >
            <UsersIcon className="w-6 h-6 text-blue-600" />
            <div className="text-left">
              <p className="font-medium text-gray-900 dark:text-white">Manage Users</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Add, edit, or remove users</p>
            </div>
          </button>
          
          <button
            onClick={() => window.location.href = '/admin/audit-logs'}
            className="flex items-center gap-3 p-4 bg-white dark:bg-gray-800 rounded-lg hover:shadow-md transition-shadow"
          >
            <ShieldCheckIcon className="w-6 h-6 text-green-600" />
            <div className="text-left">
              <p className="font-medium text-gray-900 dark:text-white">Audit Logs</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">View system activity</p>
            </div>
          </button>
          
          <button
            onClick={() => window.location.href = '/admin/settings'}
            className="flex items-center gap-3 p-4 bg-white dark:bg-gray-800 rounded-lg hover:shadow-md transition-shadow"
          >
            <ChartBarIcon className="w-6 h-6 text-purple-600" />
            <div className="text-left">
              <p className="font-medium text-gray-900 dark:text-white">System Settings</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Configure system parameters</p>
            </div>
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default AdminDashboard;