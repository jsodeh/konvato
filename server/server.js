const express = require('express');
const cors = require('cors');
const axios = require('axios');
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
    
    if (!process.env.GROQ_API_KEY && !process.env.OPENAI_API_KEY && !process.env.ANTHROPIC_API_KEY) {
        warnings.push('No LLM API key found. At least one of GROQ_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY must be set.');
    }
    
    if (!process.env.AUTOMATION_SERVICE_URL) {
        warnings.push('AUTOMATION_SERVICE_URL not set - the server cannot connect to the automation service.');
    }
    
    if (warnings.length > 0) {
        console.warn('Configuration warnings:');
        warnings.forEach(warning => console.warn(`  - ${warning}`));
    }
    
    return warnings.length === 0;
};

// Validate configuration on startup
validateConfiguration();

// Initialize cache manager
const { initializeCache } = require('./cache-init');
initializeCache().catch(error => {
    console.error('Cache manager initialization failed:', error.message);
    console.log('Continuing with in-memory caching only');
});

// Middleware
app.use(cors({
    origin: process.env.CORS_ORIGIN || process.env.NODE_ENV === 'production' 
        ? [process.env.CORS_ORIGIN, 'https://konvato-client.onrender.com']
        : ['http://localhost:3000', 'http://localhost:3001', 'http://127.0.0.1:3000'],
    credentials: true
}));
app.use(express.json());
app.use(metricsMiddleware);
app.use(complianceManager.complianceMiddleware());

// Request logging
app.use((req, res, next) => {
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.path} - IP: ${req.ip}`);
    next();
});

// Rate limiting
const conversionRequests = new Map();
const RATE_LIMIT_WINDOW = 60000;
const MAX_REQUESTS_PER_WINDOW = 15;

const rateLimitMiddleware = (req, res, next) => {
    const clientIP = req.ip;
    const now = Date.now();
    
    const clientRequests = (conversionRequests.get(clientIP) || []).filter(time => now - time < RATE_LIMIT_WINDOW);
    
    if (clientRequests.length >= MAX_REQUESTS_PER_WINDOW) {
        return res.status(429).json({
            success: false,
            error: 'Too many requests. Please wait before trying again.',
            code: 'RATE_LIMIT_EXCEEDED'
        });
    }
    
    clientRequests.push(now);
    conversionRequests.set(clientIP, clientRequests);
    
    next();
};

// --- Core Endpoints ---

app.get('/health', (req, res) => {
    res.json({ 
        status: 'OK', 
        message: 'Betslip Converter API is running',
        timestamp: new Date().toISOString(),
    });
});

app.get('/api/bookmakers', (req, res) => {
    // Return list of supported bookmakers
    const bookmakers = [
        { id: 'bet9ja', name: 'Bet9ja', baseUrl: 'https://bet9ja.com', supported: true },
        { id: 'sportybet', name: 'SportyBet', baseUrl: 'https://sportybet.com', supported: true },
        { id: 'betway', name: 'Betway', baseUrl: 'https://betway.com', supported: true },
        { id: 'bet365', name: 'Bet365', baseUrl: 'https://bet365.com', supported: true },
        { id: '1xbet', name: '1xBet', baseUrl: 'https://1xbet.com', supported: true },
        { id: 'melbet', name: 'MelBet', baseUrl: 'https://melbet.com', supported: true }
    ];
    
    res.json({
        success: true,
        bookmakers: bookmakers
    });
});

app.get('/api/compliance/disclaimers', (req, res) => {
    // Return compliance disclaimers
    const disclaimers = [
        {
            type: 'educational',
            title: 'Educational Use Only',
            content: 'This tool is for educational and research purposes only. Users are responsible for complying with local gambling laws and bookmaker terms of service.'
        },
        {
            type: 'responsibility',
            title: 'User Responsibility',
            content: 'By using this service, you acknowledge that you are solely responsible for your betting activities and any consequences thereof.'
        },
        {
            type: 'accuracy',
            title: 'No Guarantees',
            content: 'While we strive for accuracy, we cannot guarantee the correctness of converted betslips. Always verify odds and selections before placing bets.'
        }
    ];
    
    res.json({
        success: true,
        disclaimers: disclaimers
    });
});

app.get('/api/metrics', async (req, res) => {
    try {
        res.set('Content-Type', register.contentType);
        res.end(await register.metrics());
    } catch (error) {
        res.status(500).end(error.message);
    }
});

// --- Helper Functions ---

// Calls the automation service API with retry logic
const callAutomationService = async (payload, maxRetries = 3) => {
    const automationUrl = `${process.env.AUTOMATION_SERVICE_URL}/convert`;
    let lastError;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            console.log(`Attempt ${attempt}/${maxRetries} - Calling automation service at ${automationUrl}`);
            const response = await axios.post(automationUrl, payload, {
                timeout: 60000 // 60-second timeout for the automation task
            });
            console.log(`Automation service call successful on attempt ${attempt}`);
            return response.data;
        } catch (error) {
            lastError = error;
            console.error(`Attempt ${attempt}/${maxRetries} failed:`, error.message);

            if (error.response) {
                console.error('Automation service responded with error:', error.response.data);
                // Don't retry on client-side errors from the automation service
                if (error.response.status >= 400 && error.response.status < 500) {
                    throw new Error(`AUTOMATION_CLIENT_ERROR: ${error.response.data.detail || 'Bad Request'}`);
                }
            } else if (error.code === 'ECONNABORTED') {
                 console.error('Automation service call timed out.');
            }
            
            if (attempt < maxRetries) {
                const delay = Math.pow(2, attempt - 1) * 1000;
                console.log(`Waiting ${delay}ms before retry...`);
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
    }
    
    console.error(`All ${maxRetries} attempts to call automation service failed.`);
    if (lastError.code === 'ECONNABORTED') {
        throw new Error('AUTOMATION_TIMEOUT');
    }
    throw new Error(`AUTOMATION_SERVICE_UNAVAILABLE: ${lastError.message}`);
};

const formatConversionResponse = (result, processingTime) => {
    // ... (omitting for brevity, same as original)
};

const handleConversionError = (error, res, requestId) => {
    const errorDetails = {
        message: error.message,
        timestamp: new Date().toISOString(),
        requestId: requestId
    };
    console.error('Conversion error details:', errorDetails);

    let statusCode = 500;
    let errorCode = 'UNKNOWN_ERROR';
    let errorMessage = 'An unexpected error occurred during conversion.';

    if (error.message === 'AUTOMATION_TIMEOUT') {
        statusCode = 504; // Gateway Timeout
        errorCode = 'AUTOMATION_TIMEOUT';
        errorMessage = 'The conversion process timed out. The bookmaker site may be slow or unresponsive.';
    } else if (error.message.startsWith('AUTOMATION_SERVICE_UNAVAILABLE')) {
        statusCode = 503; // Service Unavailable
        errorCode = 'AUTOMATION_UNAVAILABLE';
        errorMessage = 'The automation service is currently unavailable. Please try again later.';
    } else if (error.message.startsWith('AUTOMATION_CLIENT_ERROR')) {
        statusCode = 400;
        errorCode = 'AUTOMATION_CLIENT_ERROR';
        errorMessage = `The automation service reported an error: ${error.message.replace('AUTOMATION_CLIENT_ERROR: ', '')}`;
    }

    return res.status(statusCode).json({
        success: false,
        error: errorMessage,
        code: errorCode,
        requestId: requestId
    });
};


// --- Main Conversion Endpoint ---

app.post('/api/convert', rateLimitMiddleware, async (req, res) => {
    const startTime = Date.now();
    const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const { betslipCode, sourceBookmaker, destinationBookmaker } = req.body;

    // Basic validation
    if (!betslipCode || !sourceBookmaker || !destinationBookmaker) {
        return res.status(400).json({ success: false, error: 'Missing required fields.' });
    }

    try {
        console.log(`[${requestId}] Starting conversion: ${betslipCode} from ${sourceBookmaker} to ${destinationBookmaker}`);
        
        // Check cache
        const cachedResult = await cacheManager.getConversionResult(betslipCode, sourceBookmaker, destinationBookmaker);
        if (cachedResult) {
            const processingTime = Date.now() - startTime;
            console.log(`[${requestId}] Returning cached result in ${processingTime}ms`);
            return res.json({ ...cachedResult, fromCache: true, requestId });
        }

        // Call the automation microservice
        const result = await callAutomationService({
            betslip_code: betslipCode,
            source_bookmaker: sourceBookmaker,
            destination_bookmaker: destinationBookmaker
        });
        
        const processingTime = Date.now() - startTime;

        // Record metrics
        recordConversionMetrics(sourceBookmaker, destinationBookmaker, processingTime / 1000, result.success);
        
        // Cache successful results
        if (result.success) {
            await cacheManager.cacheConversionResult(betslipCode, sourceBookmaker, destinationBookmaker, result, processingTime);
        }
        
        console.log(`[${requestId}] Conversion completed in ${processingTime}ms. Success: ${result.success}`);
        res.json({ ...result, processingTime, fromCache: false, requestId });

    } catch (error) {
        const processingTime = Date.now() - startTime;
        console.error(`[${requestId}] Conversion failed after ${processingTime}ms:`, error.message);
        recordConversionMetrics(sourceBookmaker, destinationBookmaker, processingTime / 1000, false, error.code || 'unknown');
        handleConversionError(error, res, requestId);
    }
});


// --- Server Initialization ---

const server = app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});

process.on('SIGTERM', () => {
    console.log('SIGTERM received, shutting down gracefully');
    server.close(async () => {
        await cacheManager.cleanup();
        process.exit(0);
    });
});

process.on('SIGINT', () => {
    console.log('SIGINT received, shutting down gracefully');
    server.close(async () => {
        await cacheManager.cleanup();
        process.exit(0);
    });
});

module.exports = app;
