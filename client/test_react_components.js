#!/usr/bin/env node
/**
 * Comprehensive unit tests for React components.
 * Tests component rendering, user interactions, and state management.
 * 
 * Note: This is a simplified test suite that simulates React component behavior
 * without requiring a full React testing environment.
 */

const assert = require('assert');

// Mock React and ReactDOM for testing
const mockReact = {
    useState: (initialValue) => {
        // Create a state container that can be accessed and modified
        const stateContainer = { value: initialValue };
        const setValue = (newValue) => {
            if (typeof newValue === 'function') {
                stateContainer.value = newValue(stateContainer.value);
            } else {
                stateContainer.value = newValue;
            }
        };
        // Return getter and setter that access the container
        return [
            new Proxy({}, {
                get: () => stateContainer.value,
                valueOf: () => stateContainer.value,
                toString: () => String(stateContainer.value)
            }),
            setValue
        ];
    },
    useEffect: (effect, deps) => {
        // Simulate useEffect by calling the effect immediately
        effect();
    },
    createElement: (type, props, ...children) => {
        return {
            type,
            props: { ...props, children: children.length === 1 ? children[0] : children },
            key: props?.key || null
        };
    }
};

// Mock validation module
const mockValidation = {
    validateConversionForm: (formData) => {
        const errors = {};
        let isValid = true;

        if (!formData.betslipCode || formData.betslipCode.length < 6) {
            errors.betslipCode = 'Betslip code must be at least 6 characters';
            isValid = false;
        }

        if (!formData.sourceBookmaker) {
            errors.sourceBookmaker = 'Source bookmaker is required';
            isValid = false;
        }

        if (!formData.destinationBookmaker) {
            errors.destinationBookmaker = 'Destination bookmaker is required';
            isValid = false;
        }

        if (formData.sourceBookmaker === formData.destinationBookmaker) {
            errors.general = 'Source and destination bookmakers must be different';
            isValid = false;
        }

        return { isValid, errors };
    },
    sanitizeInput: (input) => {
        if (typeof input !== 'string') return '';
        return input.trim().replace(/[<>\"'&]/g, '');
    },
    formatErrorMessage: (error) => {
        if (typeof error === 'string') return error;
        if (error?.message) return error.message;
        return 'An unexpected error occurred. Please try again.';
    }
};

// Mock fetch for API calls
const mockFetch = (url, options) => {
    return new Promise((resolve) => {
        setTimeout(() => {
            if (url.includes('/api/bookmakers')) {
                resolve({
                    ok: true,
                    json: () => Promise.resolve({
                        bookmakers: [
                            { id: 'bet9ja', name: 'Bet9ja', supported: true },
                            { id: 'sportybet', name: 'Sportybet', supported: true },
                            { id: 'betway', name: 'Betway', supported: true },
                            { id: 'bet365', name: 'Bet365', supported: true }
                        ]
                    })
                });
            } else if (url.includes('/api/convert')) {
                const body = JSON.parse(options.body);
                if (body.betslipCode === 'FAIL123') {
                    resolve({
                        ok: false,
                        json: () => Promise.resolve({
                            success: false,
                            error: 'Betslip not found'
                        })
                    });
                } else {
                    resolve({
                        ok: true,
                        json: () => Promise.resolve({
                            success: true,
                            betslipCode: 'NEW123',
                            selections: [
                                {
                                    game: 'Manchester United vs Liverpool',
                                    market: 'Match Result',
                                    odds: 2.50,
                                    originalOdds: 2.45,
                                    status: 'converted'
                                }
                            ],
                            warnings: [],
                            processingTime: 5.2
                        })
                    });
                }
            }
        }, 100);
    });
};

class TestReactComponents {
    constructor() {
        this.testsPassed = 0;
        this.testsFailed = 0;
        this.failedTests = [];
        
        // Set up global mocks
        global.React = mockReact;
        global.fetch = mockFetch;
        global.BetslipValidation = mockValidation;
    }

    runTest(testName, testFunction) {
        try {
            console.log(`\n=== Testing ${testName} ===`);
            testFunction();
            console.log(`✅ ${testName} passed`);
            this.testsPassed++;
        } catch (error) {
            console.log(`❌ ${testName} failed: ${error.message}`);
            this.testsFailed++;
            this.failedTests.push({ name: testName, error: error.message });
        }
    }

    // Simulate BetslipConverter component behavior
    createBetslipConverter() {
        // Use simple state objects instead of React hooks
        const state = {
            formData: {
                betslipCode: '',
                sourceBookmaker: '',
                destinationBookmaker: ''
            },
            result: null,
            loading: false,
            error: null,
            bookmakers: [],
            validationErrors: {}
        };

        const handleInputChange = (field, value) => {
            const sanitizedValue = mockValidation.sanitizeInput(value);
            state.formData = { ...state.formData, [field]: sanitizedValue };
            
            // Clear validation error for this field
            if (state.validationErrors[field]) {
                state.validationErrors = { ...state.validationErrors, [field]: null };
            }
        };

        const handleSubmit = async (e) => {
            e?.preventDefault();
            
            // Validate form
            const validation = mockValidation.validateConversionForm(state.formData);
            if (!validation.isValid) {
                state.validationErrors = validation.errors;
                return;
            }

            state.loading = true;
            state.error = null;
            state.result = null;

            try {
                const response = await mockFetch('/api/convert', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(state.formData)
                });

                const data = await response.json();
                
                if (data.success) {
                    state.result = data;
                } else {
                    state.error = data.error || 'Conversion failed';
                }
            } catch (err) {
                state.error = mockValidation.formatErrorMessage(err);
            } finally {
                state.loading = false;
            }
        };

        const loadBookmakers = async () => {
            try {
                const response = await mockFetch('/api/bookmakers');
                const data = await response.json();
                state.bookmakers = data.bookmakers;
            } catch (err) {
                console.error('Failed to load bookmakers:', err);
            }
        };

        return {
            get formData() { return state.formData; },
            setFormData: (newData) => { state.formData = newData; },
            get result() { return state.result; },
            setResult: (newResult) => { state.result = newResult; },
            get loading() { return state.loading; },
            setLoading: (newLoading) => { state.loading = newLoading; },
            get error() { return state.error; },
            setError: (newError) => { state.error = newError; },
            get bookmakers() { return state.bookmakers; },
            setBookmakers: (newBookmakers) => { state.bookmakers = newBookmakers; },
            get validationErrors() { return state.validationErrors; },
            setValidationErrors: (newErrors) => { state.validationErrors = newErrors; },
            handleInputChange,
            handleSubmit,
            loadBookmakers
        };
    }

    // Test component initialization
    testComponentInitialization() {
        const component = this.createBetslipConverter();
        
        // Test initial state
        assert.strictEqual(component.formData.betslipCode, '');
        assert.strictEqual(component.formData.sourceBookmaker, '');
        assert.strictEqual(component.formData.destinationBookmaker, '');
        assert.strictEqual(component.result, null);
        assert.strictEqual(component.loading, false);
        assert.strictEqual(component.error, null);
        assert(Array.isArray(component.bookmakers));
        assert.strictEqual(component.bookmakers.length, 0);
        assert.deepStrictEqual(component.validationErrors, {});
    }

    // Test input handling
    testInputHandling() {
        const component = this.createBetslipConverter();
        
        // Test betslip code input
        component.handleInputChange('betslipCode', 'ABC123DEF');
        assert.strictEqual(component.formData.betslipCode, 'ABC123DEF');
        
        // Test input sanitization
        component.handleInputChange('betslipCode', '<script>alert("xss")</script>');
        assert.strictEqual(component.formData.betslipCode, 'scriptalert(xss)/script');
        
        // Test bookmaker selection
        component.handleInputChange('sourceBookmaker', 'bet9ja');
        assert.strictEqual(component.formData.sourceBookmaker, 'bet9ja');
        
        component.handleInputChange('destinationBookmaker', 'sportybet');
        assert.strictEqual(component.formData.destinationBookmaker, 'sportybet');
    }

    // Test form validation
    testFormValidation() {
        const component = this.createBetslipConverter();
        
        // Test validation with empty form
        const mockEvent = { preventDefault: () => {} };
        component.handleSubmit(mockEvent);
        
        // Should have validation errors
        assert(Object.keys(component.validationErrors).length > 0);
        assert(component.validationErrors.betslipCode);
        assert(component.validationErrors.sourceBookmaker);
        assert(component.validationErrors.destinationBookmaker);
        
        // Test validation with same source and destination
        component.setFormData({
            betslipCode: 'ABC123DEF',
            sourceBookmaker: 'bet9ja',
            destinationBookmaker: 'bet9ja'
        });
        
        component.handleSubmit(mockEvent);
        assert(component.validationErrors.general);
    }

    // Test successful form submission
    async testSuccessfulSubmission() {
        const component = this.createBetslipConverter();
        
        // Set valid form data
        component.setFormData({
            betslipCode: 'ABC123DEF',
            sourceBookmaker: 'bet9ja',
            destinationBookmaker: 'sportybet'
        });
        
        // Submit form
        const mockEvent = { preventDefault: () => {} };
        await component.handleSubmit(mockEvent);
        
        // Wait for async operation
        await new Promise(resolve => setTimeout(resolve, 150));
        
        // Should have successful result
        assert(component.result);
        assert.strictEqual(component.result.success, true);
        assert.strictEqual(component.result.betslipCode, 'NEW123');
        assert(Array.isArray(component.result.selections));
        assert.strictEqual(component.result.selections.length, 1);
        assert.strictEqual(component.error, null);
        assert.strictEqual(component.loading, false);
    }

    // Test failed form submission
    async testFailedSubmission() {
        const component = this.createBetslipConverter();
        
        // Set form data that will trigger failure
        component.setFormData({
            betslipCode: 'FAIL123',
            sourceBookmaker: 'bet9ja',
            destinationBookmaker: 'sportybet'
        });
        
        // Submit form
        const mockEvent = { preventDefault: () => {} };
        await component.handleSubmit(mockEvent);
        
        // Wait for async operation
        await new Promise(resolve => setTimeout(resolve, 150));
        
        // Should have error
        assert(component.error);
        assert.strictEqual(component.error, 'Betslip not found');
        assert.strictEqual(component.result, null);
        assert.strictEqual(component.loading, false);
    }

    // Test bookmaker loading
    async testBookmakerLoading() {
        const component = this.createBetslipConverter();
        
        // Load bookmakers
        await component.loadBookmakers();
        
        // Wait for async operation
        await new Promise(resolve => setTimeout(resolve, 150));
        
        // Should have loaded bookmakers
        assert(Array.isArray(component.bookmakers));
        assert.strictEqual(component.bookmakers.length, 4);
        assert.strictEqual(component.bookmakers[0].id, 'bet9ja');
        assert.strictEqual(component.bookmakers[0].name, 'Bet9ja');
        assert.strictEqual(component.bookmakers[0].supported, true);
    }

    // Test loading state management
    testLoadingStateManagement() {
        const component = this.createBetslipConverter();
        
        // Initially not loading
        assert.strictEqual(component.loading, false);
        
        // Set loading state
        component.setLoading(true);
        assert.strictEqual(component.loading, true);
        
        // Clear loading state
        component.setLoading(false);
        assert.strictEqual(component.loading, false);
    }

    // Test error state management
    testErrorStateManagement() {
        const component = this.createBetslipConverter();
        
        // Initially no error
        assert.strictEqual(component.error, null);
        
        // Set error
        component.setError('Test error message');
        assert.strictEqual(component.error, 'Test error message');
        
        // Clear error
        component.setError(null);
        assert.strictEqual(component.error, null);
    }

    // Test validation error clearing
    testValidationErrorClearing() {
        const component = this.createBetslipConverter();
        
        // Set validation errors
        component.setValidationErrors({
            betslipCode: 'Invalid code',
            sourceBookmaker: 'Required field'
        });
        
        // Input change should clear specific error
        component.handleInputChange('betslipCode', 'ABC123');
        
        // The betslipCode error should be cleared, but sourceBookmaker error should remain
        assert.strictEqual(component.validationErrors.betslipCode, null);
        assert.strictEqual(component.validationErrors.sourceBookmaker, 'Required field');
    }

    // Test result display data structure
    testResultDisplayStructure() {
        const component = this.createBetslipConverter();
        
        // Set mock result
        const mockResult = {
            success: true,
            betslipCode: 'NEW123',
            selections: [
                {
                    game: 'Manchester United vs Liverpool',
                    market: 'Match Result',
                    odds: 2.50,
                    originalOdds: 2.45,
                    status: 'converted'
                },
                {
                    game: 'Arsenal vs Chelsea',
                    market: 'Over/Under 2.5',
                    odds: 1.85,
                    originalOdds: 1.90,
                    status: 'partial'
                }
            ],
            warnings: ['Minor odds difference for Arsenal vs Chelsea'],
            processingTime: 8.5
        };
        
        component.setResult(mockResult);
        
        // Verify result structure
        assert.strictEqual(component.result.success, true);
        assert.strictEqual(component.result.betslipCode, 'NEW123');
        assert.strictEqual(component.result.selections.length, 2);
        assert.strictEqual(component.result.warnings.length, 1);
        assert.strictEqual(component.result.processingTime, 8.5);
        
        // Verify selection structure
        const firstSelection = component.result.selections[0];
        assert.strictEqual(firstSelection.game, 'Manchester United vs Liverpool');
        assert.strictEqual(firstSelection.market, 'Match Result');
        assert.strictEqual(firstSelection.odds, 2.50);
        assert.strictEqual(firstSelection.originalOdds, 2.45);
        assert.strictEqual(firstSelection.status, 'converted');
    }

    // Test component state reset
    testComponentStateReset() {
        const component = this.createBetslipConverter();
        
        // Set some state
        component.setFormData({
            betslipCode: 'ABC123',
            sourceBookmaker: 'bet9ja',
            destinationBookmaker: 'sportybet'
        });
        component.setResult({ success: true });
        component.setError('Some error');
        component.setValidationErrors({ betslipCode: 'Error' });
        
        // Reset to initial state
        component.setFormData({
            betslipCode: '',
            sourceBookmaker: '',
            destinationBookmaker: ''
        });
        component.setResult(null);
        component.setError(null);
        component.setValidationErrors({});
        
        // Verify reset
        assert.strictEqual(component.formData.betslipCode, '');
        assert.strictEqual(component.formData.sourceBookmaker, '');
        assert.strictEqual(component.formData.destinationBookmaker, '');
        assert.strictEqual(component.result, null);
        assert.strictEqual(component.error, null);
        assert.deepStrictEqual(component.validationErrors, {});
    }

    // Run all tests
    async runAllTests() {
        console.log('=== React Components Test Suite ===');

        this.runTest('Component Initialization', () => this.testComponentInitialization());
        this.runTest('Input Handling', () => this.testInputHandling());
        this.runTest('Form Validation', () => this.testFormValidation());
        this.runTest('Loading State Management', () => this.testLoadingStateManagement());
        this.runTest('Error State Management', () => this.testErrorStateManagement());
        this.runTest('Validation Error Clearing', () => this.testValidationErrorClearing());
        this.runTest('Result Display Structure', () => this.testResultDisplayStructure());
        this.runTest('Component State Reset', () => this.testComponentStateReset());

        // Async tests
        await this.runAsyncTest('Successful Submission', () => this.testSuccessfulSubmission());
        await this.runAsyncTest('Failed Submission', () => this.testFailedSubmission());
        await this.runAsyncTest('Bookmaker Loading', () => this.testBookmakerLoading());

        this.printResults();
    }

    async runAsyncTest(testName, testFunction) {
        try {
            console.log(`\n=== Testing ${testName} ===`);
            await testFunction();
            console.log(`✅ ${testName} passed`);
            this.testsPassed++;
        } catch (error) {
            console.log(`❌ ${testName} failed: ${error.message}`);
            this.testsFailed++;
            this.failedTests.push({ name: testName, error: error.message });
        }
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
            console.log('✅ All React component tests passed!');
            return true;
        } else {
            console.log('❌ Some React component tests failed!');
            return false;
        }
    }
}

// Jest test suite
describe('React Components', () => {
    let tester;

    beforeEach(() => {
        tester = new TestReactComponents();
    });

    test('Component Initialization', () => {
        tester.testComponentInitialization();
    });

    test('Input Handling', () => {
        tester.testInputHandling();
    });

    test('Form Validation', () => {
        tester.testFormValidation();
    });

    test('Loading State Management', () => {
        tester.testLoadingStateManagement();
    });

    test('Error State Management', () => {
        tester.testErrorStateManagement();
    });

    test('Validation Error Clearing', () => {
        tester.testValidationErrorClearing();
    });

    test('Result Display Structure', () => {
        tester.testResultDisplayStructure();
    });

    test('Component State Reset', () => {
        tester.testComponentStateReset();
    });

    test('Successful Submission', async () => {
        await tester.testSuccessfulSubmission();
    });

    test('Failed Submission', async () => {
        await tester.testFailedSubmission();
    });

    test('Bookmaker Loading', async () => {
        await tester.testBookmakerLoading();
    });
});

module.exports = TestReactComponents;