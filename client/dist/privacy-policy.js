/**
 * Privacy Policy and Terms of Service Component
 * Displays compliance information and user agreements
 */

const { useState, useEffect } = React;

const PrivacyPolicy = ({ isOpen, onClose }) => {
    if (!isOpen) return null;
    
    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-4xl max-h-[90vh] overflow-y-auto">
                <div className="p-6">
                    <div className="flex justify-between items-center mb-4">
                        <h2 className="text-2xl font-bold">Privacy Policy & Terms of Service</h2>
                        <button 
                            onClick={onClose}
                            className="text-gray-500 hover:text-gray-700 text-2xl"
                        >
                            ×
                        </button>
                    </div>
                    
                    <div className="space-y-6 text-sm text-gray-700">
                        <section>
                            <h3 className="text-lg font-semibold mb-2 text-gray-900">Privacy Policy</h3>
                            <div className="space-y-3">
                                <p>
                                    <strong>Data Collection:</strong> We do not store or retain betslip codes, personal betting information, 
                                    or any sensitive gambling data. All conversion requests are processed temporarily and data is discarded 
                                    immediately after processing.
                                </p>
                                <p>
                                    <strong>IP Address Anonymization:</strong> IP addresses are anonymized in our logs for security purposes. 
                                    We do not track or profile individual users.
                                </p>
                                <p>
                                    <strong>Cookies:</strong> This service does not use cookies or tracking technologies. 
                                    No personal data is stored in your browser.
                                </p>
                                <p>
                                    <strong>Third-Party Services:</strong> We interact with bookmaker websites only to perform 
                                    the requested conversions. We do not share your data with any third parties.
                                </p>
                                <p>
                                    <strong>Data Retention:</strong> Conversion results may be cached temporarily (up to 24 hours) 
                                    for performance purposes only. All cached data is automatically purged.
                                </p>
                            </div>
                        </section>
                        
                        <section>
                            <h3 className="text-lg font-semibold mb-2 text-gray-900">Terms of Service</h3>
                            <div className="space-y-3">
                                <p>
                                    <strong>Service Purpose:</strong> This service provides automated betslip conversion 
                                    for convenience only. Users are responsible for verifying all selections, odds, 
                                    and terms before placing bets.
                                </p>
                                <p>
                                    <strong>User Responsibility:</strong> Users must ensure compliance with local gambling 
                                    laws and bookmaker terms of service. This service does not encourage or facilitate 
                                    illegal gambling activities.
                                </p>
                                <p>
                                    <strong>Age Verification:</strong> By using this service, you confirm that you are 
                                    of legal gambling age in your jurisdiction (typically 18+ or 21+).
                                </p>
                                <p>
                                    <strong>Accuracy Disclaimer:</strong> Odds and market availability may change between 
                                    conversion and bet placement. Always verify final selections on the destination bookmaker.
                                </p>
                                <p>
                                    <strong>Service Availability:</strong> This service is provided "as is" without warranties. 
                                    We may experience downtime due to bookmaker changes or technical issues.
                                </p>
                                <p>
                                    <strong>Limitation of Liability:</strong> We are not liable for any losses resulting 
                                    from conversion errors, system failures, or betting decisions made using this service.
                                </p>
                            </div>
                        </section>
                        
                        <section>
                            <h3 className="text-lg font-semibold mb-2 text-gray-900">Responsible Gambling</h3>
                            <div className="space-y-3">
                                <p>
                                    <strong>Gambling Awareness:</strong> Gambling can be addictive. Please gamble responsibly 
                                    and within your means.
                                </p>
                                <p>
                                    <strong>Help Resources:</strong> If you need help with gambling addiction, please contact:
                                </p>
                                <ul className="list-disc list-inside ml-4 space-y-1">
                                    <li>National Problem Gambling Helpline: 1-800-522-4700</li>
                                    <li>Gamblers Anonymous: www.gamblersanonymous.org</li>
                                    <li>National Council on Problem Gambling: www.ncpgambling.org</li>
                                </ul>
                                <p>
                                    <strong>Self-Exclusion:</strong> Most bookmakers offer self-exclusion tools. 
                                    Please use these if you need to limit your gambling activities.
                                </p>
                            </div>
                        </section>
                        
                        <section>
                            <h3 className="text-lg font-semibold mb-2 text-gray-900">Contact Information</h3>
                            <p>
                                For questions about this privacy policy or terms of service, please contact us through 
                                the appropriate channels provided by your bookmaker or gambling regulatory authority.
                            </p>
                        </section>
                    </div>
                    
                    <div className="mt-6 pt-4 border-t">
                        <p className="text-xs text-gray-500">
                            Last updated: {new Date().toLocaleDateString()}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

const ComplianceNotice = ({ disclaimers }) => {
    const [showDetails, setShowDetails] = useState(false);
    
    if (!disclaimers) return null;
    
    return (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
            <div className="flex items-start">
                <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                </div>
                <div className="ml-3 flex-1">
                    <h3 className="text-sm font-medium text-yellow-800">
                        Important Notice
                    </h3>
                    <div className="mt-2 text-sm text-yellow-700">
                        <p>{disclaimers.responsibility}</p>
                        <button 
                            onClick={() => setShowDetails(!showDetails)}
                            className="mt-2 text-yellow-800 underline hover:text-yellow-900"
                        >
                            {showDetails ? 'Hide Details' : 'View Full Disclaimers'}
                        </button>
                    </div>
                    
                    {showDetails && (
                        <div className="mt-4 space-y-3 text-sm text-yellow-700">
                            <div>
                                <strong>Accuracy:</strong> {disclaimers.accuracy}
                            </div>
                            <div>
                                <strong>Privacy:</strong> {disclaimers.privacy}
                            </div>
                            <div>
                                <strong>Terms:</strong> {disclaimers.terms}
                            </div>
                            <div>
                                <strong>Liability:</strong> {disclaimers.liability}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

// Export components for use in main app
window.PrivacyPolicy = PrivacyPolicy;
window.ComplianceNotice = ComplianceNotice;