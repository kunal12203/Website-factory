import nextJest from 'next/jest.js'
 
const createJestConfig = nextJest({
  dir: './',
})
 
/** @type {import('jest').Config} */
const config = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  preset: 'ts-jest',
  // --- THIS LINE IS ADDED ---
  // Tell Jest to look for test files in the src/components directory
  testMatch: [
    '<rootDir>/src/components/**/*.test.(ts|tsx)',
    '<rootDir>/app/**/*.test.(ts|tsx)'
  ],
}
 
export default createJestConfig(config)