const request = require('supertest');
const app = require('./server');
const { complianceManager } = require('./compliance');

describe('Compliance and Privacy Protection', () => {
    
    describe('Data Retention Policies', () => {
        test('should not store actual betslip codes', async () => {
            const testBetslipCode = 'TEST123456';
            
            // Mock a conversion request
            const response = await request(app)
                .post('/api/convert')
                .send({
                    betslipCode: testBetslipCode,
                    sourceBookmaker: 'bet9ja',
                    destinationBookmaker: 'sportybet'
                });
            
            // Check that response doesn't contain the actual betslip code in logs
            expect(response.body.betslipCode).not.toBe(testBetslipCode);
        });
        
        test('should anonymize IP addresses in logs', () => {
            const testIPs = [
                '192.168.1.100',
                '2001:0db8:85a3:0000:0000:8a2e:0370:7334',
                '10.0.0.1'
            ];
            
            testIPs.forEach(ip => {
                const anonymized = complianceManager.anonymizeIP(ip);
                expect(anonymized).not.toBe(ip);
                expect(anonymized).toContain('xxx');
            });
        });
        
        test('should sanitize sensitive data', () => {
            const sensitiveData = {
                betslipCode: 'SENSITIVE123',
                selections: [{
                    game: 'Team A vs Team B',
                    originalText: 'Sensitive betting info'
                }],
                error: {
                    stack: 'Error at /home/user/sensitive/path/file.js:123',
                    message: `Error in ${process.cwd()}/server/sensitive.js`
                }
            };
            
            const sanitized = complianceManager.sanitizeData(sensitiveData, 'conversion');
            
            expect(sanitized.betslipCode).toBe('[REDACTED]');
            expect(sanitized.selections[0].originalText).toBe('[REDACTED]');
        });
    });
    
    describe('Compliance Disclaimers', () => {
        test('should provide compliance disclaimers endpoint', async () => {
            const response = await request(app)
                .get('/api/compliance/disclaimers')
                .expect(200);
            
            expect(response.body.disclaimers).toBeDefined();
            expect(response.body.disclaimers.accuracy).toBeDefined();
            expect(response.body.disclaimers.responsibility).toBeDefined();
            expect(response.body.disclaimers.privacy).toBeDefined();
        });
        
        test('should include disclaimers in conversion responses', async () => {
            // Mock successful conversion
            jest.spyOn(require('child_process'), 'spawn').mockImplementation(() => {
                const mockProcess = {
                    stdout: { on: jest.fn() },
                    stderr: { on: jest.fn() },
                    on: jest.fn((event, callback) => {
                        if (event === 'close') {
                            // Simulate successful conversion
                            callback(0);
                        }
                    }),
                    kill: jest.fn()
                };
                
                // Simulate stdout data
                setTimeout(() => {
                    const mockResult = {
                        success: true,
                        new_betslip_code: 'NEW123',
                        converted_selections: []
                    };
                    mockProcess.stdout.on.mock.calls[0][1](JSON.stringify(mockResult));
                }, 100);
                
                return mockProcess;
            });
            
            const response = await request(app)
                .post('/api/convert')
                .send({
                    betslipCode: 'TEST123',
                    sourceBookmaker: 'bet9ja',
                    destinationBookmaker: 'sportybet'
                });
            
            expect(response.body.disclaimers).toBeDefined();
            expect(response.body.disclaimers.accuracy).toBeDefined();
        });
    });
    
    describe('Compliance Logging', () => {
        test('should log compliance events', async () => {
            const logSpy = jest.spyOn(console, 'log').mockImplementation();
            
            await complianceManager.logComplianceEvent('TEST_EVENT', {
                testData: 'test'
            }, '192.168.1.1', 'req_123');
            
            expect(logSpy).toHaveBeenCalledWith(
                expect.stringContaining('[COMPLIANCE] TEST_EVENT')
            );
            
            logSpy.mockRestore();
        });
        
        test('should validate request compliance', () => {
            const validRequest = {
                body: {
                    betslipCode: 'VALID123',
                    sourceBookmaker: 'bet9ja',
                    destinationBookmaker: 'sportybet'
                }
            };
            
            const invalidRequest = {
                body: {
                    betslipCode: 'INVALID_CODE_WITH_SPECIAL_CHARS!@#',
                    sourceBookmaker: 'bet9ja',
                    destinationBookmaker: 'sportybet'
                }
            };
            
            const validResult = complianceManager.validateRequestCompliance(validRequest);
            const invalidResult = complianceManager.validateRequestCompliance(invalidRequest);
            
            expect(validResult.compliant).toBe(true);
            expect(invalidResult.compliant).toBe(false);
            expect(invalidResult.issues.length).toBeGreaterThan(0);
        });
    });
    
    describe('Privacy Protection', () => {
        test('should not expose sensitive system information', async () => {
            const response = await request(app)
                .get('/health')
                .expect(200);
            
            // Should not expose internal paths or sensitive config
            expect(JSON.stringify(response.body)).not.toContain(process.cwd());
            expect(JSON.stringify(response.body)).not.toContain('password');
            expect(JSON.stringify(response.body)).not.toContain('secret');
        });
        
        test('should handle errors without exposing stack traces', async () => {
            // Force an error by sending invalid data
            const response = await request(app)
                .post('/api/convert')
                .send({
                    betslipCode: '', // Invalid empty code
                    sourceBookmaker: 'bet9ja',
                    destinationBookmaker: 'sportybet'
                })
                .expect(400);
            
            // Should not expose stack traces or internal paths
            expect(JSON.stringify(response.body)).not.toContain('at ');
            expect(JSON.stringify(response.body)).not.toContain(process.cwd());
        });
    });
    
    describe('Rate Limiting Compliance', () => {
        test('should enforce rate limits', async () => {
            const requests = [];
            
            // Send multiple requests rapidly
            for (let i = 0; i < 12; i++) {
                requests.push(
                    request(app)
                        .post('/api/convert')
                        .send({
                            betslipCode: `TEST${i}`,
                            sourceBookmaker: 'bet9ja',
                            destinationBookmaker: 'sportybet'
                        })
                );
            }
            
            const responses = await Promise.all(requests);
            
            // Should have at least one rate limited response
            const rateLimitedResponses = responses.filter(r => r.status === 429);
            expect(rateLimitedResponses.length).toBeGreaterThan(0);
            
            // Rate limited response should have proper error message
            if (rateLimitedResponses.length > 0) {
                expect(rateLimitedResponses[0].body.error).toContain('Too many requests');
                expect(rateLimitedResponses[0].body.code).toBe('RATE_LIMIT_EXCEEDED');
            }
        });
    });
    
    describe('Compliance Reporting', () => {
        test('should generate compliance reports', async () => {
            const startDate = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
            const endDate = new Date().toISOString();
            
            const response = await request(app)
                .get(`/api/compliance/report?startDate=${startDate}&endDate=${endDate}`)
                .expect(200);
            
            expect(response.body.success).toBe(true);
            expect(response.body.report).toBeDefined();
            expect(response.body.report.period).toBeDefined();
            expect(response.body.report.totalEvents).toBeDefined();
            expect(response.body.report.dataRetentionCompliance).toBeDefined();
            expect(response.body.report.privacyMeasures).toBeDefined();
        });
        
        test('should require date parameters for compliance reports', async () => {
            const response = await request(app)
                .get('/api/compliance/report')
                .expect(400);
            
            expect(response.body.success).toBe(false);
            expect(response.body.error).toContain('startDate and endDate');
        });
    });
});

// Cleanup after tests
afterAll(async () => {
    await complianceManager.cleanupExpiredData();
});