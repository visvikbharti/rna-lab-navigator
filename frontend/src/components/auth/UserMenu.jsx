import React, { Fragment } from 'react';
import { Menu, Transition } from '@headlessui/react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import {
  UserCircleIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline';

const UserMenu = () => {
  const { user, logout } = useAuth();

  const getRoleBadgeColor = (role) => {
    const colors = {
      ADMIN: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
      PI: 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400',
      SENIOR_RESEARCHER: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
      RESEARCHER: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
      GUEST: 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400'
    };
    return colors[role] || colors.GUEST;
  };

  return (
    <Menu as="div" className="relative">
      <Menu.Button className="flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
        <div className="text-right hidden sm:block">
          <p className="text-sm font-medium text-gray-900 dark:text-white">
            {user?.first_name} {user?.last_name}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {user?.employee_id}
          </p>
        </div>
        <div className="w-10 h-10 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center">
          <span className="text-white font-medium">
            {user?.first_name?.[0]}{user?.last_name?.[0]}
          </span>
        </div>
      </Menu.Button>

      <Transition
        as={Fragment}
        enter="transition ease-out duration-100"
        enterFrom="transform opacity-0 scale-95"
        enterTo="transform opacity-100 scale-100"
        leave="transition ease-in duration-75"
        leaveFrom="transform opacity-100 scale-100"
        leaveTo="transform opacity-0 scale-95"
      >
        <Menu.Items className="absolute right-0 mt-2 w-64 origin-top-right divide-y divide-gray-100 dark:divide-gray-700 rounded-md bg-white dark:bg-gray-800 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
          {/* User Info */}
          <div className="px-4 py-3">
            <p className="text-sm font-medium text-gray-900 dark:text-white">
              {user?.first_name} {user?.last_name}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {user?.email}
            </p>
            <div className="mt-2">
              <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getRoleBadgeColor(user?.role)}`}>
                {user?.role}
              </span>
            </div>
          </div>

          {/* Menu Items */}
          <div className="py-1">
            <Menu.Item>
              {({ active }) => (
                <Link
                  to="/profile"
                  className={`${
                    active ? 'bg-gray-100 dark:bg-gray-700' : ''
                  } group flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-300`}
                >
                  <UserCircleIcon className="mr-3 h-5 w-5 text-gray-400" />
                  My Profile
                </Link>
              )}
            </Menu.Item>

            {(user?.role === 'ADMIN' || user?.role === 'PI') && (
              <Menu.Item>
                {({ active }) => (
                  <Link
                    to="/admin"
                    className={`${
                      active ? 'bg-gray-100 dark:bg-gray-700' : ''
                    } group flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-300`}
                  >
                    <ShieldCheckIcon className="mr-3 h-5 w-5 text-gray-400" />
                    Admin Panel
                  </Link>
                )}
              </Menu.Item>
            )}

            <Menu.Item>
              {({ active }) => (
                <Link
                  to="/settings"
                  className={`${
                    active ? 'bg-gray-100 dark:bg-gray-700' : ''
                  } group flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-300`}
                >
                  <Cog6ToothIcon className="mr-3 h-5 w-5 text-gray-400" />
                  Settings
                </Link>
              )}
            </Menu.Item>
          </div>

          {/* Logout */}
          <div className="py-1">
            <Menu.Item>
              {({ active }) => (
                <button
                  onClick={logout}
                  className={`${
                    active ? 'bg-gray-100 dark:bg-gray-700' : ''
                  } group flex w-full items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-300`}
                >
                  <ArrowRightOnRectangleIcon className="mr-3 h-5 w-5 text-gray-400" />
                  Sign out
                </button>
              )}
            </Menu.Item>
          </div>

          {/* Statistics */}
          <div className="px-4 py-3 text-xs text-gray-500 dark:text-gray-400">
            <div className="flex justify-between">
              <span>Total Queries:</span>
              <span className="font-medium">{user?.total_queries || 0}</span>
            </div>
            <div className="flex justify-between mt-1">
              <span>Documents Uploaded:</span>
              <span className="font-medium">{user?.total_documents_uploaded || 0}</span>
            </div>
            <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
              <span>Last Activity: {new Date(user?.last_activity || Date.now()).toLocaleString()}</span>
            </div>
          </div>
        </Menu.Items>
      </Transition>
    </Menu>
  );
};

export default UserMenu;