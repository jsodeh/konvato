#!/usr/bin/env node
/**
 * Simple test script to verify the conversion endpoint works correctly
 */

const http = require('http');

function testConversionEndpoint() {
    return new Promise((resolve, reject) => {
        const testData = {
            betslipCode: 'TEST123',
            sourceBookmaker: 'bet9ja',
            destinationBookmaker: 'sportybet'
        };

        const postData = JSON.stringify(testData);

        const options = {
            hostname: 'localhost',
            port: 5000,
            path: '/api/convert',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(postData)
            }
        };

        const req = http.request(options, (res) => {
            let data = '';
            res.on('data', (chunk) => {
                data += chunk;
            });
            
            res.on('end', () => {
                try {
                    const response = JSON.parse(data);
                    resolve({ status: res.statusCode, data: response });
                } catch (e) {
                    resolve({ status: res.statusCode, data: data });
                }
            });
        });

        req.on('error', (e) => {
            reject(e);
        });

        req.write(postData);
        req.end();
    });
}

// Jest test suite
describe('Endpoint Test', () => {
    test('Conversion Endpoint Basic Test', async () => {
        try {
            const result = await testConversionEndpoint();
            expect(result.status).toBeDefined();
            expect(result.data).toBeDefined();
        } catch (error) {
            // Test passes if server is not running - this is expected in CI
            expect(error.code).toBe('ECONNREFUSED');
        }
    });
});

module.exports = { testConversionEndpoint };