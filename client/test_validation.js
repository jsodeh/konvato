#!/usr/bin/env node
/**
 * Comprehensive unit tests for validation.js module.
 * Tests form validation, data validation, and input sanitization.
 */

const assert = require('assert');

// Import the validation module
const {
    BOOKMAKER_IDS,
    SELECTION_STATUS,
    API_ENDPOINTS,
    VALIDATION_RULES,
    validateField,
    validateConversionForm,
    sanitizeInput,
    isValidConversionResponse,
    isValidSelection,
    isValidBookmaker,
    isValidBetslipCode,
    formatErrorMessage,
    createInitialFormState,
    createValidationErrors
} = require('./validation.js');

class TestValidationModule {
    constructor() {
        this.testsPassed = 0;
        this.testsFailed = 0;
        this.failedTests = [];
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

    // Test Constants
    testConstants() {
        assert.deepStrictEqual(BOOKMAKER_IDS, {
            BET9JA: 'bet9ja',
            SPORTYBET: 'sportybet',
            BETWAY: 'betway',
            BET365: 'bet365'
        });

        assert.deepStrictEqual(SELECTION_STATUS, {
            CONVERTED: 'converted',
            PARTIAL: 'partial',
            UNAVAILABLE: 'unavailable'
        });

        assert.deepStrictEqual(API_ENDPOINTS, {
            CONVERT: '/api/convert',
            BOOKMAKERS: '/api/bookmakers'
        });

        assert(typeof VALIDATION_RULES === 'object');
        assert(VALIDATION_RULES.betslipCode);
        assert(VALIDATION_RULES.sourceBookmaker);
        assert(VALIDATION_RULES.destinationBookmaker);
    }

    // Test Field Validation
    testValidateField() {
        // Test valid betslip code
        assert.strictEqual(validateField('betslipCode', 'ABC123DEF'), null);
        assert.strictEqual(validateField('betslipCode', 'TEST-CODE-123'), null);
        assert.strictEqual(validateField('betslipCode', '123456789'), null);

        // Test invalid betslip codes
        assert(validateField('betslipCode', '') !== null);
        assert(validateField('betslipCode', 'ABC') !== null); // Too short
        assert(validateField('betslipCode', 'A'.repeat(25)) !== null); // Too long
        assert(validateField('betslipCode', 'ABC@123') !== null); // Invalid characters

        // Test valid bookmaker
        assert.strictEqual(validateField('sourceBookmaker', 'bet9ja'), null);
        assert.strictEqual(validateField('destinationBookmaker', 'sportybet'), null);

        // Test invalid bookmaker
        assert(validateField('sourceBookmaker', 'invalid_bookmaker') !== null);
        assert(validateField('destinationBookmaker', '') !== null);

        // Test non-existent field
        assert.strictEqual(validateField('nonExistentField', 'value'), null);
    }

    // Test Form Validation
    testValidateConversionForm() {
        // Test valid form data
        const validForm = {
            betslipCode: 'ABC123DEF',
            sourceBookmaker: 'bet9ja',
            destinationBookmaker: 'sportybet'
        };

        const validResult = validateConversionForm(validForm);
        assert.strictEqual(validResult.isValid, true);
        assert.deepStrictEqual(validResult.errors, {});

        // Test invalid form data
        const invalidForm = {
            betslipCode: '',
            sourceBookmaker: 'bet9ja',
            destinationBookmaker: 'bet9ja' // Same as source
        };

        const invalidResult = validateConversionForm(invalidForm);
        assert.strictEqual(invalidResult.isValid, false);
        assert(invalidResult.errors.betslipCode);
        assert(invalidResult.errors.general);

        // Test missing fields
        const incompleteForm = {
            betslipCode: 'ABC123'
        };

        const incompleteResult = validateConversionForm(incompleteForm);
        assert.strictEqual(incompleteResult.isValid, false);
        assert(incompleteResult.errors.sourceBookmaker);
        assert(incompleteResult.errors.destinationBookmaker);
    }

    // Test Input Sanitization
    testSanitizeInput() {
        // Test normal input
        assert.strictEqual(sanitizeInput('ABC123'), 'ABC123');
        assert.strictEqual(sanitizeInput('  ABC123  '), 'ABC123');

        // Test dangerous characters
        assert.strictEqual(sanitizeInput('<script>alert("xss")</script>'), 'scriptalert(xss)/script');
        assert.strictEqual(sanitizeInput('test"quote\'test'), 'testquotetest');
        assert.strictEqual(sanitizeInput('test&amp;test'), 'testamp;test');

        // Test non-string input
        assert.strictEqual(sanitizeInput(123), '');
        assert.strictEqual(sanitizeInput(null), '');
        assert.strictEqual(sanitizeInput(undefined), '');

        // Test very long input
        const longInput = 'A'.repeat(2000);
        const sanitized = sanitizeInput(longInput);
        assert(sanitized.length <= 1000);
    }

    // Test Response Validation
    testIsValidConversionResponse() {
        // Test valid response
        const validResponse = {
            success: true,
            selections: [],
            warnings: [],
            processingTime: 5.2
        };
        assert.strictEqual(isValidConversionResponse(validResponse), true);

        // Test invalid responses
        assert.strictEqual(isValidConversionResponse(null), false);
        assert.strictEqual(isValidConversionResponse({}), false);
        assert.strictEqual(isValidConversionResponse({
            success: 'true', // Should be boolean
            selections: [],
            warnings: [],
            processingTime: 5.2
        }), false);

        assert.strictEqual(isValidConversionResponse({
            success: true,
            selections: 'not_array', // Should be array
            warnings: [],
            processingTime: 5.2
        }), false);
    }

    // Test Selection Validation
    testIsValidSelection() {
        // Test valid selection
        const validSelection = {
            game: 'Manchester United vs Liverpool',
            market: 'Match Result',
            odds: 2.50,
            originalOdds: 2.45,
            status: 'converted'
        };
        assert.strictEqual(isValidSelection(validSelection), true);

        // Test invalid selections
        assert.strictEqual(isValidSelection(null), false);
        assert.strictEqual(isValidSelection({}), false);
        assert.strictEqual(isValidSelection({
            game: 'Manchester United vs Liverpool',
            market: 'Match Result',
            odds: '2.50', // Should be number
            originalOdds: 2.45,
            status: 'converted'
        }), false);

        assert.strictEqual(isValidSelection({
            game: 'Manchester United vs Liverpool',
            market: 'Match Result',
            odds: 2.50,
            originalOdds: 2.45,
            status: 'invalid_status' // Invalid status
        }), false);
    }

    // Test Bookmaker Validation
    testIsValidBookmaker() {
        // Test valid bookmaker
        const validBookmaker = {
            id: 'bet9ja',
            name: 'Bet9ja',
            baseUrl: 'https://www.bet9ja.com',
            supported: true
        };
        assert.strictEqual(isValidBookmaker(validBookmaker), true);

        // Test invalid bookmakers
        assert.strictEqual(isValidBookmaker(null), false);
        assert.strictEqual(isValidBookmaker({}), false);
        assert.strictEqual(isValidBookmaker({
            id: 123, // Should be string
            name: 'Bet9ja',
            baseUrl: 'https://www.bet9ja.com',
            supported: true
        }), false);

        assert.strictEqual(isValidBookmaker({
            id: 'bet9ja',
            name: 'Bet9ja',
            baseUrl: 'https://www.bet9ja.com',
            supported: 'true' // Should be boolean
        }), false);
    }

    // Test Betslip Code Validation
    testIsValidBetslipCode() {
        // Test valid codes
        assert.strictEqual(isValidBetslipCode('ABC123DEF'), true);
        assert.strictEqual(isValidBetslipCode('TEST-CODE-123'), true);
        assert.strictEqual(isValidBetslipCode('TEST_CODE_123'), true);
        assert.strictEqual(isValidBetslipCode('123456'), true);

        // Test invalid codes
        assert.strictEqual(isValidBetslipCode(''), false);
        assert.strictEqual(isValidBetslipCode('ABC'), false); // Too short
        assert.strictEqual(isValidBetslipCode('A'.repeat(25)), false); // Too long
        assert.strictEqual(isValidBetslipCode('ABC@123'), false); // Invalid characters
        assert.strictEqual(isValidBetslipCode(123), false); // Not string
        assert.strictEqual(isValidBetslipCode(null), false);
    }

    // Test Error Message Formatting
    testFormatErrorMessage() {
        // Test string error
        assert.strictEqual(formatErrorMessage('Simple error'), 'Simple error');

        // Test error object with message
        const errorWithMessage = { message: 'Error message' };
        assert.strictEqual(formatErrorMessage(errorWithMessage), 'Error message');

        // Test axios-style error
        const axiosError = {
            response: {
                data: {
                    message: 'API error message'
                }
            }
        };
        assert.strictEqual(formatErrorMessage(axiosError), 'API error message');

        // Test unknown error
        assert.strictEqual(formatErrorMessage({}), 'An unexpected error occurred. Please try again.');
        assert.strictEqual(formatErrorMessage(null), 'An unexpected error occurred. Please try again.');
    }

    // Test State Creation Functions
    testCreateInitialFormState() {
        const initialState = createInitialFormState();
        
        assert.strictEqual(typeof initialState, 'object');
        assert.strictEqual(initialState.betslipCode, '');
        assert.strictEqual(initialState.sourceBookmaker, '');
        assert.strictEqual(initialState.destinationBookmaker, '');
        assert.strictEqual(initialState.result, null);
        assert.strictEqual(initialState.loading, false);
        assert.strictEqual(initialState.error, null);
        assert(Array.isArray(initialState.bookmakers));
        assert.strictEqual(initialState.bookmarkersLoading, false);
    }

    testCreateValidationErrors() {
        const errors = createValidationErrors();
        
        assert.strictEqual(typeof errors, 'object');
        assert.strictEqual(errors.betslipCode, null);
        assert.strictEqual(errors.sourceBookmaker, null);
        assert.strictEqual(errors.destinationBookmaker, null);
        assert.strictEqual(errors.general, null);
    }

    // Test Edge Cases
    testEdgeCases() {
        // Test validateField with undefined values
        assert(validateField('betslipCode', undefined) !== null);
        assert(validateField('betslipCode', null) !== null);

        // Test validateConversionForm with missing properties
        const emptyForm = {};
        const result = validateConversionForm(emptyForm);
        assert.strictEqual(result.isValid, false);
        assert(Object.keys(result.errors).length > 0);

        // Test sanitizeInput with edge cases
        assert.strictEqual(sanitizeInput(''), '');
        assert.strictEqual(sanitizeInput('   '), '');

        // Test validation with whitespace-only values
        assert(validateField('betslipCode', '   ') !== null);
        assert(validateField('sourceBookmaker', '   ') !== null);
    }

    // Test Cross-Field Validation
    testCrossFieldValidation() {
        // Test same source and destination bookmaker
        const sameBookmakerForm = {
            betslipCode: 'ABC123DEF',
            sourceBookmaker: 'bet9ja',
            destinationBookmaker: 'bet9ja'
        };

        const result = validateConversionForm(sameBookmakerForm);
        assert.strictEqual(result.isValid, false);
        assert(result.errors.general);
        assert(result.errors.general.includes('different'));
    }

    // Test Validation Rules Structure
    testValidationRulesStructure() {
        // Test betslipCode rule
        const betslipRule = VALIDATION_RULES.betslipCode;
        assert.strictEqual(betslipRule.required, true);
        assert.strictEqual(betslipRule.minLength, 6);
        assert.strictEqual(betslipRule.maxLength, 20);
        assert(betslipRule.pattern instanceof RegExp);
        assert(typeof betslipRule.custom === 'function');

        // Test custom validation function
        assert.strictEqual(betslipRule.custom('ABC123'), null);
        assert(betslipRule.custom('') !== null);
        assert(betslipRule.custom('ABC') !== null);
    }

    // Run all tests
    runAllTests() {
        console.log('=== Validation Module Test Suite ===');

        this.runTest('Constants', () => this.testConstants());
        this.runTest('Field Validation', () => this.testValidateField());
        this.runTest('Form Validation', () => this.testValidateConversionForm());
        this.runTest('Input Sanitization', () => this.testSanitizeInput());
        this.runTest('Response Validation', () => this.testIsValidConversionResponse());
        this.runTest('Selection Validation', () => this.testIsValidSelection());
        this.runTest('Bookmaker Validation', () => this.testIsValidBookmaker());
        this.runTest('Betslip Code Validation', () => this.testIsValidBetslipCode());
        this.runTest('Error Message Formatting', () => this.testFormatErrorMessage());
        this.runTest('Initial Form State', () => this.testCreateInitialFormState());
        this.runTest('Validation Errors', () => this.testCreateValidationErrors());
        this.runTest('Edge Cases', () => this.testEdgeCases());
        this.runTest('Cross-Field Validation', () => this.testCrossFieldValidation());
        this.runTest('Validation Rules Structure', () => this.testValidationRulesStructure());

        this.printResults();
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
            console.log('✅ All validation tests passed!');
            return true;
        } else {
            console.log('❌ Some validation tests failed!');
            return false;
        }
    }
}

// Jest test suite
describe('Validation Module', () => {
    let tester;

    beforeEach(() => {
        tester = new TestValidationModule();
    });

    test('Constants', () => {
        tester.testConstants();
    });

    test('Field Validation', () => {
        tester.testValidateField();
    });

    test('Form Validation', () => {
        tester.testValidateConversionForm();
    });

    test('Input Sanitization', () => {
        tester.testSanitizeInput();
    });

    test('Response Validation', () => {
        tester.testIsValidConversionResponse();
    });

    test('Selection Validation', () => {
        tester.testIsValidSelection();
    });

    test('Bookmaker Validation', () => {
        tester.testIsValidBookmaker();
    });

    test('Betslip Code Validation', () => {
        tester.testIsValidBetslipCode();
    });

    test('Error Message Formatting', () => {
        tester.testFormatErrorMessage();
    });

    test('Initial Form State', () => {
        tester.testCreateInitialFormState();
    });

    test('Validation Errors', () => {
        tester.testCreateValidationErrors();
    });

    test('Edge Cases', () => {
        tester.testEdgeCases();
    });

    test('Cross-Field Validation', () => {
        tester.testCrossFieldValidation();
    });

    test('Validation Rules Structure', () => {
        tester.testValidationRulesStructure();
    });
});

module.exports = TestValidationModule;