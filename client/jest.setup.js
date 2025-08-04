// Jest setup file
require('@testing-library/jest-dom');

// Mock DOM APIs that might not be available in test environment
global.fetch = jest.fn();
global.navigator = {
  clipboard: {
    writeText: jest.fn()
  }
};

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;