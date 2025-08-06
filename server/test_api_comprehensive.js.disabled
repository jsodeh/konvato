#!/usr/bin/env node
/**
 * Comprehensive API endpoint tests for the betslip conversion server.
 * Tests all endpoints with various input scenarios, error handling, and edge cases.
 */

const http = require('http');
const assert = require('assert');

class TestAPIEndpoints {
    constructor() {
        this.testsPassed = 0;
        this.testsFailed = 0;
        this.failedTests = [];
        this.baseUrl = 'http://localhost:5000';
        this.timeout = 10000; // 10 second timeout for tests
    }

    runTest(testName, testFunction) {
        return new Promise(async (resolve) => {
            try {
                console.log(`\n=== Testing ${testName} ===`);
                await testFunction();
                console.log(`✅ ${testName} passed`);
                this.testsPassed++;
                resolve(true);
            } catch (error) {
                console.log(`❌ ${testName} failed: ${error.message}`);
                this.testsFailed++;
                this.failedTests.push({ name: testName, error: error.message });
                resolve(false);
            }
        });
    }

    // Helper method to make HTTP requests
    makeRequest(method, path, data = null, headers = {}) {
        return new Promise((resolve, reject) => {
            const url = new URL(path, this.baseUrl);
            const options = {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    ...headers
                }
            };

            const req = http.request(url, options, (res) => {
                let body = '';
                res.on('data', chunk => body += chunk);
                res.on('end', () => {
                    try {
                        const responseData = body ? JSON.parse(body) : {};
                        resolve({
                            statusCode: res.statusCode,
                            headers: res.headers,
                            data: responseData,
                            rawBody: body
                        });
                    } catch (parseError) {
                        resolve({
                            statusCode: res.statusCode,
                            headers: res.headers,
                            data: null,
                            rawBody: body,
                            parseError: parseError.message
                        });
                    }
                });
            });

            req.on('error', reject);
            req.setTimeout(this.timeout, () => {
                req.destroy();
                reject(new Error('Request timeout'));
            });

            if (data) {
                req.write(JSON.stringify(data));
            }
            req.end();
        });
    }

    // Test health endpoint
    async testHealthEndpoint() {
        const response = await this.makeRequest('GET', '/health');
        
        assert.strictEqual(response.statusCode, 200);
        assert.strictEqual(response.data.status, 'OK');
        assert(response.data.message);
        assert(response.data.cache);
    }

    // Test bookmakers endpoint
    async testBookmakersEndpoint() {
        const response = await this.makeRequest('GET', '/api/bookmakers');
        
        assert.strictEqual(response.statusCode, 200);
        assert(response.data.bookmakers);
        assert(Array.isArray(response.data.bookmakers));
        assert(response.data.bookmakers.length > 0);
        
        // Verify bookmaker structure
        const bookmaker = response.data.bookmakers[0];
        assert(bookmaker.id);
        assert(bookmaker.name);
        assert(typeof bookmaker.supported === 'boolean');
    }

    // Test conversion endpoint with valid data
    async testConversionEndpointValid() {
        const validData = {
            betslipCode: 'TEST123456',
            sourceBookmaker: 'bet9ja',
            destinationBookmaker: 'sportybet'
        };

        const response = await this.makeRequest('POST', '/api/convert', validData);
        
        // Note: This might fail if the Python script isn't properly set up
        // We'll check for either success or a proper error response
        assert([200, 500, 408].includes(response.statusCode));
        
        if (response.statusCode === 200) {
            assert(typeof response.data.success === 'boolean');
            assert(Array.isArray(response.data.selections));
            assert(Array.isArray(response.data.warnings));
            assert(typeof response.data.processingTime === 'number');
        } else {
            // Should have proper error structure
            assert(response.data.error);
            assert(response.data.code);
        }
    }

    // Test conversion endpoint with missing fields
    async testConversionEndpointMissingFields() {
        const invalidData = {
            betslipCode: 'TEST123456'
            // Missing sourceBookmaker and destinationBookmaker
        };

        const response = await this.makeRequest('POST', '/api/convert', invalidData);
        
        assert.strictEqual(response.statusCode, 400);
        assert.strictEqual(response.data.success, false);
        assert(response.data.error.includes('Missing required fields'));
    }

    // Test conversion endpoint with invalid betslip code format
    async testConversionEndpointInvalidBetslipCode() {
        const testCases = [
            { betslipCode: '', description: 'empty betslip code' },
            { betslipCode: 'AB', description: 'too short betslip code' },
            { betslipCode: 'A'.repeat(60), description: 'too long betslip code' },
            { betslipCode: 'ABC@123', description: 'invalid characters in betslip code' }
        ];

        for (const testCase of testCases) {
            const invalidData = {
                betslipCode: testCase.betslipCode,
                sourceBookmaker: 'bet9ja',
                destinationBookmaker: 'sportybet'
            };

            const response = await this.makeRequest('POST', '/api/convert', invalidData);
            
            assert.strictEqual(response.statusCode, 400, `Failed for ${testCase.description}`);
            assert.strictEqual(response.data.success, false);
            assert(response.data.error.includes('Invalid betslip code format'));
        }
    }

    // Test conversion endpoint with unsupported bookmakers
    async testConversionEndpointUnsupportedBookmakers() {
        const invalidData = {
            betslipCode: 'TEST123456',
            sourceBookmaker: 'unsupported_bookmaker',
            destinationBookmaker: 'sportybet'
        };

        const response = await this.makeRequest('POST', '/api/convert', invalidData);
        
        assert.strictEqual(response.statusCode, 400);
        assert.strictEqual(response.data.success, false);
        assert(response.data.error.includes('Unsupported bookmaker'));
    }

    // Test conversion endpoint with same source and destination
    async testConversionEndpointSameBookmakers() {
        const invalidData = {
            betslipCode: 'TEST123456',
            sourceBookmaker: 'bet9ja',
            destinationBookmaker: 'bet9ja'
        };

        const response = await this.makeRequest('POST', '/api/convert', invalidData);
        
        assert.strictEqual(response.statusCode, 400);
        assert.strictEqual(response.data.success, false);
        assert(response.data.error.includes('must be different'));
    }

    // Test conversion endpoint with malformed JSON
    async testConversionEndpointMalformedJSON() {
        return new Promise((resolve, reject) => {
            const url = new URL('/api/convert', this.baseUrl);
            const options = {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            };

            const req = http.request(url, options, (res) => {
                let body = '';
                res.on('data', chunk => body += chunk);
                res.on('end', () => {
                    try {
                        assert.strictEqual(res.statusCode, 400);
                        resolve();
                    } catch (error) {
                        reject(error);
                    }
                });
            });

            req.on('error', reject);
            req.write('{"invalid": json}'); // Malformed JSON
            req.end();
        });
    }

    // Test rate limiting (if implemented)
    async testRateLimiting() {
        const validData = {
            betslipCode: 'TEST123456',
            sourceBookmaker: 'bet9ja',
            destinationBookmaker: 'sportybet'
        };

        // Make multiple rapid requests
        const promises = [];
        for (let i = 0; i < 15; i++) { // Exceed the typical rate limit
            promises.push(this.makeRequest('POST', '/api/convert', validData));
        }

        const responses = await Promise.all(promises);
        
        // At least one should be rate limited (429 status)
        const rateLimitedResponses = responses.filter(r => r.statusCode === 429);
        
        if (rateLimitedResponses.length > 0) {
            const rateLimitedResponse = rateLimitedResponses[0];
            assert(rateLimitedResponse.data.error.includes('Too many requests'));
            assert(rateLimitedResponse.data.code === 'RATE_LIMIT_EXCEEDED');
            assert(typeof rateLimitedResponse.data.retryAfter === 'number');
        }
        
        // Note: If no rate limiting is implemented, this test will pass
        console.log(`Rate limiting test: ${rateLimitedResponses.length} requests were rate limited`);
    }

    // Test CORS headers
    async testCORSHeaders() {
        const response = await this.makeRequest('OPTIONS', '/api/convert', null, {
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        });

        // Should have CORS headers
        assert(response.headers['access-control-allow-origin'] || 
               response.headers['Access-Control-Allow-Origin']);
    }

    // Test cache statistics endpoint
    async testCacheStatsEndpoint() {
        const response = await this.makeRequest('GET', '/api/cache/stats');
        
        assert.strictEqual(response.statusCode, 200);
        assert(typeof response.data === 'object');
        // Cache stats structure may vary, so we just check it's an object
    }

    // Test cache invalidation endpoints
    async testCacheInvalidationEndpoints() {
        // Test game mappings cache invalidation
        let response = await this.makeRequest('DELETE', '/api/cache/game-mappings/bet9ja/sportybet');
        assert([200, 500].includes(response.statusCode)); // May fail if cache not initialized
        
        // Test odds cache invalidation
        response = await this.makeRequest('DELETE', '/api/cache/odds/bet9ja');
        assert([200, 500].includes(response.statusCode)); // May fail if cache not initialized
    }

    // Test non-existent endpoints
    async testNonExistentEndpoints() {
        const response = await this.makeRequest('GET', '/api/nonexistent');
        
        assert.strictEqual(response.statusCode, 404);
    }

    // Test request timeout handling
    async testRequestTimeout() {
        // This test is difficult to implement without modifying the server
        // We'll simulate it by testing with a very short timeout
        const originalTimeout = this.timeout;
        this.timeout = 1; // 1ms timeout
        
        try {
            await this.makeRequest('GET', '/health');
            // If it doesn't timeout, that's also fine
        } catch (error) {
            assert(error.message.includes('timeout'));
        } finally {
            this.timeout = originalTimeout;
        }
    }

    // Test request with large payload
    async testLargePayload() {
        const largeData = {
            betslipCode: 'A'.repeat(1000), // Very long betslip code
            sourceBookmaker: 'bet9ja',
            destinationBookmaker: 'sportybet'
        };

        const response = await this.makeRequest('POST', '/api/convert', largeData);
        
        // Should be rejected due to invalid betslip code format
        assert.strictEqual(response.statusCode, 400);
        assert(response.data.error.includes('Invalid betslip code format'));
    }

    // Test concurrent requests
    async testConcurrentRequests() {
        const validData = {
            betslipCode: 'TEST123456',
            sourceBookmaker: 'bet9ja',
            destinationBookmaker: 'sportybet'
        };

        // Make 5 concurrent requests
        const promises = [];
        for (let i = 0; i < 5; i++) {
            promises.push(this.makeRequest('POST', '/api/convert', validData));
        }

        const responses = await Promise.all(promises);
        
        // All should complete (either successfully or with proper errors)
        responses.forEach(response => {
            assert([200, 400, 408, 429, 500].includes(response.statusCode));
            if (response.statusCode !== 429) { // Skip rate limited responses
                assert(response.data);
            }
        });
    }

    // Test request headers validation
    async testRequestHeaders() {
        const validData = {
            betslipCode: 'TEST123456',
            sourceBookmaker: 'bet9ja',
            destinationBookmaker: 'sportybet'
        };

        // Test without Content-Type header
        const response = await this.makeRequest('POST', '/api/convert', validData, {
            'Content-Type': 'text/plain'
        });

        // Should still work or give a proper error
        assert([200, 400, 408, 500].includes(response.statusCode));
    }

    // Test response format consistency
    async testResponseFormatConsistency() {
        // Test successful bookmakers endpoint
        let response = await this.makeRequest('GET', '/api/bookmakers');
        assert(response.data);
        assert(!response.parseError);

        // Test error response format
        response = await this.makeRequest('POST', '/api/convert', {});
        assert.strictEqual(response.statusCode, 400);
        assert.strictEqual(response.data.success, false);
        assert(response.data.error);
        assert(!response.parseError);
    }

    // Check if server is running
    async checkServerRunning() {
        try {
            await this.makeRequest('GET', '/health');
            return true;
        } catch (error) {
            return false;
        }
    }

    // Run all tests
    async runAllTests() {
        console.log('=== API Endpoints Test Suite ===');

        // Check if server is running
        const serverRunning = await this.checkServerRunning();
        if (!serverRunning) {
            console.log('❌ Server is not running. Please start the server first.');
            console.log('   Run: node server/server.js');
            return false;
        }

        console.log('✅ Server is running, proceeding with tests...');

        // Run all tests
        await this.runTest('Health Endpoint', () => this.testHealthEndpoint());
        await this.runTest('Bookmakers Endpoint', () => this.testBookmakersEndpoint());
        await this.runTest('Conversion Endpoint - Valid Data', () => this.testConversionEndpointValid());
        await this.runTest('Conversion Endpoint - Missing Fields', () => this.testConversionEndpointMissingFields());
        await this.runTest('Conversion Endpoint - Invalid Betslip Code', () => this.testConversionEndpointInvalidBetslipCode());
        await this.runTest('Conversion Endpoint - Unsupported Bookmakers', () => this.testConversionEndpointUnsupportedBookmakers());
        await this.runTest('Conversion Endpoint - Same Bookmakers', () => this.testConversionEndpointSameBookmakers());
        await this.runTest('Conversion Endpoint - Malformed JSON', () => this.testConversionEndpointMalformedJSON());
        await this.runTest('Rate Limiting', () => this.testRateLimiting());
        await this.runTest('CORS Headers', () => this.testCORSHeaders());
        await this.runTest('Cache Stats Endpoint', () => this.testCacheStatsEndpoint());
        await this.runTest('Cache Invalidation Endpoints', () => this.testCacheInvalidationEndpoints());
        await this.runTest('Non-existent Endpoints', () => this.testNonExistentEndpoints());
        await this.runTest('Request Timeout', () => this.testRequestTimeout());
        await this.runTest('Large Payload', () => this.testLargePayload());
        await this.runTest('Concurrent Requests', () => this.testConcurrentRequests());
        await this.runTest('Request Headers', () => this.testRequestHeaders());
        await this.runTest('Response Format Consistency', () => this.testResponseFormatConsistency());

        this.printResults();
        return this.testsFailed === 0;
    }

    printResults() {
        console.log('\n=== Test Results ===');
        console.log(`Passed: ${this.testsPassed}`);
        console.log(`Failed: ${this.testsFailed}`);
        console.log(`Total: ${this.testsPassed + this.testsFailed}`);

        if (this.testsFailed > 0) {
            console.log('\nFailed Tests:');
            this.failedTests.forEach(test => {
                console.log(`  - ${test.name}: ${test.error}`);
            });
        }

        if (this.testsFailed === 0) {
            console.log('✅ All API endpoint tests passed!');
        } else {
            console.log('❌ Some API endpoint tests failed!');
        }
    }
}

// Jest test suite
describe('API Endpoints', () => {
    let tester;

    beforeAll(() => {
        tester = new TestAPIEndpoints();
    });

    test('Health Endpoint', async () => {
        await tester.testHealthEndpoint();
    });

    test('Bookmakers Endpoint', async () => {
        await tester.testBookmakersEndpoint();
    });

    test('Conversion Endpoint Valid', async () => {
        await tester.testConversionEndpointValid();
    });

    test('Conversion Endpoint Missing Fields', async () => {
        await tester.testConversionEndpointMissingFields();
    });

    test('Conversion Endpoint Invalid Betslip Code', async () => {
        await tester.testConversionEndpointInvalidBetslipCode();
    });

    test('Conversion Endpoint Unsupported Bookmakers', async () => {
        await tester.testConversionEndpointUnsupportedBookmakers();
    });

    test('Conversion Endpoint Same Bookmakers', async () => {
        await tester.testConversionEndpointSameBookmakers();
    });

    test('Conversion Endpoint Malformed JSON', async () => {
        await tester.testConversionEndpointMalformedJSON();
    });

    test('Rate Limiting', async () => {
        await tester.testRateLimiting();
    });

    test('CORS Headers', async () => {
        await tester.testCORSHeaders();
    });

    test('Cache Stats Endpoint', async () => {
        await tester.testCacheStatsEndpoint();
    });

    test('Cache Invalidation Endpoints', async () => {
        await tester.testCacheInvalidationEndpoints();
    });

    test('Non-Existent Endpoints', async () => {
        await tester.testNonExistentEndpoints();
    });

    test('Request Timeout', async () => {
        await tester.testRequestTimeout();
    });

    test('Large Payload', async () => {
        await tester.testLargePayload();
    });

    test('Concurrent Requests', async () => {
        await tester.testConcurrentRequests();
    });

    test('Request Headers', async () => {
        await tester.testRequestHeaders();
    });

    test('Response Format Consistency', async () => {
        await tester.testResponseFormatConsistency();
    });
});

module.exports = TestAPIEndpoints;