import React, { createContext, useContext, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  CheckCircleIcon, 
  ExclamationCircleIcon, 
  InformationCircleIcon, 
  XCircleIcon,
  XMarkIcon 
} from '@heroicons/react/24/solid';

// Notification Context
const NotificationContext = createContext();

// Notification types and their configurations
const notificationTypes = {
  success: {
    icon: CheckCircleIcon,
    bgColor: 'bg-green-50 dark:bg-green-900/20',
    borderColor: 'border-green-200 dark:border-green-800',
    iconColor: 'text-green-600 dark:text-green-400',
    titleColor: 'text-green-800 dark:text-green-200',
    messageColor: 'text-green-700 dark:text-green-300'
  },
  error: {
    icon: XCircleIcon,
    bgColor: 'bg-red-50 dark:bg-red-900/20',
    borderColor: 'border-red-200 dark:border-red-800',
    iconColor: 'text-red-600 dark:text-red-400',
    titleColor: 'text-red-800 dark:text-red-200',
    messageColor: 'text-red-700 dark:text-red-300'
  },
  warning: {
    icon: ExclamationCircleIcon,
    bgColor: 'bg-yellow-50 dark:bg-yellow-900/20',
    borderColor: 'border-yellow-200 dark:border-yellow-800',
    iconColor: 'text-yellow-600 dark:text-yellow-400',
    titleColor: 'text-yellow-800 dark:text-yellow-200',
    messageColor: 'text-yellow-700 dark:text-yellow-300'
  },
  info: {
    icon: InformationCircleIcon,
    bgColor: 'bg-blue-50 dark:bg-blue-900/20',
    borderColor: 'border-blue-200 dark:border-blue-800',
    iconColor: 'text-blue-600 dark:text-blue-400',
    titleColor: 'text-blue-800 dark:text-blue-200',
    messageColor: 'text-blue-700 dark:text-blue-300'
  }
};

// Individual Notification Component
const Notification = ({ id, type, title, message, actions, onDismiss, duration = 5000 }) => {
  const config = notificationTypes[type] || notificationTypes.info;
  const Icon = config.icon;

  // Auto-dismiss after duration
  React.useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        onDismiss(id);
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [id, duration, onDismiss]);

  return (
    <motion.div
      initial={{ opacity: 0, y: -20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, x: 100, scale: 0.95 }}
      transition={{ duration: 0.2 }}
      className={`
        relative overflow-hidden rounded-lg shadow-lg p-4 mb-3 border
        ${config.bgColor} ${config.borderColor}
        backdrop-blur-sm min-w-[320px] max-w-md
      `}
    >
      {/* Progress bar for auto-dismiss */}
      {duration > 0 && (
        <motion.div
          initial={{ scaleX: 1 }}
          animate={{ scaleX: 0 }}
          transition={{ duration: duration / 1000, ease: 'linear' }}
          className="absolute bottom-0 left-0 h-1 bg-current opacity-30 origin-left"
          style={{ width: '100%' }}
        />
      )}

      <div className="flex items-start">
        <div className="flex-shrink-0">
          <Icon className={`h-6 w-6 ${config.iconColor}`} />
        </div>
        
        <div className="ml-3 flex-1">
          {title && (
            <h3 className={`text-sm font-medium ${config.titleColor}`}>
              {title}
            </h3>
          )}
          {message && (
            <p className={`mt-1 text-sm ${config.messageColor}`}>
              {message}
            </p>
          )}
          
          {actions && actions.length > 0 && (
            <div className="mt-3 flex gap-2">
              {actions.map((action, index) => (
                <button
                  key={index}
                  onClick={() => {
                    if (action.action) {
                      if (typeof action.action === 'function') {
                        action.action();
                      } else if (typeof action.action === 'string') {
                        window.location.href = action.action;
                      }
                    }
                    onDismiss(id);
                  }}
                  className={`
                    text-sm font-medium px-3 py-1 rounded
                    ${config.titleColor} hover:opacity-80
                    transition-opacity
                  `}
                >
                  {action.label}
                </button>
              ))}
            </div>
          )}
        </div>
        
        <button
          onClick={() => onDismiss(id)}
          className={`
            ml-4 flex-shrink-0 rounded-md 
            ${config.iconColor} hover:opacity-70
            focus:outline-none transition-opacity
          `}
        >
          <XMarkIcon className="h-5 w-5" />
        </button>
      </div>
    </motion.div>
  );
};

// Notification Container Component
const NotificationContainer = ({ notifications, onDismiss }) => {
  return (
    <div className="fixed top-4 right-4 z-50">
      <AnimatePresence mode="sync">
        {notifications.map(notification => (
          <Notification
            key={notification.id}
            {...notification}
            onDismiss={onDismiss}
          />
        ))}
      </AnimatePresence>
    </div>
  );
};

// Notification Provider Component
export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([]);

  const showNotification = useCallback((notification) => {
    const id = Date.now() + Math.random();
    const newNotification = {
      id,
      type: 'info',
      duration: 5000,
      ...notification
    };
    
    setNotifications(prev => [...prev, newNotification]);
    return id;
  }, []);

  const dismissNotification = useCallback((id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  const dismissAll = useCallback(() => {
    setNotifications([]);
  }, []);

  // Make showNotification available globally
  React.useEffect(() => {
    window.showNotification = showNotification;
    return () => {
      delete window.showNotification;
    };
  }, [showNotification]);

  const value = {
    showNotification,
    dismissNotification,
    dismissAll,
    notifications
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
      <NotificationContainer 
        notifications={notifications}
        onDismiss={dismissNotification}
      />
    </NotificationContext.Provider>
  );
};

// Hook to use notifications
export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within NotificationProvider');
  }
  return context;
};

// Convenience methods
export const notify = {
  success: (message, options = {}) => {
    if (window.showNotification) {
      return window.showNotification({
        type: 'success',
        message,
        ...options
      });
    }
  },
  error: (message, options = {}) => {
    if (window.showNotification) {
      return window.showNotification({
        type: 'error',
        message,
        ...options
      });
    }
  },
  warning: (message, options = {}) => {
    if (window.showNotification) {
      return window.showNotification({
        type: 'warning',
        message,
        ...options
      });
    }
  },
  info: (message, options = {}) => {
    if (window.showNotification) {
      return window.showNotification({
        type: 'info',
        message,
        ...options
      });
    }
  }
};