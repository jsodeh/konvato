const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const path = require('path');
const cacheManager = require('./cache-manager');
const { complianceManager } = require('./compliance');
const { 
    register, 
    metricsMiddleware, 
    recordConversionMetrics, 
    updateCacheMetrics,
    updateHealthMetrics 
} = require('./metrics');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5000;

// Configuration validation
const validateConfiguration = () => {
    const warnings = [];
    
    if (!process.env.OPENAI_API_KEY) {
        warnings.push('OPENAI_API_KEY not set - browser automation will fail');
    }
    
    if (!process.env.PYTHON_PATH) {
        warnings.push('PYTHON_PATH not set - using default python3');
    }
    
    if (warnings.length > 0) {
        console.warn('Configuration warnings:');
        warnings.forEach(warning => console.warn(`  - ${warning}`));
    }
    
    return warnings.length === 0;
};

// Validate configuration on startup
validateConfiguration();

// Initialize cache manager with bookmaker configurations
const { initializeCache } = require('./cache-init');

initializeCache().catch(error => {
    console.error('Cache manager initialization failed:', error.message);
    console.log('Continuing with in-memory caching only');
});

// Middleware
app.use(cors({
    origin: process.env.CORS_ORIGIN || 'http://localhost:3000'
}));
app.use(express.json());

// Metrics middleware
app.use(metricsMiddleware);

// Compliance middleware
app.use(complianceManager.complianceMiddleware());

// Request logging middleware
app.use((req, res, next) => {
    const timestamp = new Date().toISOString();
    console.log(`[${timestamp}] ${req.method} ${req.path} - IP: ${req.ip}`);
    next();
});

// Simple rate limiting for conversion endpoint
const conversionRequests = new Map();
const RATE_LIMIT_WINDOW = 60000; // 1 minute
const MAX_REQUESTS_PER_WINDOW = 10;

const rateLimitMiddleware = (req, res, next) => {
    const clientIP = req.ip;
    const now = Date.now();
    
    // Clean up old entries
    for (const [ip, requests] of conversionRequests.entries()) {
        conversionRequests.set(ip, requests.filter(time => now - time < RATE_LIMIT_WINDOW));
        if (conversionRequests.get(ip).length === 0) {
            conversionRequests.delete(ip);
        }
    }
    
    // Check current client's requests
    const clientRequests = conversionRequests.get(clientIP) || [];
    
    if (clientRequests.length >= MAX_REQUESTS_PER_WINDOW) {
        return res.status(429).json({
            success: false,
            error: 'Too many requests. Please wait before trying again.',
            code: 'RATE_LIMIT_EXCEEDED',
            retryAfter: Math.ceil(RATE_LIMIT_WINDOW / 1000)
        });
    }
    
    // Add current request
    clientRequests.push(now);
    conversionRequests.set(clientIP, clientRequests);
    
    next();
};

// Enhanced health check endpoint for monitoring
app.get('/health', (req, res) => {
    const cacheStats = cacheManager.getCacheStats();
    res.json({ 
        status: 'OK', 
        message: 'Betslip Converter API is running',
        cache: cacheStats,
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        memory: process.memoryUsage(),
        version: process.env.npm_package_version || '1.0.0'
    });
});

// API health check endpoint for Docker healthcheck
app.get('/api/health', (req, res) => {
    const cacheStats = cacheManager.getCacheStats();
    const healthStatus = {
        status: 'healthy',
        timestamp: new Date().toISOString(),
        services: {
            api: 'healthy',
            cache: cacheStats.connected ? 'healthy' : 'degraded'
        }
    };
    
    // Update health metrics
    updateHealthMetrics('api', true);
    updateHealthMetrics('cache', cacheStats.connected);
    
    res.json(healthStatus);
});

// Metrics endpoint for Prometheus
app.get('/api/metrics', async (req, res) => {
    try {
        res.set('Content-Type', register.contentType);
        res.end(await register.metrics());
    } catch (error) {
        res.status(500).end(error.message);
    }
});

// Compliance disclaimers endpoint
app.get('/api/compliance/disclaimers', (req, res) => {
    const disclaimers = complianceManager.getComplianceDisclaimers();
    res.json({ disclaimers });
});

// Compliance report endpoint (admin only)
app.get('/api/compliance/report', async (req, res) => {
    try {
        const { startDate, endDate } = req.query;
        
        if (!startDate || !endDate) {
            return res.status(400).json({
                success: false,
                error: 'startDate and endDate query parameters are required'
            });
        }
        
        const report = await complianceManager.generateComplianceReport(startDate, endDate);
        res.json({ success: true, report });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// Cache statistics endpoint
app.get('/api/cache/stats', (req, res) => {
    const stats = cacheManager.getCacheStats();
    res.json(stats);
});

// Cache management endpoints (for admin use)
app.delete('/api/cache/game-mappings/:sourceBookmaker/:destinationBookmaker', async (req, res) => {
    try {
        const { sourceBookmaker, destinationBookmaker } = req.params;
        await cacheManager.invalidateGameMappings(sourceBookmaker, destinationBookmaker);
        res.json({ success: true, message: 'Game mappings cache invalidated' });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

app.delete('/api/cache/odds/:bookmaker/:gameId?', async (req, res) => {
    try {
        const { bookmaker, gameId } = req.params;
        await cacheManager.invalidateOddsData(bookmaker, gameId);
        res.json({ success: true, message: 'Odds data cache invalidated' });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// Request validation middleware for conversion endpoint
const validateConversionRequest = (req, res, next) => {
    const { betslipCode, sourceBookmaker, destinationBookmaker } = req.body;
    
    // Check required fields
    if (!betslipCode || !sourceBookmaker || !destinationBookmaker) {
        return res.status(400).json({
            success: false,
            error: 'Missing required fields: betslipCode, sourceBookmaker, destinationBookmaker'
        });
    }
    
    // Validate betslip code format (alphanumeric, 3-50 characters)
    if (!/^[a-zA-Z0-9]{3,50}$/.test(betslipCode)) {
        return res.status(400).json({
            success: false,
            error: 'Invalid betslip code format. Must be alphanumeric, 3-50 characters'
        });
    }
    
    // Validate bookmaker values
    const supportedBookmakers = ['bet9ja', 'sportybet', 'betway', 'bet365'];
    if (!supportedBookmakers.includes(sourceBookmaker) || !supportedBookmakers.includes(destinationBookmaker)) {
        return res.status(400).json({
            success: false,
            error: 'Unsupported bookmaker. Supported: ' + supportedBookmakers.join(', ')
        });
    }
    
    // Ensure source and destination are different
    if (sourceBookmaker === destinationBookmaker) {
        return res.status(400).json({
            success: false,
            error: 'Source and destination bookmakers must be different'
        });
    }
    
    next();
};

// Helper function to execute Python automation script with retry logic
const executePythonScript = (scriptArgs, timeout = 30000, maxRetries = 3) => {
    return new Promise(async (resolve, reject) => {
        let lastError;
        
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                console.log(`Attempt ${attempt}/${maxRetries} - Executing Python script with args:`, scriptArgs);
                
                const result = await executePythonScriptOnce(scriptArgs, timeout);
                console.log(`Script execution successful on attempt ${attempt}`);
                resolve(result);
                return;
                
            } catch (error) {
                lastError = error;
                console.error(`Attempt ${attempt}/${maxRetries} failed:`, error.message);
                
                // Don't retry for certain error types
                if (error.message.includes('PARSE_ERROR') || error.message.includes('INVALID_INPUT')) {
                    reject(error);
                    return;
                }
                
                // Exponential backoff delay (1s, 2s, 4s)
                if (attempt < maxRetries) {
                    const delay = Math.pow(2, attempt - 1) * 1000;
                    console.log(`Waiting ${delay}ms before retry...`);
                    await new Promise(resolve => setTimeout(resolve, delay));
                }
            }
        }
        
        console.error(`All ${maxRetries} attempts failed. Last error:`, lastError.message);
        reject(lastError);
    });
};

// Single execution attempt for Python script
const executePythonScriptOnce = (scriptArgs, timeout = 30000) => {
    return new Promise((resolve, reject) => {
        const pythonPath = process.env.PYTHON_PATH || 'python3';
        const scriptPath = path.join(__dirname, '..', 'automation', 'convert_betslip.py');
        
        const pythonProcess = spawn(pythonPath, [scriptPath, ...scriptArgs], {
            stdio: ['pipe', 'pipe', 'pipe'],
            env: { ...process.env }
        });
        
        let stdout = '';
        let stderr = '';
        
        // Set up timeout
        const timeoutId = setTimeout(() => {
            console.error(`Python script timeout after ${timeout}ms`);
            pythonProcess.kill('SIGTERM');
            reject(new Error('TIMEOUT'));
        }, timeout);
        
        pythonProcess.stdout.on('data', (data) => {
            stdout += data.toString();
        });
        
        pythonProcess.stderr.on('data', (data) => {
            stderr += data.toString();
            console.error('Python script stderr:', data.toString());
        });
        
        pythonProcess.on('close', (code) => {
            clearTimeout(timeoutId);
            
            console.log(`Python script exited with code ${code}`);
            
            if (code === 0) {
                try {
                    const result = JSON.parse(stdout);
                    resolve(result);
                } catch (parseError) {
                    console.error('Failed to parse Python script output:', parseError.message);
                    console.error('Raw stdout:', stdout);
                    reject(new Error('PARSE_ERROR: ' + parseError.message));
                }
            } else {
                console.error('Python script failed with stderr:', stderr);
                reject(new Error('SCRIPT_ERROR: ' + stderr || 'Unknown error'));
            }
        });
        
        pythonProcess.on('error', (error) => {
            clearTimeout(timeoutId);
            console.error('Python process error:', error.message);
            reject(new Error('PROCESS_ERROR: ' + error.message));
        });
    });
};

// Helper function to format conversion response
const formatConversionResponse = (result, processingTime) => {
    const response = {
        success: result.success,
        betslipCode: result.new_betslip_code || null,
        selections: result.converted_selections || [],
        warnings: result.warnings || [],
        processingTime: processingTime,
        partialConversion: result.partial_conversion || false,
        timestamp: new Date().toISOString()
    };
    
    // Add error information if conversion failed
    if (!result.success && result.error) {
        response.error = result.error;
    }
    
    // Add statistics
    response.stats = {
        totalSelections: response.selections.length,
        convertedSelections: response.selections.filter(s => s.status === 'converted').length,
        partialSelections: response.selections.filter(s => s.status === 'partial').length,
        unavailableSelections: response.selections.filter(s => s.status === 'unavailable').length
    };
    
    // Add compliance disclaimers
    response.disclaimers = complianceManager.getComplianceDisclaimers();
    
    // Sanitize response data for privacy
    return complianceManager.sanitizeData(response, 'conversion');
};

// Helper function to handle conversion errors with detailed logging
const handleConversionError = (error, res, requestId = null) => {
    const errorDetails = {
        message: error.message,
        stack: error.stack,
        timestamp: new Date().toISOString(),
        requestId: requestId
    };
    
    console.error('Conversion error details:', errorDetails);
    
    if (error.message === 'TIMEOUT') {
        return res.status(408).json({
            success: false,
            error: 'Conversion request timed out after 30 seconds. Please try again.',
            code: 'TIMEOUT',
            requestId: requestId
        });
    }
    
    if (error.message.startsWith('PARSE_ERROR')) {
        return res.status(500).json({
            success: false,
            error: 'Failed to process conversion result. The automation script returned invalid data.',
            code: 'PARSE_ERROR',
            requestId: requestId
        });
    }
    
    if (error.message.startsWith('SCRIPT_ERROR')) {
        return res.status(500).json({
            success: false,
            error: 'Browser automation failed. This may be due to bookmaker site changes or anti-bot measures.',
            code: 'SCRIPT_ERROR',
            requestId: requestId
        });
    }
    
    if (error.message.startsWith('PROCESS_ERROR')) {
        return res.status(500).json({
            success: false,
            error: 'Failed to execute conversion process. Please check system configuration.',
            code: 'PROCESS_ERROR',
            requestId: requestId
        });
    }
    
    // Generic error
    return res.status(500).json({
        success: false,
        error: 'An unexpected error occurred during conversion. Please try again later.',
        code: 'UNKNOWN_ERROR',
        requestId: requestId
    });
};

// Conversion API endpoint with caching
app.post('/api/convert', rateLimitMiddleware, validateConversionRequest, async (req, res) => {
    const startTime = Date.now();
    const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const { betslipCode, sourceBookmaker, destinationBookmaker } = req.body;
    
    try {
        console.log(`[${requestId}] Starting conversion: ${betslipCode} from ${sourceBookmaker} to ${destinationBookmaker}`);
        
        // Check cache for recent conversion result
        const cachedResult = await cacheManager.getConversionResult(betslipCode, sourceBookmaker, destinationBookmaker);
        if (cachedResult) {
            const processingTime = Date.now() - startTime;
            const response = formatConversionResponse(cachedResult.result, processingTime);
            response.fromCache = true;
            response.originalProcessingTime = cachedResult.processingTime;
            response.requestId = requestId;
            
            console.log(`[${requestId}] Returning cached result in ${processingTime}ms (original: ${cachedResult.processingTime}ms)`);
            return res.json(response);
        }
        
        // Execute Python automation script with retry logic and 30-second timeout
        const scriptArgs = [betslipCode, sourceBookmaker, destinationBookmaker];
        const result = await executePythonScript(scriptArgs, 30000, 3); // 30s timeout, 3 retries
        
        const processingTime = Date.now() - startTime;
        const response = formatConversionResponse(result, processingTime);
        
        // Record metrics and cache results
        recordConversionMetrics(sourceBookmaker, destinationBookmaker, processingTime / 1000, result.success);
        
        // Cache the successful result (sanitized)
        if (result.success) {
            const sanitizedResult = complianceManager.sanitizeData(result, 'conversion');
            await cacheManager.cacheConversionResult('[REDACTED]', sourceBookmaker, destinationBookmaker, sanitizedResult, processingTime);
            
            // Log successful conversion for compliance
            await complianceManager.logComplianceEvent('CONVERSION_SUCCESS', {
                sourceBookmaker,
                destinationBookmaker,
                selectionsCount: result.converted_selections?.length || 0,
                processingTime
            }, req.ip, requestId);
        } else {
            // Log failed conversion
            await complianceManager.logComplianceEvent('CONVERSION_FAILED', {
                sourceBookmaker,
                destinationBookmaker,
                error: result.error || 'Unknown error'
            }, req.ip, requestId);
        }
        
        console.log(`[${requestId}] Conversion completed successfully in ${processingTime}ms`);
        console.log(`[${requestId}] Result summary: ${response.success ? 'SUCCESS' : 'FAILED'}, ` +
                   `selections: ${response.selections.length}, warnings: ${response.warnings.length}`);
        
        // Add request ID to response for tracking
        response.requestId = requestId;
        res.json(response);
        
    } catch (error) {
        const processingTime = Date.now() - startTime;
        console.error(`[${requestId}] Conversion failed after ${processingTime}ms:`, error.message);
        
        // Record failure metrics
        let errorType = 'unknown';
        if (error.message === 'TIMEOUT') errorType = 'timeout';
        else if (error.message.includes('SCRIPT_ERROR')) errorType = 'browser_error';
        else if (error.message.includes('antibot')) errorType = 'antibot_detection';
        
        recordConversionMetrics(sourceBookmaker, destinationBookmaker, processingTime / 1000, false, errorType);
        
        handleConversionError(error, res, requestId);
    }
});

app.get('/api/bookmakers', async (req, res) => {
    try {
        // Try to get bookmaker configurations from cache
        const bookmakers = [];
        const bookmakerIds = ['bet9ja', 'sportybet', 'betway', 'bet365'];
        
        for (const id of bookmakerIds) {
            const config = await cacheManager.getBookmakerConfig(id);
            bookmakers.push({
                id,
                name: id.charAt(0).toUpperCase() + id.slice(1),
                supported: true,
                cached: !!config
            });
        }
        
        res.json({ bookmakers });
    } catch (error) {
        console.error('Error fetching bookmaker configurations:', error.message);
        // Fallback to static configuration
        res.json({
            bookmakers: [
                { id: 'bet9ja', name: 'Bet9ja', supported: true },
                { id: 'sportybet', name: 'Sportybet', supported: true },
                { id: 'betway', name: 'Betway', supported: true },
                { id: 'bet365', name: 'Bet365', supported: true }
            ]
        });
    }
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ error: 'Something went wrong!' });
});

const server = app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});

// Graceful shutdown handling
process.on('SIGTERM', async () => {
    console.log('SIGTERM received, shutting down gracefully');
    server.close(async () => {
        await cacheManager.cleanup();
        process.exit(0);
    });
});

process.on('SIGINT', async () => {
    console.log('SIGINT received, shutting down gracefully');
    server.close(async () => {
        await cacheManager.cleanup();
        process.exit(0);
    });
});

module.exports = app;