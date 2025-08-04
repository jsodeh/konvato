/**
 * Application metrics collection for monitoring
 * Provides Prometheus-compatible metrics for the betslip converter
 */

const promClient = require('prom-client');

// Create a Registry to register the metrics
const register = new promClient.Registry();

// Add default metrics (CPU, memory, etc.)
promClient.collectDefaultMetrics({
    register,
    prefix: 'betslip_converter_'
});

// Custom metrics for betslip converter
const httpRequestsTotal = new promClient.Counter({
    name: 'http_requests_total',
    help: 'Total number of HTTP requests',
    labelNames: ['method', 'route', 'status'],
    registers: [register]
});

const httpRequestDuration = new promClient.Histogram({
    name: 'http_request_duration_seconds',
    help: 'Duration of HTTP requests in seconds',
    labelNames: ['method', 'route', 'status'],
    buckets: [0.1, 0.5, 1, 2, 5, 10, 30],
    registers: [register]
});

const conversionRequestsTotal = new promClient.Counter({
    name: 'conversion_requests_total',
    help: 'Total number of betslip conversion requests',
    labelNames: ['source_bookmaker', 'destination_bookmaker', 'status'],
    registers: [register]
});

const conversionDuration = new promClient.Histogram({
    name: 'conversion_duration_seconds',
    help: 'Duration of betslip conversions in seconds',
    labelNames: ['source_bookmaker', 'destination_bookmaker'],
    buckets: [1, 5, 10, 15, 20, 30, 45, 60],
    registers: [register]
});

const conversionTimeouts = new promClient.Counter({
    name: 'conversion_timeouts_total',
    help: 'Total number of conversion timeouts',
    labelNames: ['source_bookmaker', 'destination_bookmaker'],
    registers: [register]
});

const browserAutomationFailures = new promClient.Counter({
    name: 'browser_automation_failures_total',
    help: 'Total number of browser automation failures',
    labelNames: ['bookmaker', 'error_type'],
    registers: [register]
});

const antibotDetections = new promClient.Counter({
    name: 'antibot_detections_total',
    help: 'Total number of anti-bot detections',
    labelNames: ['bookmaker'],
    registers: [register]
});

const cacheHitRate = new promClient.Gauge({
    name: 'cache_hit_rate',
    help: 'Cache hit rate (0-1)',
    registers: [register]
});

const cacheOperations = new promClient.Counter({
    name: 'cache_operations_total',
    help: 'Total number of cache operations',
    labelNames: ['operation', 'result'],
    registers: [register]
});

const activeBrowserSessions = new promClient.Gauge({
    name: 'active_browser_sessions',
    help: 'Number of active browser automation sessions',
    registers: [register]
});

const memoryUsage = new promClient.Gauge({
    name: 'memory_usage_bytes',
    help: 'Memory usage in bytes',
    labelNames: ['type'],
    registers: [register]
});

// Middleware to collect HTTP metrics
const metricsMiddleware = (req, res, next) => {
    const start = Date.now();
    
    res.on('finish', () => {
        const duration = (Date.now() - start) / 1000;
        const route = req.route ? req.route.path : req.path;
        const status = res.statusCode.toString();
        
        httpRequestsTotal.inc({
            method: req.method,
            route: route,
            status: status
        });
        
        httpRequestDuration.observe({
            method: req.method,
            route: route,
            status: status
        }, duration);
    });
    
    next();
};

// Function to record conversion metrics
const recordConversionMetrics = (sourceBookmaker, destinationBookmaker, duration, success, errorType = null) => {
    const status = success ? 'success' : 'failure';
    
    conversionRequestsTotal.inc({
        source_bookmaker: sourceBookmaker,
        destination_bookmaker: destinationBookmaker,
        status: status
    });
    
    if (success) {
        conversionDuration.observe({
            source_bookmaker: sourceBookmaker,
            destination_bookmaker: destinationBookmaker
        }, duration);
    }
    
    if (errorType === 'timeout') {
        conversionTimeouts.inc({
            source_bookmaker: sourceBookmaker,
            destination_bookmaker: destinationBookmaker
        });
    }
    
    if (errorType && errorType.includes('browser')) {
        browserAutomationFailures.inc({
            bookmaker: sourceBookmaker,
            error_type: errorType
        });
    }
    
    if (errorType && errorType.includes('antibot')) {
        antibotDetections.inc({
            bookmaker: sourceBookmaker
        });
    }
};

// Function to update cache metrics
const updateCacheMetrics = (hitRate, operation, result) => {
    cacheHitRate.set(hitRate);
    
    if (operation && result) {
        cacheOperations.inc({
            operation: operation,
            result: result
        });
    }
};

// Function to update browser session metrics
const updateBrowserSessions = (count) => {
    activeBrowserSessions.set(count);
};

// Function to update memory metrics
const updateMemoryMetrics = () => {
    const usage = process.memoryUsage();
    
    memoryUsage.set({ type: 'rss' }, usage.rss);
    memoryUsage.set({ type: 'heap_used' }, usage.heapUsed);
    memoryUsage.set({ type: 'heap_total' }, usage.heapTotal);
    memoryUsage.set({ type: 'external' }, usage.external);
};

// Update memory metrics every 30 seconds
setInterval(updateMemoryMetrics, 30000);

// Health check metrics
const healthCheckStatus = new promClient.Gauge({
    name: 'health_check_status',
    help: 'Health check status (1 = healthy, 0 = unhealthy)',
    labelNames: ['service'],
    registers: [register]
});

const updateHealthMetrics = (service, status) => {
    healthCheckStatus.set({ service: service }, status ? 1 : 0);
};

module.exports = {
    register,
    metricsMiddleware,
    recordConversionMetrics,
    updateCacheMetrics,
    updateBrowserSessions,
    updateMemoryMetrics,
    updateHealthMetrics,
    
    // Individual metrics for direct access
    httpRequestsTotal,
    httpRequestDuration,
    conversionRequestsTotal,
    conversionDuration,
    conversionTimeouts,
    browserAutomationFailures,
    antibotDetections,
    cacheHitRate,
    cacheOperations,
    activeBrowserSessions,
    memoryUsage,
    healthCheckStatus
};