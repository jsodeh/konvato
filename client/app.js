/**
 * Main React application for Betslip Converter
 * 
 * This component provides the main application structure with:
 * - State management for form inputs and conversion results
 * - Loading and error state handling
 * - Responsive layout using Tailwind CSS
 */

const { useState, useEffect } = React;

// ResultsDisplay Component
function ResultsDisplay({ result, onNewConversion }) {
  const [copiedCode, setCopiedCode] = useState(false);

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 2000);
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      converted: 'bg-green-100 text-green-800',
      partial: 'bg-yellow-100 text-yellow-800',
      unavailable: 'bg-red-100 text-red-800'
    };
    
    const labels = {
      converted: 'Converted',
      partial: 'Partial',
      unavailable: 'Unavailable'
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${badges[status] || badges.unavailable}`}>
        {labels[status] || 'Unknown'}
      </span>
    );
  };

  const getOddsComparison = (originalOdds, newOdds) => {
    const diff = newOdds - originalOdds;
    const percentage = ((diff / originalOdds) * 100).toFixed(1);
    
    if (Math.abs(diff) < 0.01) {
      return <span className="text-gray-600">Same</span>;
    }
    
    if (diff > 0) {
      return <span className="text-green-600">+{diff.toFixed(2)} (+{percentage}%)</span>;
    } else {
      return <span className="text-red-600">{diff.toFixed(2)} ({percentage}%)</span>;
    }
  };

  return (
    <div className="mt-8 space-y-6">
      {/* Success Header */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
        <div className="flex items-start">
          <svg className="h-6 w-6 text-green-400 mt-0.5 mr-3" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          <div className="flex-1">
            <h3 className="text-lg font-medium text-green-800">Conversion Successful!</h3>
            <p className="text-sm text-green-700 mt-1">
              Your betslip has been converted in {result.processingTime?.toFixed(1) || 'N/A'} seconds.
            </p>
            
            {/* New Betslip Code */}
            {result.betslipCode && (
              <div className="mt-4 p-4 bg-white border border-green-200 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900">New Betslip Code:</p>
                    <p className="text-lg font-mono text-blue-600 mt-1">{result.betslipCode}</p>
                  </div>
                  <button
                    onClick={() => copyToClipboard(result.betslipCode)}
                    className="ml-4 px-3 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
                  >
                    {copiedCode ? (
                      <span className="flex items-center">
                        <svg className="h-4 w-4 mr-1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                        Copied!
                      </span>
                    ) : (
                      <span className="flex items-center">
                        <svg className="h-4 w-4 mr-1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                          <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z" />
                          <path d="M6 3a2 2 0 00-2 2v11a2 2 0 002 2h8a2 2 0 002-2V5a2 2 0 00-2-2 3 3 0 01-3 3H9a3 3 0 01-3-3z" />
                        </svg>
                        Copy
                      </span>
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Warnings */}
      {result.warnings && result.warnings.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start">
            <svg className="h-5 w-5 text-yellow-400 mt-0.5 mr-3" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <div className="flex-1">
              <h4 className="text-sm font-medium text-yellow-800">Conversion Warnings</h4>
              <ul className="mt-2 text-sm text-yellow-700 space-y-1">
                {result.warnings.map((warning, index) => (
                  <li key={index}>• {warning}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Selections Comparison Table */}
      {result.selections && result.selections.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <h4 className="text-lg font-medium text-gray-900">Conversion Details</h4>
            <p className="text-sm text-gray-600 mt-1">
              {result.selections.length} selection{result.selections.length !== 1 ? 's' : ''} processed
            </p>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Game
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Market
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Original Odds
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    New Odds
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Difference
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {result.selections.map((selection, index) => (
                  <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {selection.game}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {selection.market}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {selection.originalOdds?.toFixed(2) || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {selection.status === 'converted' ? selection.odds?.toFixed(2) || 'N/A' : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {selection.status === 'converted' && selection.odds && selection.originalOdds
                        ? getOddsComparison(selection.originalOdds, selection.odds)
                        : '-'
                      }
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(selection.status)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex justify-center space-x-4">
        <button
          onClick={onNewConversion}
          className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
        >
          Convert Another Betslip
        </button>
        
        {result.betslipCode && (
          <button
            onClick={() => copyToClipboard(result.betslipCode)}
            className="px-6 py-3 bg-gray-600 text-white font-medium rounded-lg hover:bg-gray-700 focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
          >
            {copiedCode ? 'Copied!' : 'Copy Betslip Code'}
          </button>
        )}
      </div>
    </div>
  );
}

// BookmakerSelector Component
function BookmakerSelector({ value, onChange, bookmakers, label, disabled, error, excludeValue }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        {label}
      </label>
      <select
        value={value}
        onChange={onChange}
        className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
          error ? 'border-red-300 focus:ring-red-500 focus:border-red-500' : 'border-gray-300'
        }`}
        disabled={disabled}
        required
      >
        <option value="">{`Select ${label.toLowerCase()}`}</option>
        {bookmakers
          .filter(b => b.supported && b.id !== excludeValue)
          .map(bookmaker => (
            <option key={bookmaker.id} value={bookmaker.id}>
              {bookmaker.name}
            </option>
          ))}
      </select>
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
}

// BetslipCodeInput Component
function BetslipCodeInput({ value, onChange, disabled, error }) {
  return (
    <div>
      <label htmlFor="betslipCode" className="block text-sm font-medium text-gray-700 mb-2">
        Betslip Code
      </label>
      <input
        type="text"
        id="betslipCode"
        value={value}
        onChange={onChange}
        placeholder="Enter your betslip code (e.g., ABC123XYZ)"
        className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
          error ? 'border-red-300 focus:ring-red-500 focus:border-red-500' : 'border-gray-300'
        }`}
        disabled={disabled}
        required
        minLength="6"
        maxLength="20"
        pattern="[A-Za-z0-9_-]+"
      />
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
      <p className="mt-1 text-xs text-gray-500">
        6-20 characters, letters, numbers, hyphens and underscores only
      </p>
    </div>
  );
}

// Main App Component
function App() {
  // Form input state
  const [betslipCode, setBetslipCode] = useState('');
  const [sourceBookmaker, setSourceBookmaker] = useState('');
  const [destinationBookmaker, setDestinationBookmaker] = useState('');
  
  // Application state
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Bookmaker data state
  const [bookmakers, setBookmakers] = useState([]);
  const [bookmarkersLoading, setBookmarkersLoading] = useState(false);
  
  // Form validation state
  const [validationErrors, setValidationErrors] = useState({});
  
  // Compliance state
  const [disclaimers, setDisclaimers] = useState(null);
  const [showPrivacyPolicy, setShowPrivacyPolicy] = useState(false);
  const [hasAcceptedTerms, setHasAcceptedTerms] = useState(false);

  // Load bookmakers and compliance data on component mount
  useEffect(() => {
    loadBookmakers();
    loadComplianceDisclaimers();
  }, []);

  /**
   * Load available bookmakers from API
   */
  const loadBookmakers = async () => {
    setBookmarkersLoading(true);
    try {
      const response = await axios.get('/api/bookmakers');
      if (response.data && Array.isArray(response.data.bookmakers)) {
        setBookmakers(response.data.bookmakers);
      } else {
        // Fallback to default bookmakers if API fails
        setBookmakers([
          { id: 'bet9ja', name: 'Bet9ja', baseUrl: 'https://bet9ja.com', supported: true },
          { id: 'sportybet', name: 'SportyBet', baseUrl: 'https://sportybet.com', supported: true },
          { id: 'betway', name: 'Betway', baseUrl: 'https://betway.com', supported: true },
          { id: 'bet365', name: 'Bet365', baseUrl: 'https://bet365.com', supported: true }
        ]);
      }
    } catch (err) {
      console.error('Failed to load bookmakers:', err);
      // Use fallback bookmakers
      setBookmakers([
        { id: 'bet9ja', name: 'Bet9ja', baseUrl: 'https://bet9ja.com', supported: true },
        { id: 'sportybet', name: 'SportyBet', baseUrl: 'https://sportybet.com', supported: true },
        { id: 'betway', name: 'Betway', baseUrl: 'https://betway.com', supported: true },
        { id: 'bet365', name: 'Bet365', baseUrl: 'https://bet365.com', supported: true }
      ]);
    } finally {
      setBookmarkersLoading(false);
    }
  };

  /**
   * Load compliance disclaimers from API
   */
  const loadComplianceDisclaimers = async () => {
    try {
      const response = await axios.get('/api/compliance/disclaimers');
      if (response.data && response.data.disclaimers) {
        setDisclaimers(response.data.disclaimers);
      }
    } catch (err) {
      console.error('Failed to load compliance disclaimers:', err);
      // Set fallback disclaimers
      setDisclaimers({
        accuracy: "This service provides automated betslip conversion for convenience only. Users are responsible for verifying all selections, odds, and terms before placing bets.",
        responsibility: "Users must ensure compliance with local gambling laws and bookmaker terms of service. This service does not encourage or facilitate illegal gambling.",
        privacy: "We do not store betslip codes or personal betting information. All data is processed temporarily and discarded after conversion.",
        terms: "By using this service, you acknowledge that you are of legal gambling age and accept full responsibility for your betting activities."
      });
    }
  };

  /**
   * Validate form field in real-time
   */
  const validateFormField = (fieldName, value, allValues = {}) => {
    const error = window.BetslipValidation.validateField(fieldName, value, allValues);
    setValidationErrors(prev => ({
      ...prev,
      [fieldName]: error
    }));
    return error;
  };

  /**
   * Handle form submission for betslip conversion
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Check if user has accepted terms
    if (!hasAcceptedTerms) {
      setError('Please accept the terms and conditions before proceeding.');
      return;
    }
    
    // Clear previous results and errors
    setError(null);
    setResult(null);
    setValidationErrors({});

    // Validate form using validation.js
    const formData = {
      betslipCode: betslipCode.trim(),
      sourceBookmaker,
      destinationBookmaker
    };

    const validation = window.BetslipValidation.validateConversionForm(formData);
    
    if (!validation.isValid) {
      setValidationErrors(validation.errors);
      const errorMessages = Object.values(validation.errors).filter(Boolean);
      setError(errorMessages[0] || 'Please check your input and try again');
      return;
    }

    setLoading(true);

    try {
      // Make API request
      const response = await axios.post('/api/convert', formData);
      
      if (response.data && response.data.success) {
        setResult(response.data);
        // Update disclaimers if returned in response
        if (response.data.disclaimers) {
          setDisclaimers(response.data.disclaimers);
        }
      } else {
        throw new Error(response.data?.errorMessage || 'Conversion failed');
      }
    } catch (err) {
      const errorMessage = window.BetslipValidation.formatErrorMessage(err);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Reset form to initial state
   */
  const handleNewConversion = () => {
    setBetslipCode('');
    setSourceBookmaker('');
    setDestinationBookmaker('');
    setResult(null);
    setError(null);
    setValidationErrors({});
    // Keep terms acceptance for subsequent conversions
  };

  /**
   * Handle input changes with sanitization and validation
   */
  const handleBetslipCodeChange = (e) => {
    const sanitized = window.BetslipValidation.sanitizeInput(e.target.value);
    setBetslipCode(sanitized);
    
    // Real-time validation
    setTimeout(() => {
      validateFormField('betslipCode', sanitized, {
        betslipCode: sanitized,
        sourceBookmaker,
        destinationBookmaker
      });
    }, 300); // Debounce validation
  };

  const handleSourceBookmakerChange = (e) => {
    const value = e.target.value;
    setSourceBookmaker(value);
    
    // Clear destination if same as source
    if (value === destinationBookmaker) {
      setDestinationBookmaker('');
    }
    
    // Real-time validation
    validateFormField('sourceBookmaker', value, {
      betslipCode,
      sourceBookmaker: value,
      destinationBookmaker
    });
  };

  const handleDestinationBookmakerChange = (e) => {
    const value = e.target.value;
    setDestinationBookmaker(value);
    
    // Real-time validation
    validateFormField('destinationBookmaker', value, {
      betslipCode,
      sourceBookmaker,
      destinationBookmaker: value
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900 text-center">
            Betslip Converter
          </h1>
          <p className="text-gray-600 text-center mt-2">
            Convert your betslips between different bookmakers instantly
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Compliance Notice */}
        {disclaimers && (
          <window.ComplianceNotice disclaimers={disclaimers} />
        )}
        
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          {/* Conversion Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Betslip Code Input */}
            <BetslipCodeInput
              value={betslipCode}
              onChange={handleBetslipCodeChange}
              disabled={loading}
              error={validationErrors.betslipCode}
            />

            {/* Bookmaker Selection Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Source Bookmaker */}
              <BookmakerSelector
                value={sourceBookmaker}
                onChange={handleSourceBookmakerChange}
                bookmakers={bookmakers}
                label="From Bookmaker"
                disabled={loading || bookmarkersLoading}
                error={validationErrors.sourceBookmaker}
              />

              {/* Destination Bookmaker */}
              <BookmakerSelector
                value={destinationBookmaker}
                onChange={handleDestinationBookmakerChange}
                bookmakers={bookmakers}
                label="To Bookmaker"
                disabled={loading || bookmarkersLoading}
                error={validationErrors.destinationBookmaker}
                excludeValue={sourceBookmaker}
              />
            </div>

            {/* General Form Error */}
            {validationErrors.general && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-700">{validationErrors.general}</p>
              </div>
            )}

            {/* Terms and Conditions Acceptance */}
            <div className="flex items-start space-x-3 p-4 bg-gray-50 rounded-lg">
              <input
                type="checkbox"
                id="acceptTerms"
                checked={hasAcceptedTerms}
                onChange={(e) => setHasAcceptedTerms(e.target.checked)}
                className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="acceptTerms" className="text-sm text-gray-700">
                I confirm that I am of legal gambling age and accept the{' '}
                <button
                  type="button"
                  onClick={() => setShowPrivacyPolicy(true)}
                  className="text-blue-600 hover:text-blue-800 underline"
                >
                  Terms of Service and Privacy Policy
                </button>
                . I understand that this service is for convenience only and I am responsible for verifying all betting information.
              </label>
            </div>

            {/* Submit Button */}
            <div className="flex justify-center">
              <button
                type="submit"
                disabled={loading || bookmarkersLoading || !betslipCode.trim() || !sourceBookmaker || !destinationBookmaker || !hasAcceptedTerms}
                className="px-8 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? (
                  <span className="flex items-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Converting...
                  </span>
                ) : bookmarkersLoading ? (
                  'Loading Bookmakers...'
                ) : (
                  'Convert Betslip'
                )}
              </button>
            </div>
          </form>

          {/* Loading State */}
          {loading && (
            <div className="mt-8 text-center">
              <div className="inline-flex items-center px-4 py-2 bg-blue-50 rounded-lg">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span className="text-blue-800">Processing your betslip conversion...</span>
              </div>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="mt-8 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start">
                <svg className="h-5 w-5 text-red-400 mt-0.5 mr-3" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <div className="flex-1">
                  <h3 className="text-sm font-medium text-red-800">Conversion Failed</h3>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Results Display */}
          {result && (
            <ResultsDisplay 
              result={result} 
              onNewConversion={handleNewConversion}
            />
          )}
        </div>

        {/* Footer */}
        <footer className="text-center text-gray-500 text-sm space-y-2">
          <p>
            Please ensure you comply with the terms and conditions of both bookmakers.
            This tool is for convenience only and accuracy is not guaranteed.
          </p>
          <div className="flex justify-center space-x-4">
            <button
              onClick={() => setShowPrivacyPolicy(true)}
              className="text-blue-600 hover:text-blue-800 underline"
            >
              Privacy Policy
            </button>
            <span>•</span>
            <span>Responsible Gambling</span>
            <span>•</span>
            <span>Contact Support</span>
          </div>
          <p className="text-xs">
            If you need help with gambling addiction, please contact the National Problem Gambling Helpline: 1-800-522-4700
          </p>
        </footer>
      </main>
      
      {/* Privacy Policy Modal */}
      <window.PrivacyPolicy 
        isOpen={showPrivacyPolicy} 
        onClose={() => setShowPrivacyPolicy(false)} 
      />
    </div>
  );
}

// Mount the React application
const root = ReactDOM.createRoot(document.getElementById('app'));
root.render(<App />);