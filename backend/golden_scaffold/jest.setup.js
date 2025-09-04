import '@testing-library/jest-dom';
import { server } from './src/mocks/server.js';
import { toHaveNoViolations } from 'jest-axe';

// Add the jest-axe matcher
expect.extend(toHaveNoViolations);

// Establish API mocking before all tests.
beforeAll(() => server.listen());

// Reset any request handlers that we may add during the tests,
// so they don't affect other tests.
afterEach(() => server.resetHandlers());

// Clean up after the tests are finished.
afterAll(() => server.close());