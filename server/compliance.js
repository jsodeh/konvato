const fs = require('fs').promises;
const path = require('path');

/**
 * Compliance and Privacy Protection Module
 * Handles data retention policies, privacy protection, and compliance auditing
 */

class ComplianceManager {
    constructor() {
        this.dataRetentionPolicies = {
            betslipCodes: 0, // Never store betslip codes
            conversionResults: 24 * 60 * 60 * 1000, // 24 hours for caching only
            userSessions: 30 * 60 * 1000, // 30 minutes
            auditLogs: 90 * 24 * 60 * 60 * 1000, // 90 days
            errorLogs: 30 * 24 * 60 * 60 * 1000 // 30 days
        };
        
        this.auditLog = [];
        this.maxAuditLogSize = 10000; // Maximum number of audit entries
        
        // Initialize audit log file path
        this.auditLogPath = path.join(__dirname, 'logs', 'compliance-audit.log');
        this.ensureLogDirectory();
    }
    
    async ensureLogDirectory() {
        const logDir = path.dirname(this.auditLogPath);
        try {
            await fs.mkdir(logDir, { recursive: true });
        } catch (error) {
            console.error('Failed to create log directory:', error.message);
        }
    }
    
    /**
     * Log compliance-related events for auditing
     */
    async logComplianceEvent(eventType, details, userIP = null, requestId = null) {
        const auditEntry = {
            timestamp: new Date().toISOString(),
            eventType,
            details,
            userIP: this.anonymizeIP(userIP),
            requestId,
            id: `audit_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
        };
        
        // Add to in-memory log
        this.auditLog.push(auditEntry);
        
        // Maintain log size limit
        if (this.auditLog.length > this.maxAuditLogSize) {
            this.auditLog = this.auditLog.slice(-this.maxAuditLogSize);
        }
        
        // Write to file for persistence
        try {
            const logLine = JSON.stringify(auditEntry) + '\n';
            await fs.appendFile(this.auditLogPath, logLine);
        } catch (error) {
            console.error('Failed to write audit log:', error.message);
        }
        
        console.log(`[COMPLIANCE] ${eventType}: ${JSON.stringify(details)}`);
    }
    
    /**
     * Anonymize IP addresses for privacy protection
     */
    anonymizeIP(ip) {
        if (!ip) return null;
        
        // For IPv4, mask the last octet
        if (ip.includes('.')) {
            const parts = ip.split('.');
            if (parts.length === 4) {
                return `${parts[0]}.${parts[1]}.${parts[2]}.xxx`;
            }
        }
        
        // For IPv6, mask the last 64 bits
        if (ip.includes(':')) {
            const parts = ip.split(':');
            if (parts.length >= 4) {
                return parts.slice(0, 4).join(':') + '::xxxx';
            }
        }
        
        return 'xxx.xxx.xxx.xxx';
    }
    
    /**
     * Sanitize data to remove sensitive information
     */
    sanitizeData(data, dataType = 'general') {
        if (!data) return data;
        
        const sanitized = JSON.parse(JSON.stringify(data));
        
        switch (dataType) {
            case 'betslip':
                // Never store actual betslip codes
                if (sanitized.betslipCode) {
                    sanitized.betslipCode = '[REDACTED]';
                }
                break;
                
            case 'conversion':
                // Remove sensitive betslip information
                if (sanitized.betslipCode) {
                    sanitized.betslipCode = '[REDACTED]';
                }
                if (sanitized.selections) {
                    sanitized.selections = sanitized.selections.map(selection => ({
                        ...selection,
                        originalText: '[REDACTED]'
                    }));
                }
                break;
                
            case 'error':
                // Remove stack traces and sensitive paths
                if (sanitized.stack) {
                    sanitized.stack = '[REDACTED]';
                }
                if (sanitized.message && sanitized.message.includes(process.cwd())) {
                    sanitized.message = sanitized.message.replace(new RegExp(process.cwd(), 'g'), '[PATH]');
                }
                break;
        }
        
        return sanitized;
    }
    
    /**
     * Check if data should be retained based on retention policies
     */
    shouldRetainData(dataType, timestamp) {
        const retentionPeriod = this.dataRetentionPolicies[dataType];
        if (retentionPeriod === 0) return false; // Never retain
        
        const dataAge = Date.now() - new Date(timestamp).getTime();
        return dataAge < retentionPeriod;
    }
    
    /**
     * Clean up expired data based on retention policies
     */
    async cleanupExpiredData() {
        const now = Date.now();
        
        // Clean up audit logs
        const auditRetention = this.dataRetentionPolicies.auditLogs;
        this.auditLog = this.auditLog.filter(entry => {
            const entryAge = now - new Date(entry.timestamp).getTime();
            return entryAge < auditRetention;
        });
        
        await this.logComplianceEvent('DATA_CLEANUP', {
            action: 'expired_data_cleanup',
            auditLogSize: this.auditLog.length
        });
    }
    
    /**
     * Generate compliance report
     */
    async generateComplianceReport(startDate, endDate) {
        const start = new Date(startDate);
        const end = new Date(endDate);
        
        const relevantLogs = this.auditLog.filter(entry => {
            const entryDate = new Date(entry.timestamp);
            return entryDate >= start && entryDate <= end;
        });
        
        const report = {
            period: { start: start.toISOString(), end: end.toISOString() },
            totalEvents: relevantLogs.length,
            eventsByType: {},
            dataRetentionCompliance: {
                policies: this.dataRetentionPolicies,
                lastCleanup: new Date().toISOString()
            },
            privacyMeasures: {
                ipAnonymization: true,
                dataSanitization: true,
                noSensitiveDataStorage: true
            }
        };
        
        // Count events by type
        relevantLogs.forEach(entry => {
            report.eventsByType[entry.eventType] = (report.eventsByType[entry.eventType] || 0) + 1;
        });
        
        await this.logComplianceEvent('COMPLIANCE_REPORT_GENERATED', {
            reportPeriod: report.period,
            totalEvents: report.totalEvents
        });
        
        return report;
    }
    
    /**
     * Validate request for compliance
     */
    validateRequestCompliance(req) {
        const issues = [];
        
        // Check for suspicious patterns
        const { betslipCode, sourceBookmaker, destinationBookmaker } = req.body || {};
        
        if (betslipCode && betslipCode.length > 50) {
            issues.push('Betslip code exceeds maximum length');
        }
        
        if (betslipCode && !/^[a-zA-Z0-9]+$/.test(betslipCode)) {
            issues.push('Betslip code contains invalid characters');
        }
        
        return {
            compliant: issues.length === 0,
            issues
        };
    }
    
    /**
     * Get compliance disclaimers and notices
     */
    getComplianceDisclaimers() {
        return {
            accuracy: "This service provides automated betslip conversion for convenience only. Users are responsible for verifying all selections, odds, and terms before placing bets.",
            responsibility: "Users must ensure compliance with local gambling laws and bookmaker terms of service. This service does not encourage or facilitate illegal gambling.",
            privacy: "We do not store betslip codes or personal betting information. All data is processed temporarily and discarded after conversion.",
            terms: "By using this service, you acknowledge that you are of legal gambling age and accept full responsibility for your betting activities.",
            accuracy_notice: "Odds and market availability may change between conversion and bet placement. Always verify final selections on the destination bookmaker.",
            liability: "This service is provided 'as is' without warranties. We are not liable for any losses resulting from conversion errors or system failures."
        };
    }
    
    /**
     * Middleware for compliance logging
     */
    complianceMiddleware() {
        return async (req, res, next) => {
            const startTime = Date.now();
            const requestId = req.headers['x-request-id'] || `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            
            // Log request
            await this.logComplianceEvent('REQUEST_RECEIVED', {
                method: req.method,
                path: req.path,
                userAgent: req.get('User-Agent'),
                contentLength: req.get('Content-Length')
            }, req.ip, requestId);
            
            // Validate compliance
            const complianceCheck = this.validateRequestCompliance(req);
            if (!complianceCheck.compliant) {
                await this.logComplianceEvent('COMPLIANCE_VIOLATION', {
                    issues: complianceCheck.issues,
                    path: req.path
                }, req.ip, requestId);
                
                return res.status(400).json({
                    success: false,
                    error: 'Request does not meet compliance requirements',
                    issues: complianceCheck.issues
                });
            }
            
            // Override res.json to log responses
            const originalJson = res.json;
            res.json = function(data) {
                const processingTime = Date.now() - startTime;
                
                // Log response (sanitized)
                complianceManager.logComplianceEvent('RESPONSE_SENT', {
                    statusCode: res.statusCode,
                    processingTime,
                    success: data.success,
                    hasError: !!data.error
                }, req.ip, requestId);
                
                return originalJson.call(this, data);
            };
            
            next();
        };
    }
}

// Create singleton instance
const complianceManager = new ComplianceManager();

// Schedule periodic cleanup (every hour)
setInterval(() => {
    complianceManager.cleanupExpiredData().catch(error => {
        console.error('Compliance cleanup failed:', error.message);
    });
}, 60 * 60 * 1000); // 1 hour

module.exports = {
    ComplianceManager,
    complianceManager
};