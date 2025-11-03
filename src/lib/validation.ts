/**
 * Validation utilities for user inputs
 */

import { WebsiteConfig, ValidationResult } from './types';
import { VALIDATION_RULES, ERROR_MESSAGES } from './constants';

/**
 * Validate prompt text
 */
export function validatePrompt(prompt: string): ValidationResult {
  const errors: string[] = [];

  const trimmed = prompt.trim();

  if (trimmed.length < VALIDATION_RULES.MIN_PROMPT_LENGTH) {
    errors.push(ERROR_MESSAGES.PROMPT_TOO_SHORT);
  }

  if (trimmed.length > VALIDATION_RULES.MAX_PROMPT_LENGTH) {
    errors.push(ERROR_MESSAGES.PROMPT_TOO_LONG);
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

/**
 * Validate hex color
 */
export function validateColor(color: string): ValidationResult {
  const errors: string[] = [];

  if (!VALIDATION_RULES.COLOR_REGEX.test(color)) {
    errors.push(ERROR_MESSAGES.INVALID_COLOR);
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

/**
 * Validate page name
 */
export function validatePageName(name: string): ValidationResult {
  const errors: string[] = [];

  const trimmed = name.trim();

  if (trimmed.length < VALIDATION_RULES.MIN_PAGE_NAME_LENGTH) {
    errors.push(ERROR_MESSAGES.PAGE_NAME_REQUIRED);
  }

  if (trimmed.length > VALIDATION_RULES.MAX_PAGE_NAME_LENGTH) {
    errors.push(ERROR_MESSAGES.PAGE_NAME_TOO_LONG);
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

/**
 * Validate entire website configuration
 */
export function validateWebsiteConfig(config: WebsiteConfig): ValidationResult {
  const errors: string[] = [];

  // Validate prompt
  const promptValidation = validatePrompt(config.prompt);
  errors.push(...promptValidation.errors);

  // Validate colors
  const primaryColorValidation = validateColor(config.primaryColor);
  const secondaryColorValidation = validateColor(config.secondaryColor);
  const accentColorValidation = validateColor(config.accentColor);

  errors.push(...primaryColorValidation.errors);
  errors.push(...secondaryColorValidation.errors);
  errors.push(...accentColorValidation.errors);

  // Validate additional pages
  if (config.additionalPages.length > VALIDATION_RULES.MAX_ADDITIONAL_PAGES) {
    errors.push(ERROR_MESSAGES.TOO_MANY_PAGES);
  }

  for (const pageName of config.additionalPages) {
    const pageValidation = validatePageName(pageName);
    errors.push(...pageValidation.errors);
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

/**
 * Sanitize user input
 */
export function sanitizeInput(input: string): string {
  return input
    .trim()
    .replace(/[<>]/g, '') // Remove potential HTML tags
    .substring(0, VALIDATION_RULES.MAX_PROMPT_LENGTH);
}

/**
 * Sanitize page name
 */
export function sanitizePageName(name: string): string {
  return name
    .trim()
    .replace(/[^a-zA-Z0-9\s-]/g, '') // Only allow alphanumeric, spaces, and hyphens
    .substring(0, VALIDATION_RULES.MAX_PAGE_NAME_LENGTH);
}
