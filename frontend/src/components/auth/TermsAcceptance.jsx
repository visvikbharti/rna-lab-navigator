import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const TermsAcceptance = () => {
  const navigate = useNavigate();
  const { acceptTerms, logout } = useAuth();
  const [loading, setLoading] = useState(false);
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [acceptedDataAgreement, setAcceptedDataAgreement] = useState(false);
  const [error, setError] = useState(null);

  const handleAccept = async () => {
    if (!acceptedTerms || !acceptedDataAgreement) {
      setError('You must accept both the Terms of Use and Data Access Agreement to continue.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await acceptTerms();
      if (result.success) {
        navigate('/');
      } else {
        setError(result.error || 'Failed to accept terms. Please try again.');
      }
    } catch (err) {
      setError('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDecline = () => {
    logout();
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
          {/* Header */}
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Terms and Agreements
            </h1>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              Please review and accept the following terms to continue using RNA Lab Navigator
            </p>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {error && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}

            {/* Terms of Use */}
            <div>
              <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
                Terms of Use
              </h2>
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 max-h-60 overflow-y-auto text-sm text-gray-700 dark:text-gray-300 space-y-2">
                <p>
                  <strong>1. Acceptance of Terms</strong><br />
                  By accessing and using the RNA Lab Navigator system, you agree to be bound by these Terms of Use.
                </p>
                <p>
                  <strong>2. Authorized Use</strong><br />
                  This system is for authorized CSIR-IGIB personnel only. You must have valid credentials and authorization from the RNA Biology Lab to access this system.
                </p>
                <p>
                  <strong>3. Confidentiality</strong><br />
                  All data, protocols, and research information accessed through this system are confidential and proprietary. You agree not to share, distribute, or disclose any information without proper authorization.
                </p>
                <p>
                  <strong>4. Data Integrity</strong><br />
                  You agree to maintain the integrity of all data and not to modify, delete, or corrupt any information unless authorized to do so as part of your role.
                </p>
                <p>
                  <strong>5. Compliance</strong><br />
                  You agree to comply with all applicable laws, regulations, and institutional policies, including GMP guidelines and data protection regulations.
                </p>
                <p>
                  <strong>6. Security</strong><br />
                  You are responsible for maintaining the security of your credentials and for all activities that occur under your account.
                </p>
              </div>
              <div className="mt-3">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    checked={acceptedTerms}
                    onChange={(e) => setAcceptedTerms(e.target.checked)}
                  />
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                    I have read and accept the Terms of Use
                  </span>
                </label>
              </div>
            </div>

            {/* Data Access Agreement */}
            <div>
              <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
                Data Access Agreement
              </h2>
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 max-h-60 overflow-y-auto text-sm text-gray-700 dark:text-gray-300 space-y-2">
                <p>
                  <strong>1. Data Classification</strong><br />
                  All research data, protocols, and documents in this system are classified as confidential institutional property.
                </p>
                <p>
                  <strong>2. Permitted Use</strong><br />
                  Data accessed through this system may only be used for legitimate research purposes within the scope of your assigned projects and responsibilities.
                </p>
                <p>
                  <strong>3. Data Sharing</strong><br />
                  Sharing of data is restricted to authorized personnel within the RNA Biology Lab. External sharing requires explicit written approval from the Principal Investigator.
                </p>
                <p>
                  <strong>4. Data Protection</strong><br />
                  You agree to implement appropriate technical and organizational measures to protect data from unauthorized access, disclosure, alteration, or destruction.
                </p>
                <p>
                  <strong>5. Audit Trail</strong><br />
                  All data access and modifications are logged for compliance and security purposes. You consent to this monitoring as a condition of system access.
                </p>
                <p>
                  <strong>6. Breach Notification</strong><br />
                  You agree to immediately report any suspected or actual data breach, unauthorized access, or security incident to the system administrator.
                </p>
              </div>
              <div className="mt-3">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    checked={acceptedDataAgreement}
                    onChange={(e) => setAcceptedDataAgreement(e.target.checked)}
                  />
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                    I have read and accept the Data Access Agreement
                  </span>
                </label>
              </div>
            </div>

            {/* Actions */}
            <div className="flex justify-end space-x-4 pt-4">
              <button
                onClick={handleDecline}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Decline and Logout
              </button>
              <button
                onClick={handleAccept}
                disabled={loading || !acceptedTerms || !acceptedDataAgreement}
                className="px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Processing...' : 'Accept and Continue'}
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 text-center text-sm text-gray-600 dark:text-gray-400">
          <p>
            By continuing, you acknowledge that you have read, understood, and agree to be bound by these terms.
          </p>
          <p className="mt-2">
            Last updated: June 27, 2025 | Version 1.0
          </p>
        </div>
      </div>
    </div>
  );
};

export default TermsAcceptance;